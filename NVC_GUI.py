import sys
import numpy as np
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QComboBox, QToolBar
from PyQt5.QtGui import QClipboard
import pyqtgraph as pg
from scipy.signal import savgol_filter, find_peaks
import finnpy.filters.frequency as ff
import finnpy.basic.downsampling as ds

class NpzViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.span_selectors = []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.label = QLabel("Select a folder:")
        layout.addWidget(self.label)

        self.button = QPushButton("Browse")
        self.button.clicked.connect(self.open_folder)
        layout.addWidget(self.button)

        self.file_dropdown = QComboBox()
        layout.addWidget(self.file_dropdown)
        self.file_dropdown.currentIndexChanged.connect(self.plot_data)

        self.plot_widget1 = pg.PlotWidget()
        self.plot_widget2 = pg.PlotWidget()

        self.plot_widget1.setXLink(self.plot_widget2)

        layout.addWidget(self.plot_widget1)
        layout.addWidget(self.plot_widget2)

        self.toolbar = QToolBar("Tools")
        layout.addWidget(self.toolbar)

        self.toggle_span_button = QPushButton("Toggle Span Selector")
        self.toggle_span_button.setCheckable(True)
        self.toggle_span_button.clicked.connect(self.toggle_span_selector)
        self.toolbar.addWidget(self.toggle_span_button)

        self.copy_span_button = QPushButton("Copy Span Times")
        self.copy_span_button.clicked.connect(self.copy_span_times)
        self.toolbar.addWidget(self.copy_span_button)
        
        self.copy_diff_button = QPushButton("Copy Median Peak-Trough Diff")
        self.copy_diff_button.clicked.connect(self.copy_median_peak_trough_diff)
        self.toolbar.addWidget(self.copy_diff_button)

        self.setLayout(layout)
        self.setWindowTitle("NVC Ananlyis")

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            files = sorted([f for f in os.listdir(folder_path) if f.endswith('.npz')])  # Add sorted() here
            self.file_dropdown.clear()
            self.folder_path = folder_path
            for idx, file in enumerate(files, start=1):
                self.file_dropdown.addItem(f"({idx}) {file}", os.path.join(folder_path, file))

    def plot_data(self):
        file_path = self.file_dropdown.currentData()
        if not file_path:
            return
    
        self.toggle_span_button.setChecked(False)
    
        self.plot_widget1.clear()
        self.plot_widget2.clear()
    
        self.plot_widget1.addLegend()
        self.plot_widget2.addLegend()
    
        time, ch1, ch2, fs = load_npz_data(file_path)
        self.fs_ds = 300
    
        self.ch1_downsampled = ds.run(ch1, fs, self.fs_ds)
        self.ch2_downsampled = ds.run(ch2, fs, self.fs_ds)
    
        self.ch1_filtered = ff.butter(self.ch1_downsampled, 0.3, 149, self.fs_ds, order=2, zero_phase=True)
        self.ch2_filtered = ff.butter(self.ch2_downsampled, 0.3, 149, self.fs_ds, order=2, zero_phase=True)
    
        self.ch1_smoothed = savgol_filter(self.ch1_filtered, 31, 3)
        self.ch2_smoothed = savgol_filter(self.ch2_filtered, 31, 3)
        self.times_downsampled = np.arange(len(self.ch1_smoothed)) / self.fs_ds
    
        self.plot_widget1.setTitle("Electrode 1")
        curve1_raw = self.plot_widget1.plot(time, ch1, pen=pg.mkPen(color=(128, 128, 128), width=1, alpha=0.1), name="Raw")
        curve1_raw.setDownsampling(ds=True, auto=True, method='peak')
        curve1_raw.setClipToView(True)
    
        self.plot_widget1.plot(self.times_downsampled, self.ch1_smoothed, pen='y', name="Smoothed")
    
        peaks1, _ = find_peaks(self.ch1_smoothed, distance=int(0.5 * self.fs_ds))
        troughs1, _ = find_peaks(-self.ch1_smoothed, distance=int(0.5 * self.fs_ds))
        self.plot_widget1.plot(self.times_downsampled[peaks1], self.ch1_smoothed[peaks1], pen=None, symbol='o', symbolBrush='r', name="Peaks")
        self.plot_widget1.plot(self.times_downsampled[troughs1], self.ch1_smoothed[troughs1], pen=None, symbol='o', symbolBrush='b', name="Troughs")
    
        self.plot_widget2.setTitle("Electrode 2")
        curve2_raw = self.plot_widget2.plot(time, ch2, pen=pg.mkPen(color=(128, 128, 128), width=1, alpha=0.1), name="Raw")
        curve2_raw.setDownsampling(ds=True, auto=True, method='peak')
        curve2_raw.setClipToView(True)
    
        self.plot_widget2.plot(self.times_downsampled, self.ch2_smoothed, pen='g', name="Smoothed")
    
        peaks2, _ = find_peaks(self.ch2_smoothed, distance=int(0.5 * self.fs_ds))
        troughs2, _ = find_peaks(-self.ch2_smoothed, distance=int(0.5 * self.fs_ds))
        self.plot_widget2.plot(self.times_downsampled[peaks2], self.ch2_smoothed[peaks2], pen=None, symbol='x', symbolBrush='r', name="Peaks")
        self.plot_widget2.plot(self.times_downsampled[troughs2], self.ch2_smoothed[troughs2], pen=None, symbol='x', symbolBrush='b', name="Troughs")
    
        self.plot_widget1.enableAutoRange()
        self.plot_widget2.enableAutoRange()

    def toggle_span_selector(self, checked):
        if checked:
            self.add_span_selectors()
        else:
            self.remove_span_selectors()

    def add_span_selectors(self):
        center_time = self.get_view_center_time()
        span_region = [center_time - 0.5, center_time + 0.5]

        for plot in [self.plot_widget1, self.plot_widget2]:
            span = pg.LinearRegionItem(span_region)
            plot.addItem(span)
            self.span_selectors.append(span)
            span.sigRegionChanged.connect(self.update_spans_from_any_plot)

    def remove_span_selectors(self):
        for span in self.span_selectors:
            span.sigRegionChanged.disconnect(self.update_spans_from_any_plot)
            span.getViewBox().removeItem(span)
        self.span_selectors.clear()

    def update_spans_from_any_plot(self):
        if not self.span_selectors:
            return
        region = self.sender().getRegion()
        for span in self.span_selectors:
            if span != self.sender():
                span.blockSignals(True)
                span.setRegion(region)
                span.blockSignals(False)

    def get_view_center_time(self):
        vb = self.plot_widget1.getViewBox()
        x_range = vb.viewRange()[0]
        return (x_range[0] + x_range[1]) / 2

    def copy_span_times(self):
        if not self.span_selectors:
            return
        span = self.span_selectors[0]
        region = span.getRegion()
        clipboard = QApplication.clipboard()
        clipboard.setText(f"{region[0]:.2f},{region[1]:.2f}")

    def copy_median_peak_trough_diff(self):
        if not self.span_selectors:
            return
        span = self.span_selectors[0]
        region = span.getRegion()

        ch1_data, ch2_data = self.get_span_data(region)

        median_diff_ch1 = self.calculate_median_peak_trough_diff(ch1_data)
        median_diff_ch2 = self.calculate_median_peak_trough_diff(ch2_data)

        clipboard = QApplication.clipboard()
        clipboard.setText(f"{median_diff_ch1:.2f},{median_diff_ch2:.2f}")

    def get_span_data(self, region):
        start_idx = int(region[0] * self.fs_ds)
        end_idx = int(region[1] * self.fs_ds)
        ch1_data = self.ch1_smoothed[start_idx:end_idx]
        ch2_data = self.ch2_smoothed[start_idx:end_idx]
        return ch1_data, ch2_data

    def calculate_median_peak_trough_diff(self, data):
        peaks, _ = find_peaks(data, distance=int(0.5 * self.fs_ds))
        troughs, _ = find_peaks(-data, distance=int(0.5 * self.fs_ds))
        median_peak = np.median(data[peaks])
        median_trough = np.median(data[troughs])
        return abs(median_peak - median_trough)

def load_npz_data(file_path):
    data = np.load(file_path)
    ch1 = data['raw_data_ch1']
    ch2 = data['raw_data_ch2']
    if 'time' in data:
        time = data['time']
        sampling_freq = 30000
    elif 'sampling_frequency' in data:
        sampling_freq = data['sampling_frequency']
        time = np.arange(len(ch1)) / sampling_freq
    else:
        raise ValueError("No time or sampling frequency information available in the file.")
    return time, ch1, ch2, sampling_freq

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = NpzViewer()
    ex.show()
    sys.exit(app.exec_())
