import smbus
import time
import RTIMU
import os.path
import time
import math
import RPi.GPIO as GPIO
import serial
from struct import pack, unpack
import sys
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_tcp
import RPi.GPIO as GPIO
import threading
import time
import spidev
import itertools
import copy
from RPiMCP23S17.MCP23S17 import MCP23S17
import socket
import os
import queue

# define the total num connect to rasp
total_channel_num = 3
# and also define the AD0 pin of each mpu9255 ,connect to which gpio pin
channel_ad0_via_gpio = [9, 10, 11]


# Initiliazation of I2C bus
bus = smbus.SMBus(1)
address = 0x68       # Sensor I2C address

# Register address from MPU 9255 register map
power_mgmt_1 = 0x6b
accel_config = 0x1c
accel_xout_h = 0x3b
accel_yout_h = 0x3d
accel_zout_h = 0x3f


GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

for i in range(total_channel_num):
    GPIO.setup(channel_ad0_via_gpio[i], GPIO.OUT, initial=GPIO.HIGH)

for i in range(total_channel_num):
    GPIO.setup(channel_ad0_via_gpio[i], GPIO.OUT, initial=GPIO.LOW)
    time.sleep(0.05)
    try:
        chip_id = bus.read_byte_data(address, 0x75)
        bus.write_byte_data(address, power_mgmt_1, 0)
        bus.write_byte_data(address, accel_config, 8)
        print("channel %d init success, chip id 0x%x" % (i, chip_id))
    except Exception as exc:
        print("channel %d init failed, Error: %s" % (i, exc))
    GPIO.setup(channel_ad0_via_gpio[i], GPIO.OUT, initial=GPIO.HIGH)
    time.sleep(0.05)

# # GPIO.setup(channel_ad0_via_gpio[0], GPIO.OUT, initial=GPIO.LOW)
# chip_id = bus.read_byte_data(address, 0x75)
# print(" %x# IMU Init Succeeded" % chip_id)
#
# # i2c_id_0 = bus.read_byte_data(address, 0x37)
#
# # Setting power register to start getting sesnor data
# bus.write_byte_data(address, power_mgmt_1, 0)
#
# # Setting Acceleration register to set the sensitivity
# # 0,8,16 and 24 for 16384,8192,4096 and 2048 sensitivity respectively
# bus.write_byte_data(address, accel_config, 8)


# Function to read byte and word and then convert 2's compliment data to integer
def read_byte(adr):
    return bus.read_byte_data(address, adr)


def read_word(adr):
    high = bus.read_byte_data(address, adr)
    low = bus.read_byte_data(address, adr+1)
    val = (high << 8) + low
    return val


def read_word_2c(adr):
    val = read_word(adr)
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val


GPIO.setup(channel_ad0_via_gpio[2], GPIO.OUT, initial=GPIO.LOW)
while True:
    # print("Raw and Scaled Acelerometer data\n")

    accel_xout = read_word_2c(accel_xout_h)  # We just need to put H byte address
    accel_yout = read_word_2c(accel_yout_h)  # as we are reading the word data
    accel_zout = read_word_2c(accel_zout_h)

    # accel_xout_scaled = accel_xout / 2048.0  # According to the sensitivity you set
    # accel_yout_scaled = accel_yout / 2048.0
    # accel_zout_scaled = accel_zout / 2048.0

    accel_xout_scaled = accel_xout / 8192.0  # According to the sensitivity you set
    accel_yout_scaled = accel_yout / 8192.0
    accel_zout_scaled = accel_zout / 8192.0

    print(accel_xout, accel_yout, accel_zout)
    # print("X>\t Raw: ", accel_xout, "\t Scaled: ", accel_xout_scaled)
    # print("Y>\t Raw: ", accel_yout, "\t Scaled: ", accel_yout_scaled)
    # print("Z>\t Raw: ", accel_zout, "\t Scaled: ", accel_zout_scaled)
    time.sleep(0.1)
