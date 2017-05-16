"""
rs485 debug log, add by zrd, 2017.5.16

    baudrate setting should be: 115200 odd check(ji jiao yan)
    rs232 ttl - rs485 module should pull up the RSE pin
    when cannot control meter move, send hex 00 80 4A 45 (the float byte of 3240) to test
"""
import serial
import time
from struct import pack, unpack
import RPi.GPIO as gpio

gpio.setmode(gpio.BCM)
gpio.setup(21, gpio.OUT)
gpio.output(21, gpio.HIGH)

# while True:
#     print("a")
#     time.sleep(2)
#     pass

rs485tometer = serial.Serial('/dev/serial0', 115200, timeout=1)
# rs485tometer = serial.Serial()
rs485tometer.parity = serial.PARITY_ODD


if rs485tometer.isOpen() is False:
    rs485tometer.open()


cmd1_head = b'UUUU2'
cmd2_address = b'\x02'
meter_float = 1000.0
cmd3_position = pack('f', meter_float)

while True:
    rs485tometer.write(cmd1_head)
    rs485tometer.write(cmd2_address)
    rs485tometer.write(cmd3_position)
    time.sleep(3)
