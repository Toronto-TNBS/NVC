# NVC Analysis GUI
The `NVC_GUI.py` was developed to analyze cardioballistic waveform amplitudes recorded before and after intraoperative microstimulation. It enables inspection and analysis of raw electrophysiological signal files in `.npz` format. The GUI can be used to:
- Visualize microelectrode recordings from two electrodes.
- Apply bandpass filtering and smoothing.
- Identify peaks and troughs.
- Measure changes in CBW amplitude.

![NVC_GUI_DEMO](https://github.com/user-attachments/assets/00ebec51-d363-41d5-96c2-cd86b9a8710c)

## Features
- Load `.npz` files with paired electrode signals.
- Plot raw and smoothed data for both channels.
- Add span selectors synced across plots.
- Copy time windows or median peak-trough amplitudes.
- Designed for comparison of pre/post-stim windows.

## Input Format
Each `.npz` file must contain:
- `raw_data_ch1` and `raw_data_ch2`: electrode channels.
- `time` or `sampling_frequency`: for computing time axis.

## Requirements
The following Python packages are required to run this GUI:
- `numpy`
- `PyQt5`
- `pyqtgraph`
- `scipy`
- `finnpy`
