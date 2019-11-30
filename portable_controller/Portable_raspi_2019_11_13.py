#!/usr/bin/env python
# -*- coding: utf_8 -*-
"""
    Raspiberry is moubus tcp server, PC is client
    spi communication between Raspiberry and MCU
        2019.7.22 hzm

        zrd 2019.11.25


"""

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
import socket
import os
from periphery import SPI
import queue
import random

commandsend = b'UUUU3'  # Pi to MCU command words
commandrecv = b'UUUU4'  # MCU to Pi command words


class modbusserver(object):
    def __init__(self, server, slaveid):
        self.server = server
        self.slaveid = slaveid
        # self.spi = spidev.SpiDev()
        # self.spi.open(0, 0)
        # self.spi.mode = 0b01
        # self.spi.bits_per_word = 8
        # self.spi.lsbfirst = False
        # self.spi.max_speed_hz = 1000000
        # self.spi.cshigh = False
        self.spi = SPI("/dev/spidev0.0", 1, 1000000)
        self.senddata = [0] * 41
        self.recvdata = [0] * 41
        self.metor_value = [0] * 16
        self.last_metor_value = [0] * 16
        self.coils_value = None
        self.last_coils_value = None
        self.led_tmp = [([0] * 8) for i in range(4)]
        self.led = [0] * 4
        self.ai_value = [0] * 22
        self.last_ai_value = [0] * 22
        self.ai = [0] * 11
        self.key_value = [0] * 4
        self.last_key_value = [0] * 4
        self.key_tmp = [([0] * 8) for i in range(4)]
        self.key = [0] * 32

        self.slave = self.server.get_slave(self.slaveid)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(7, GPIO.IN)

    def sendtomcu(self):
        # add command word "UUUU3"
        self.senddata[0:5] = commandsend
        # get metor from PC
        self.metor_value = list(self.slave.get_values('HOLDING_REGISTERS', 0, 16))
        # print("metor", self.metor_value)
        if (self.metor_value != self.last_metor_value):
            for i in range(0, 16):
                self.senddata[2 * i + 5] = self.metor_value[i] & 0xff
                self.senddata[2 * i + 5 + 1] = self.metor_value[i] >> 8
            self.last_metor_value = copy.copy(self.metor_value)

        # get lamp from PC
        self.coils_value = self.slave.get_values('COILS', 0, 32)
        self.led_tmp[0] = self.coils_value[0:8]
        self.led_tmp[1] = self.coils_value[8:16]
        self.led_tmp[2] = self.coils_value[16:24]
        self.led_tmp[3] = self.coils_value[24:32]
        # change di from list to byte
        if (self.coils_value != self.last_coils_value):
            # chang 8 bit data to one byte
            for i in range(0, 4):
                for j in range(0, 8):
                    if self.led_tmp[i][j] == 0x1:
                        self.led[i] = self.led[i] | 0x80
                    else:
                        self.led[i] = self.led[i] & 0x7f
                    if j != 7:
                        self.led[i] = self.led[i] >> 1

            # package senddata
            self.senddata[37] = self.led[0]
            self.senddata[38] = self.led[1]
            self.senddata[39] = self.led[2]
            self.senddata[40] = self.led[3]
            self.last_coils_value = copy.copy(self.coils_value)

        # print("senddata = ", self.senddata)
        # Master start SPI transport
        # GPIO.output(7, GPIO.LOW)
        # self.recvdata = self.spi.xfer2(self.senddata, 0, 90000, 8)
        # self.recvdata = self.spi.xfer2(self.senddata)
        self.recvdata = self.spi.transfer(self.senddata)
        # GPIO.output(7, GPIO.HIGH)
        # print("recvdata", self.recvdata)

    # analysis receive data
    def recvmcu(self):
        # check command word
        if (self.recvdata[0:5] == list(commandrecv)):
            for i in range(0, 22):
                self.ai_value[i] = self.recvdata[i + 5]
            if (self.ai_value != self.last_ai_value):
                for i in range(0, 11):
                    self.ai[i] = (self.ai_value[2 * i] & 0xff) + (self.ai_value[2 * i + 1] << 8)
                    self.slave.set_values('READ_INPUT_REGISTERS', 0, self.ai)
                    self.last_ai_value = copy.copy(self.ai_value)

            for i in range(0, 4):
                self.key_value[i] = self.recvdata[i + 27]
            # change key to list from byte
            if (self.key_value != self.last_key_value):
                self.last_key_value = copy.copy(self.key_value)
                for i in range(0, 4):
                    for j in range(0, 8):
                        if self.key_value[i] & 0x1 == 0x1:
                            self.key_tmp[i][j] = 0x1
                        else:
                            self.key_tmp[i][j] = 0x0
                        if j != 7:
                            self.key_value[i] = self.key_value[i] >> 1
                self.key[0:8] = self.key_tmp[0]
                self.key[8:16] = self.key_tmp[1]
                self.key[16:24] = self.key_tmp[2]
                self.key[24:32] = self.key_tmp[3]                # package recvdaa
                self.slave.set_values('DISCRETE_INPUTS', 0, self.key)

        # print("ai = ", self.ai)
        # print("key = ", self.key)


def main():
    slaveid = 1
    logger = modbus_tk.utils.create_logger(name="console", record_format="%(message)s")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(13, GPIO.OUT, initial=GPIO.HIGH)

    try:
        # get ip address
        gw = os.popen("ip -4 route show default").read().split()
        print("gw", gw)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # gate is 255.255.255.0
        s.connect((gw[2], 0))
        ipaddr = s.getsockname()[0]
        print("IP:", ipaddr)
        s.close()
        GPIO.output(13, GPIO.LOW)
        time.sleep(1)
        server = modbus_tcp.TcpServer(address=ipaddr, port=502)
        logger.info("esimtech modbus server running...")
        logger.info("enter 'quit' for closing the server")
        server.start()

        slave_1 = server.add_slave(slaveid)
        slave_1.add_block('HOLDING_REGISTERS', cst.HOLDING_REGISTERS, 0, 16)
        slave_1.add_block('DISCRETE_INPUTS', cst.DISCRETE_INPUTS, 0, 32)
        slave_1.add_block('READ_INPUT_REGISTERS', cst.READ_INPUT_REGISTERS, 0, 11)
        slave_1.add_block('COILS', cst.COILS, 0, 32)

        pcontroller = modbusserver(server, slaveid)

        while True:
            if GPIO.input(7) == GPIO.LOW:
                pcontroller.sendtomcu()
                pcontroller.recvmcu()
                time.sleep(1)

    finally:
        server.stop()
        GPIO.cleanup()


if __name__ == "__main__":
    main()







