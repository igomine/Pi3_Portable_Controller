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

# rs485 chip enable pin
gpio.setmode(gpio.BCM)
gpio.setup(4, gpio.OUT)
gpio.output(4, gpio.HIGH)
float_list = [0]*12

# while True:
#     print("a")
#     time.sleep(2)
#     pass

rs485tometer = serial.Serial('/dev/serial0', 115200, timeout=1)
# rs485tometer = serial.Serial()
rs485tometer.parity = serial.PARITY_ODD


if rs485tometer.isOpen() is False:
    rs485tometer.open()


cmd1_head = b'UUUU1'
cmd2_address = b'\x01'
meter_float = 0.0
cmd3_position = pack('f', meter_float)
done = 0


def write_position(position):
    cmd_position = pack('f', position*1.0)
    rs485tometer.write(b'UUUU2')
    rs485tometer.write(b'\x01')
    rs485tometer.write(cmd_position)

# write_position(0.0)
# time.sleep(3)
# write_position(3240.0/120*20)
# write_position(3240.0/120*21)

# for i in range(2000):
#     random_position = 3240.0/120*20+random.uniform(-3240.0/600.0, 3240.0/600.0)
#     write_position(random_position)
#     print("%d : %.2f" % (i, random_position))
#     time.sleep(1)
#
# write_position(3240.0)
meter_float = 0.0
last_meter_position = meter_float
cmd3_position1 = pack('f', meter_float)
cmd3_position2 = pack('f', meter_float)
cmd3_position3 = pack('f', meter_float)

for i in range(12):
    # meter_float = random.uniform(0, 3200)
    # cmd3_position1 = pack('f', meter_float)
    float_list[i] = int(random.uniform(0, 3200))
    print('%d :%f' % (i, float_list[i]))

    float_list[0] = 0

while True:
    # for i in range(1000):
    # cmd3_position1 = pack('f', meter_float)
    # cmd3_position2 = pack('f', meter_float)
    # print("%d : %.2f" % (i, meter_float))
    # for i in range(12):
    #     float_list[i] = int(random.uniform(0, 3200))
    # if float_list[0] == 0:
    float_list[0] = 3240
    # else:
    # float_list[0] = 0

    print('0 :%f' % (float_list[0]))
        # print('%d :%f' % (i, float_list[i]))
    # print('8 :%f' % ( float_list[8]))
    # print('9 :%f' % ( float_list[9]))
    last_meter_position = meter_float
    rs485tometer.write(cmd1_head)
    rs485tometer.write(b'\x30')
    # rs485tometer.write(cmd3_position1)
    # rs485tometer.write(cmd3_position2)
    # rs485tometer.write(cmd3_position3)
    for i in range(12):
        cmd3_position1 = pack('f', float_list[i])
        # print('%d :%f' % (i, cmd3_position1))
        rs485tometer.write(cmd3_position1)
        # meter_float = random.uniform(0, 3200)
        # cmd3_position1 = pack('f', meter_float)
        # float_list[i] = random.uniform(0, 3200)
        # print('%d :%f' % (i, float_list[i]))
    # rs485tometer.write(cmd1_head)
    # rs485tometer.write(b'\x06')
    # rs485tometer.write(cmd3_position)

    # meter_float = random.uniform(0, 3200)
    #print("%d : %.2f" % (i, meter_float))

    time.sleep(0.05)

    # time.sleep(1)




