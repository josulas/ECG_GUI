import sys
from PySide6 import QtCore
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Slot, QTimer, QProcess
from ui_form import Ui_main_window
import numpy as np
import pyqtgraph as pg
from filter import (line_supressor_50_coefficients_fir, 
                    line_supressor_60_coefficients_fir,
                    pass_band_ecg_coefficients_fir, 
                    pam_topkins_coefficients_iir,
                    MAX_NUM_TAPS)
import os
from scipy.signal import convolve


SAMPLING_RATE = 400
SECONDS_SHOWN = 10
AHEAD_SECONDS = 0.5
FRAME_RATE = 30
FILE_NAME = 'saved_ecg_{}.csv'
SAVED_FILES_FOLDER = r'./saved_ecg/'
FILE_HEADERS  = ['Index', 'Signal', 'BPM']
ARDUINO_MAX_VOLTAGE = 5
ARDUINO_MAX_VALUE = 1023
AD8232_VREF = 1.5
FIG_TITLE = 'BPM: {}'
BANDPASS_FILTER_ORDER = len(pass_band_ecg_coefficients_fir)

FILTERS_IDS = {'50Hz': line_supressor_50_coefficients_fir,
               '60Hz': line_supressor_60_coefficients_fir,
               'PASS_BAND': pass_band_ecg_coefficients_fir}

pg.setConfigOption('antialias', True)

BAND_PASS_FILTERED_DATA_NUMBER_OF_BUFFERS = len(pam_topkins_coefficients_iir)

class Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_main_window()
        self.ui.setupUi(self)

        # Setup the GUI
        self.ui.toggle_recording_button.setEnabled(False)
        self.ui.toggle_recording_button.setCheckable(True)
        self.ui.toggle_recording_button.setChecked(False)

        # Patient data
        self.patient_name = None
        self.patient_age = None
        self.patient_sex = None

        # This is for processing data
        self.to_filter_data_buffers = [np.zeros(3) for _ in range(BAND_PASS_FILTERED_DATA_NUMBER_OF_BUFFERS)]
        self.data_buffer = np.zeros(3)
        self.sample_index = 0
        self.band_pass_filtered_data_buffer = np.zeros(2)
        self.squared_derivative_data_buffer = np.zeros(25)
        self.start_p_t_flag = False # Start execution of the PAN-TOMPKINS algorithm
        self.blockout_step = int(0.2 * SAMPLING_RATE) # 200 ms
        self.threshold_proportion = 0.5
        self.last_blockout_index = 0
        self.last_peak_index = None
        self.max_integrated_value = None
        self.last_integrated_value = None
        self.last_peaks_amplitudes = np.zeros(3) # we will store the last 3 peaks amplitudes
        self.last_peaks_mean = None
        self.times_between_peaks = np.zeros(8) # we will store the last 8 times between peaks

        # This buffers will store this values until they are saved in the file
        self.bpm_buffer = None

        # This is the data that is shown in the plot
        self.initial_line_value = 0
        self.serial_buffer_mean = self.initial_line_value
        self.canvas_data = PlotData(SECONDS_SHOWN * SAMPLING_RATE, self.initial_line_value)

        # This is the figure that will show the plot
        self.canvas_fig = pg.PlotItem()
        # check for the color of the background
        self.canvas_fig.setTitle(FIG_TITLE.format('-'), size='18pt', color='w')
        self.canvas_fig.showGrid(False, False)
        self.canvas_fig.hideAxis('bottom')
        self.canvas_fig.hideAxis('left')
        self.canvas_fig.setMenuEnabled(False)
        self.canvas_fig.hideButtons()
        self.canvas_fig.vb.setLimits(xMin = 0, xMax = SECONDS_SHOWN * SAMPLING_RATE)
        self.canvas_fig.vb.disableAutoRange()
        self.canvas_fig.vb.setMouseEnabled(x = False, y = False)
        self.ecg_pen = pg.mkPen(color='r', width=1)
        self.left_line = pg.PlotCurveItem()
        self.right_line = pg.PlotCurveItem()
        self.white_line = pg.PlotCurveItem()
        self.white_line_text = pg.TextItem(text='1s', color='w', anchor=(0.5, 1))
        self.canvas_fig.addItem(self.left_line)
        self.canvas_fig.addItem(self.right_line)
        self.canvas_fig.addItem(self.white_line)
        self.canvas_fig.addItem(self.white_line_text)
        self.ui.ECG_plot.enableMouse(False)
        self.ui.ECG_plot.setCentralItem(self.canvas_fig)

        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_fig_data)
        self.animation_timer.start(1000 / FRAME_RATE)

        # This is the file where the data is saved
        self.save_data_file = None

        # Timer to send data from the serial buffer to the data buffer, it is set to 1/SAMPLING_RATE seconds
        self.send_data_timer = QTimer()
        self.send_data_timer.timeout.connect(self.send_data_serial)

        # This variables serve to the serial communication
        self.serial_connection_process = None
        self.start_serial_connection_process()
        self.serial_buffer = []

    # Process management functions
    def start_serial_connection_process(self):
        if self.serial_connection_process is None:
            self.serial_connection_process = QProcess()
            self.serial_connection_process.readyReadStandardOutput.connect(self.handle_stdout)
            self.serial_connection_process.readyReadStandardError.connect(self.handle_stderr)
            self.serial_connection_process.stateChanged.connect(self.handle_state)
            self.serial_connection_process.finished.connect(self.cleanup)

    def handle_stdout(self):
        data = self.serial_connection_process.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        values = np.float64(stdout.split('\r\n')[:-1])

        self.serial_buffer_mean = np.mean(self.canvas_data.data)
        self.serial_buffer.extend(list(values))

    def handle_stderr(self):
        """
        Error Codes:
        - 1: Arduino not found
        - 2: Serial connection lost
        - 3: Invalid input
        """
        data = self.serial_connection_process.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        if stderr == '0':
            self.ui.connect_button.setText('Connected')
            self.ui.connect_button.setEnabled(False)
            self.ui.toggle_recording_button.setChecked(False)
            self.ui.toggle_recording_button.setEnabled(True)
        elif stderr == '1':
            pass
        elif stderr == '2':
            self.serial_connection_process.kill()
            self.ui.connect_button.setText('Connect to Arduino')    
            self.ui.connect_button.setEnabled(True)
            self.ui.toggle_recording_button.setChecked(False)
            self.ui.toggle_recording_button.setEnabled(False)
        elif stderr == '3':
            pass
        else:
            raise NotImplementedError(f'Error code {stderr} not implemented')

    def handle_state(self, state):
        states = {
            QProcess.ProcessState.NotRunning: 'Not running',
            QProcess.ProcessState.Starting: 'Starting',
            QProcess.ProcessState.Running: 'Running',
        }
        state_name = states[state]
        print(f'Process state changed to: {state_name}')

    def cleanup(self):
        print("Process finished.")
        self.serial_connection_process = None
        self.start_serial_connection_process()
        
    @Slot()
    def on_toggle_recording_button_clicked(self):
        states = ['Start Recording', 'Stop Recording']
        self.ui.toggle_recording_button.setText(states[self.ui.toggle_recording_button.isChecked()])
        if self.ui.toggle_recording_button.isChecked():
            self.save_data_file = open(self.get_file_name(), 'w')
            # Write metadata with comments
            self.save_data_file.write('# Sampling rate: {}\n'.format(SAMPLING_RATE))
            self.save_data_file.write('# Date: {}\n'.format(QtCore.QDateTime.currentDateTime().toString('dd/MM/yyyy hh:mm:ss')))
            self.save_data_file.write('# Patient name: {}\n'.format(self.patient_name if self.patient_name else '-'))
            self.save_data_file.write('# Patient age: {}\n'.format(self.patient_age if self.patient_age else '-'))
            self.save_data_file.write('# Patient sex: {}\n'.format(self.patient_sex if self.patient_sex else '-'))
            self.save_data_file.write(','.join(FILE_HEADERS) + '\n')
            self.serial_connection_process.write(b'1')
            self.serial_connection_process.write(b' ')
            self.serial_connection_process.write(b'0')
            self.serial_connection_process.write(b'\n')
            self.send_data_timer.start(1000 / SAMPLING_RATE)
        else:
            self.canvas_fig.setTitle(FIG_TITLE.format('-'))
            self.send_data_timer.stop()
            self.serial_connection_process.write(b'0')
            self.serial_connection_process.write(b' ')
            self.serial_connection_process.write(b'0')
            self.serial_connection_process.write(b'\n')
            self.sample_index = 0
            if self.save_data_file is not None:
                self.save_data_file.close()
                self.save_data_file = None
            
    @Slot()
    def on_connect_button_clicked(self):
        self.serial_connection_process.start('py', ['communication.py'])
        started = self.serial_connection_process.waitForStarted(500)
        if not started:
            raise Exception('Could not start process.')
        

    # Create an Slot that is called when the checkbox line supressor is clicked
    @Slot(bool)
    def on_noise_line_remover_clicked(self, checked):
        if checked:
            self.canvas_data.filters.append(self.ui.comboBox.currentText())
        else:
            self.canvas_data.filters.remove(self.ui.comboBox.currentText())
        
    
    # Create an Slot that is called when the checkbox adaptative filter is clicked
    @Slot(bool)
    def on_passband_filter_clicked(self, checked):
        if checked:
            self.canvas_data.filters.append('PASS_BAND')
        else:
            self.canvas_data.filters.remove('PASS_BAND')

    # Create an Slot that is called when the combobox line frequency is clicked
    @Slot(str)
    def on_comboBox_currentTextChanged(self, text):
        changing_dict = {'50Hz': '60Hz', '60Hz': '50Hz'}
        if self.ui.noise_line_remover.isChecked():
            self.canvas_data.filters.remove(changing_dict[text])
            self.canvas_data.filters.append(text)

    # Get the patient's name when the line is edited
    @Slot()
    def on_name_line_returnPressed(self):
        patient_name = self.ui.name_line.text()
        # See if the name is valid. If it is, save it. A valid name is a string with at least one character, with only letters and spaces
        if patient_name and patient_name.replace(' ', '').isalpha():
            self.patient_name = ' '.join([name.capitalize() for name in patient_name.split(' ')])
            self.ui.name_line.setText(self.patient_name)
            # Restore the default text color
            self.ui.name_line.setStyleSheet('color: white')
        else:
            self.patient_name = None
            # Set the text in red with the message 'Invalid name'
            self.ui.name_line.setStyleSheet('color: red')
            self.ui.name_line.setText('Invalid name')

    # Get the patient's age when the line is edited
    @Slot()
    def on_age_line_returnPressed(self):
        patient_age = self.ui.age_line.text()
        # See if the age is valid. If it is, save it. A valid age is a number between 0 and 150
        if patient_age and patient_age.isdigit() and 0 <= int(patient_age) <= 120:
            self.patient_age = int(patient_age)
            self.ui.age_line.setText(patient_age)
            # Restore the default text color
            self.ui.age_line.setStyleSheet('color: white')
        else:
            self.patient_age = None
            # Set the text in red with the message 'Invalid age'
            self.ui.age_line.setStyleSheet('color: red')
            self.ui.age_line.setText('Invalid age')
    
    # Get the patient's sex when the combobox is changed
    @Slot(str)
    def on_sex_box_currentTextChanged(self, text):
        if text == 'Select':
            self.patient_sex = None
        else:
            self.patient_sex = text


    def get_cached_freq(self):
        if self.bpm_buffer is None:
            return ''
        else:
            aux = self.bpm_buffer
            self.bpm_buffer = None
            return aux
    
    def send_data_serial(self):
        try:
            # Get a sample and save it
            sample = self.serial_buffer.pop(0)
            self.save_data_sample(sample)
            self.canvas_data.update_data(sample)
            self.sample_index += 1
            self.online_pam_tompkins(sample)
        except IndexError:
            pass

    def set_pam_tompkins_threshold(self, integrated_value):
        if self.max_integrated_value is None:
            self.max_integrated_value = integrated_value
        elif integrated_value > self.max_integrated_value:
            self.max_integrated_value = integrated_value

    def online_pam_tompkins(self, sample):
        # Process the sample
        
        self.data_buffer = np.roll(self.data_buffer, 1)
        self.data_buffer[0] = sample
        
        self.band_pass_filtered_data_buffer = np.roll(self.band_pass_filtered_data_buffer, 1)
        # self.band_pass_filtered_data_buffer[0] = np.dot(self.data_buffer, pass_band_ecg_coefficients_fir)
        for i, (b0, b1, b2, _, a1, a2) in enumerate(pam_topkins_coefficients_iir):
            if i == 0:
                self.to_filter_data_buffers[0] = np.roll(self.to_filter_data_buffers[0], 1)
                self.to_filter_data_buffers[0][0] = b0 * self.data_buffer[0] + b1 * self.data_buffer[1] + b2 * self.data_buffer[2] - a1 * self.to_filter_data_buffers[0][1] - a2 * self.to_filter_data_buffers[0][2]
            else:
                self.to_filter_data_buffers[i] = np.roll(self.to_filter_data_buffers[i], 1)
                self.to_filter_data_buffers[i][0] = b0 * self.to_filter_data_buffers[i-1][0] + b1 * self.to_filter_data_buffers[i-1][1] + b2 * self.to_filter_data_buffers[i-1][2] - a1 * self.to_filter_data_buffers[i][1] - a2 * self.to_filter_data_buffers[i][2]
        self.band_pass_filtered_data_buffer[0] = self.to_filter_data_buffers[-1][0]
        
        self.squared_derivative_data_buffer = np.roll(self.squared_derivative_data_buffer, 1)
        self.squared_derivative_data_buffer[0] = (self.band_pass_filtered_data_buffer[0] - self.band_pass_filtered_data_buffer[1]) ** 2
        
        integrated_value = np.mean(self.squared_derivative_data_buffer)
        
        # Check if we have to start the PAN-TOMPKINS algorithm
        if self.sample_index == 2 * SAMPLING_RATE:
            self.start_p_t_flag = True
            self.last_peaks_mean = self.max_integrated_value
        if not self.start_p_t_flag:
            if self.sample_index > int(0.5 * SAMPLING_RATE): # This line avoids setting the threshold too high, due to the initial noise
                self.set_pam_tompkins_threshold(integrated_value)
        else:
            # Check if we still have to wait for another peak
            if self.last_blockout_index + self.blockout_step < self.sample_index:
                # Asume we didn't find a peak
                new_heart_rate = None
                peak_detected = False
                if integrated_value < self.last_integrated_value:
                    # First use the first threshold
                    if integrated_value > self.threshold_proportion * self.last_peaks_mean:
                        peak_detected = True
                    # If we didn't find a peak and has passed more than 166% of the last time between peaks, use the second threshold
                    if self.times_between_peaks[0] and self.sample_index - self.last_peak_index > 1.66 * self.times_between_peaks[0] * SAMPLING_RATE and integrated_value > self.threshold_proportion/2 * self.last_peaks_mean:
                        peak_detected = True
                # If we have a valid peak, update the values
                if peak_detected:
                    # Set the blockout index
                    self.last_blockout_index = self.sample_index
                    # Update the last peaks mean
                    self.last_peaks_amplitudes = np.roll(self.last_peaks_amplitudes, 1)
                    self.last_peaks_amplitudes[0] = self.last_integrated_value
                    if np.all(self.last_peaks_amplitudes):
                        self.last_peaks_mean = np.average(self.last_peaks_amplitudes)
                    # Update the times between peaks and the heart rate
                    if self.last_peak_index:
                        self.times_between_peaks = np.roll(self.times_between_peaks, 1)
                        self.times_between_peaks[0] = (self.sample_index - self.last_peak_index) / SAMPLING_RATE
                        self.last_peak_index = self.sample_index
                        sum_times = 0
                        num_added_times = 0
                        for time in self.times_between_peaks:
                            if time:
                                sum_times += time
                                num_added_times += 1
                        if num_added_times:
                            new_heart_rate = 60 / (sum_times / num_added_times)
                            self.bpm_buffer = new_heart_rate
                    else:
                        self.last_peak_index = self.sample_index
                # If we could calculate the heart rate, update the title
                if new_heart_rate is not None:
                    self.canvas_fig.setTitle(FIG_TITLE.format(round(new_heart_rate)))
        # Finally update the last integrated value
        self.last_integrated_value = integrated_value

    def save_data_sample(self, sample):
        if self.save_data_file is not None:
            self.save_data_file.write(f'{self.sample_index},{int(sample)},{self.get_cached_freq()}\n')

    def update_fig_data(self):
        if not self.ui.toggle_recording_button.isChecked():
            for _ in range(int(SAMPLING_RATE / FRAME_RATE)):
                    self.canvas_data.update_data(self.serial_buffer_mean)
        x_data = self.canvas_data.indexes
        y_data = self.canvas_data.data
        start_delete = self.canvas_data.last_modified
        end_delete = start_delete + int(AHEAD_SECONDS * SAMPLING_RATE)
        if end_delete > SECONDS_SHOWN * SAMPLING_RATE:
            end_delete %= SECONDS_SHOWN * SAMPLING_RATE
            self.left_line.setData(x_data[end_delete:start_delete], y_data[end_delete:start_delete], pen=self.ecg_pen)
            self.right_line.setData([], [], pen=self.ecg_pen)
        else:
            self.left_line.setData(x_data[:start_delete], y_data[:start_delete], 
                                 pen=self.ecg_pen)
            self.right_line.setData(x_data[end_delete:], y_data[end_delete:], 
                                 pen=self.ecg_pen)
        # The white line is used to indicate how much is one second
        white_line_start = 0.5 * SAMPLING_RATE
        white_line_end = white_line_start + SAMPLING_RATE
        # get the current y range of the plot
        self.canvas_fig.vb.autoRange(items=[self.left_line, self.right_line])
        y_range = self.canvas_fig.vb.viewRange()[1]
        # set the line at the bottom of the plot
        y_line = y_range[0] + 0.05 * (y_range[1] - y_range[0])
        self.white_line.setData([white_line_start, white_line_end], [y_line, y_line], 
                                pen=pg.mkPen(color='w', width=2))
        # Put the text in the middle of the line
        self.white_line_text.setPos((white_line_start + white_line_end) / 2, y_line)
        
        
    def get_file_name(self):
        i = 0
        while os.path.exists(SAVED_FILES_FOLDER + FILE_NAME.format(i)):
            i += 1
        return SAVED_FILES_FOLDER + FILE_NAME.format(i)

    def closeEvent(self, event):
        self.send_data_timer.stop()
        self.animation_timer.stop()
        if self.serial_connection_process is not None:
            self.serial_connection_process.kill()
        if self.save_data_file is not None:
            self.save_data_file.close()
        event.accept()


class PlotData(object):
    def __init__(self, n_points, initial_value=0):
        self.n_points = n_points
        self.indexes = np.array(range(n_points))
        self.data = np.ones(n_points) * initial_value
        self.data_buffer = np.zeros(int(MAX_NUM_TAPS * 2.5))
        self.last_modified = 0
        self.filters = []
    
    def get_next_index(self):
        return (self.last_modified + 1) % self.n_points
    
    def update_data(self, sample):
        self.data_buffer = np.roll(self.data_buffer, 1)
        self.data_buffer[0] = sample
        self.data[self.last_modified] = self.filter_data()
        self.last_modified = self.get_next_index()

    def filter_data(self):
        if self.filters:
            aux_buffer = self.data_buffer.copy()
            for filter in self.filters:
                aux_buffer = convolve(aux_buffer, FILTERS_IDS[filter], mode='valid')
            return aux_buffer[0]
        else:
            return self.data_buffer[0]


if __name__ == "__main__":
    if not os.path.exists(SAVED_FILES_FOLDER):
        os.mkdir(SAVED_FILES_FOLDER)
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    QApplication.setHighDpiScaleFactorRoundingPolicy(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setStyle('Windows')
    widget = Widget()
    widget.show()
    sys.exit(app.exec())
