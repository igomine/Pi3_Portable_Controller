#!/usr/bin/env python
# -*- coding: utf_8 -*-
"""
    based on Portable_raspi_2019.11.13
    modify frame to [0x55]*10 + data + CRC + [0xAA]*10
    add CRC in the end of data

        zrd 2021.10.19
"""
"""
    before this version, the frame is:
    Pi to MCU command words: total 41 bytes
        typedef  struct PiToStm32
        {
            __IO uint8_t 	Frame_Head[5];
            __IO uint8_t 	Metor[16];
            __IO uint8_t	DigitalLED[16];
            __IO uint8_t	DO[4];
        }SPI1_PiToStm32_TypeDef;
    ----
    MCU to PI command words: total 41 bytes
    typedef struct Stm32ToPi
    {
        __IO uint8_t 	Frame_Head[5];
        __IO uint16_t 	AI[11];
        __IO uint8_t	DI[4];
        __IO uint8_t	bak[10];
    }SPI1_Stm32ToPi_TypeDef;
==============================================================
    in version 2021.10.15,change frame to 
    Pi to MCU command words: total 50 bytes
        typedef  struct PiToStm32
        {
            __IO uint8_t 	Frame_Head[7];
            __IO uint8_t 	Metor[16];
            __IO uint8_t	DigitalLED[16];
            __IO uint8_t	DO[4];
            __IO uint8_t	Frame_Tail[7];
        }SPI1_PiToStm32_TypeDef;
    ----
    MCU to PI command words: total 50 bytes
    typedef struct Stm32ToPi
    {
        __IO uint8_t 	Frame_Head[7];
        __IO uint16_t 	AI[11];
        __IO uint8_t	DI[4];
        __IO uint8_t	bak[10];
        __IO uint8_t	Frame_Tail[7];
    }SPI1_Stm32ToPi_TypeDef;
"""
# import serial
from struct import pack, unpack
import sys
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_tcp
import RPi.GPIO as GPIO
import threading
import time
# import spidev
import itertools
import copy
import socket
import os
from periphery import SPI
import queue
import random

# PitoStm32FrameHead = b'UUUUUUU'  # Pi to MCU command words
# PitoStm32FrameTail = "\x55\x55\x55\x55\x55\x55\x55"
PitoStm32FrameHead = ["\x55"]*7
PitoStm32FrameTail = ["\xAA"]*7

commandrecv = b'UUUUUUU'  # MCU to Pi command words
# frametail = b'UUUUUUU'


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
        self.spi = SPI("/dev/spidev0.0", 1, 125000)
        # self.senddata = [0] * 41
        # self.recvdata = [0] * 41
        self.senddata = [0] * 36
        self.recvdata = [0] * 50
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

        self.PitoStm32FrameHead = [0x55] * 7
        self.PitoStm32FrameTail = [0xaa] * 7
        self.spiTotalTransCount = 0
        # spiFrameHTCheckOKCount : head and Tail check
        self.spiFrameHTCheckOKCount = 0
        self.t1=0
        self.t2=0


    def sendtomcu(self):
        # add command word "UUUU3"
        # self.senddata[0:5] = PitoStm32FrameHead
        # add frame head and tail at last 2021.10.19

        # get metor from PC
        if self.spiTotalTransCount % 1000 == 0 or self.spiTotalTransCount == 0:
            self.t1 = time.time()
        self.metor_value = list(self.slave.get_values('HOLDING_REGISTERS', 0, 16))
        # print("metor", self.metor_value)
        if (self.metor_value != self.last_metor_value):
            for i in range(0, 16):
                self.senddata[i*2] = self.metor_value[i] & 0xff
                self.senddata[i*2 + 1] = self.metor_value[i] >> 8
                # for test:
                # self.senddata[i*2] = "\x36"
                # self.senddata[i*2 + 1] = "\x36"
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
            self.senddata[32] = self.led[0]
            self.senddata[33] = self.led[1]
            self.senddata[34] = self.led[2]
            self.senddata[35] = self.led[3]
            # for test
            # for i in range(0, 16):
            #     self.senddata[i*2] = 0x36
            #     self.senddata[i*2 + 1] = 0x36
            # self.senddata[32] = 0x89
            # self.senddata[33] = 0x89
            # self.senddata[34] = 0x89
            # self.senddata[35] = 0x89
            # print(self.senddata)
            self.last_coils_value = copy.copy(self.coils_value)

        #add frame head and tail
        self.PitoStm32FrameHead = [0x55] * 7
        self.PitoStm32FrameHead.extend(self.senddata)
        self.PitoStm32FrameHead.extend(self.PitoStm32FrameTail)

        self.recvdata = self.spi.transfer(self.PitoStm32FrameHead)
        self.spiTotalTransCount += 1
        if self.spiTotalTransCount % 1000 == 0:
            self.t2 = time.time()
            successRate = self.spiFrameHTCheckOKCount / self.spiTotalTransCount
            print("TotalTransCount %d, FrameCheckSuccess %d, Sucess rate %0.3f"\
                  % (self.spiTotalTransCount,\
                     self.spiFrameHTCheckOKCount,\
                     successRate))
            print("Current Sample Rate %d Samples/sec" % int((1000/(self.t2-self.t1))))
        self.PitoStm32FrameHead.pop(43)
        # self.recvdata = self.spi.transfer(self.senddata)


    # analysis receive data
    def recvmcu(self):
        # check command word
        if self.recvdata[0:7] == ([0x55]*7) and self.recvdata[43:50] == ([0xaa]*7):
            self.spiFrameHTCheckOKCount += 1
            for i in range(0, 22):
                self.ai_value[i] = self.recvdata[i + 7]
            if (self.ai_value != self.last_ai_value):
                for i in range(0, 11):
                    self.ai[i] = (self.ai_value[2 * i] & 0xff) + (self.ai_value[2 * i + 1] << 8)
                    self.slave.set_values('READ_INPUT_REGISTERS', 0, self.ai)
                    self.last_ai_value = copy.copy(self.ai_value)

            for i in range(0, 4):
                self.key_value[i] = self.recvdata[i + 29]
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
                self.key[24:32] = self.key_tmp[3]  # package recvdaa
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
                time.sleep(0.01)
    except Exception as e:
        print(e.args)
        print(str(e))
        print(repr(e))
    finally:
        server.stop()
        GPIO.cleanup()


if __name__ == "__main__":
    main()







