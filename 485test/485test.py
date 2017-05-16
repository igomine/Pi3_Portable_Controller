import serial
import time
from struct import pack, unpack
import RPi.GPIO as gpio

gpio.setmode(gpio.BCM)
gpio.setup(21, gpio.OUT)
gpio.output(21, gpio.HIGH)

while True:
    print("a")
    time.sleep(2)
    pass

rs485tometer = serial.Serial('/dev/serial0', 9600, timeout=1)


if rs485tometer.isOpen() is False:
    rs485tometer.open()


cmd1_head = b'UUUU2'
cmd2_address = b'\x03'
meter_float = 3240.0
cmd3_position = pack('f', meter_float)

while True:
    rs485tometer.write(cmd1_head)
    rs485tometer.write(cmd2_address)
    rs485tometer.write(cmd3_position)
    time.sleep(3)
