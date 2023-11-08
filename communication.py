import serial
from serial.tools import list_ports
import sys
import threading

ARDUINO_BAUD_RATE = 115200
BUFFER_SIZE = 200

class serialArduino(object):
    def __init__(self):
        try:
            self.serial = serial.Serial(port=self.get_port(), 
                                baudrate=ARDUINO_BAUD_RATE, 
                                bytesize=serial.EIGHTBITS, 
                                parity=serial.PARITY_NONE, 
                                stopbits=serial.STOPBITS_ONE, 
                                timeout=0.5)
        except serial.serialutil.SerialException:
            self.serial = None
    
    def close(self):
        if self.serial is not None:
            self.serial.close()
            self.serial = None
    
    def read(self, n_bytes):
        try:
            return self.serial.read(n_bytes)
        except serial.serialutil.SerialException:
            return None
    
    def write(self, byte):
        try:
            return self.serial.write(byte)
        except serial.serialutil.SerialException:
            return None
    
    def get_port(self):
        ports = list(list_ports.comports())
        for port in ports:
            if 'Arduino' in port.description:
                return port.device
        raise serial.serialutil.SerialException('Arduino not found')


def get_data_serial(serial_connection: serialArduino) -> bool:
        serial_connection.write(b's')
        serial_data = serial_connection.read(BUFFER_SIZE * 2 + 2)
        if serial_data is None:
            return False
        for i in range(0, len(serial_data) - 1, 2):
            high = ord(serial_data[i:i+1])
            low = ord(serial_data[i+1:i+2])
            val = high * 256 + low
            sys.stdout.write(f'{val}\n')
        sys.stdout.flush()
        return True


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
    arduino = serialArduino()
    stop = False
    enable = False
    if arduino.serial is None:
        sys.stderr.write('1')
        sys.stderr.flush()
        stop = True
    else:
        sys.stderr.write('0')
        sys.stderr.flush()
        read_thread = threading.Thread(target=manage_input)
        read_thread.start()
    while not stop:
        if enable:
            if not get_data_serial(arduino):
                sys.stderr.write('2')
                sys.stderr.flush()
                break
        if not read_thread.is_alive():
            if stop:
                break
            else:
                read_thread = threading.Thread(target=manage_input)
                read_thread.start()
        