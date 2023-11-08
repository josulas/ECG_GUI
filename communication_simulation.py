import sys
import numpy as np
from scipy.datasets import electrocardiogram
from threading import Thread, Timer
from scipy.signal import resample

ARDUINO_BAUD_RATE = 115200
BUFFER_SIZE = 200
SAMPLING_RATE = 400

def simulate_get_data_serial() -> None:
        global signal
        global index
        global stop
        try:
            serial_data = signal[index:index + BUFFER_SIZE]
        except IndexError:
            sys.stderr.write('2')
            sys.stderr.flush()
            stop = True
        for value in serial_data:
            sys.stdout.write(f'{value}\n')
        sys.stdout.flush()
        index += BUFFER_SIZE


def manage_input():
    global enable
    global stop
    try:
        control = sys.stdin.readline().split()
        enable = bool(int(control[0]))
        stop = bool(int(control[1]))
    except ValueError:
        sys.stderr.write('3')
        sys.stderr.flush()
    except KeyboardInterrupt:
        stop = True
    except IndexError:
        sys.stderr.write('3')
        sys.stderr.flush()


if __name__ == '__main__':
    stop = False
    enable = False
    signal = electrocardiogram()
    signal = np.int16(resample(signal, int(len(signal) * SAMPLING_RATE / 360)) * 1000 + 500)
    index = 0
    sys.stderr.write('0')
    sys.stderr.flush()
    read_thread = Thread(target=manage_input)
    read_thread.start()
    send_timer = Timer(BUFFER_SIZE/SAMPLING_RATE, simulate_get_data_serial)
    while not stop:
        if enable:
            if not send_timer.is_alive():
                send_timer.start()
            if send_timer.finished:
                send_timer.join()
                send_timer = Timer(BUFFER_SIZE/SAMPLING_RATE, simulate_get_data_serial)
        if not read_thread.is_alive():
            if stop:
                break
            else:
                read_thread = Thread(target=manage_input)
                read_thread.start()
        if stop:
            if read_thread.is_alive():
                del read_thread
        