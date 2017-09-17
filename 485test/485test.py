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
import random


gpio.setmode(gpio.BCM)
gpio.setup(4, gpio.OUT)
gpio.output(4, gpio.HIGH)

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
cmd2_address = b'\x01'
meter_float = 0.0
cmd3_position = pack('f', meter_float)
done = 0
while True:
    while done is 0:

        for i in range(1000):
            cmd3_position = pack('f', meter_float)

            rs485tometer.write(cmd1_head)
            rs485tometer.write(b'\x01')
            rs485tometer.write(cmd3_position)

            rs485tometer.write(cmd1_head)
            rs485tometer.write(b'\x06')
            rs485tometer.write(cmd3_position)

            meter_float = random.uniform(0, 3200)
            print("%d : %.2f" % (i, meter_float))

            if done is 1:
                break

            time.sleep(1)
    while done is 1:
        print("back to zero")
        meter_float = 0.0
        cmd3_position = pack('f', meter_float)

        rs485tometer.write(cmd1_head)
        rs485tometer.write(b'\x01')
        rs485tometer.write(cmd3_position)

        rs485tometer.write(cmd1_head)
        rs485tometer.write(b'\x02')
        rs485tometer.write(cmd3_position)

        time.sleep(60)
