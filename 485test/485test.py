import serial
import time
from struct import pack, unpack

# rs485tometer = serial.Serial(port='/dev/serial0', baudrate=9600, bytesize=8, stopbits=1, timeout=1)
# rs485tometer.open()

rs485tometer = serial.Serial('/dev/serial0', 9600, timeout=1)
# rs485tometer.baudrate = 9600
# rs485tometer.port = '/dev/serial0'

if rs485tometer.isOpen() is False:
    rs485tometer.open()


cmd1_head = b'UUUU2'
cmd2_address = b'\x01'
meter_float = 17.23
cmd3_position = pack('f', meter_float)

while True:
    rs485tometer.write(cmd1_head)
    rs485tometer.write(cmd2_address)
    rs485tometer.write(cmd3_position)
    time.sleep(1)
