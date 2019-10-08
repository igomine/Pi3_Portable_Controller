#!/usr/bin/env python
# -*- coding: utf_8 -*-
"""
    based on zlq_test_v1.py, change hardware to a new board use chip MCP23S17
    U1 port 0-15, U2 port 0-15 config as digital output
    U3 port 0-15 config as digital input

        2017.9.11 zrd
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
from RPiMCP23S17.MCP23S17 import MCP23S17
import socket
import os
import queue
import random

q = queue.Queue(10)
rotary_number = 4
rotary_pin_list = [None] * rotary_number
for i in range(rotary_number):
    rotary_pin_list[i] = [None] * 3

rotary_pin_list[0] = [2, 3, 15]
rotary_pin_list[1] = [14, 10, 9]
rotary_pin_list[2] = [11, 8, 7]
rotary_pin_list[3] = [12, 13, 19]
print(rotary_pin_list)

class OutputLoopThread(threading.Thread):
    frequency = 0.01
    next_due = 0

    def __init__(self, server, slaveid, mcp_handle):
        # change for multi threading
        super(OutputLoopThread, self).__init__()
        self.__running = threading.Event()
        self.__running.set()
        self.server = server
        self.slaveid = slaveid
        self.mcp23s17_u2 = mcp_handle

        self.coils_value = None
        self.last_coils_value = None
        self.h_reg_value = [0]*16
        self.last_h_reg_value = [0]*16

        GPIO.setmode(GPIO.BCM)
        # spi output init
        self.spi = spidev.SpiDev(0, 0)
        self.spi.open(0, 0)
        self.spi.mode = 0b11
        self.spi.max_speed_hz = 50
        self.spi.cshigh = False
        # serial to 485 init
        self.rs485tometer = serial.Serial('/dev/serial0', 115200, timeout=1)
        self.rs485tometer.parity = serial.PARITY_ODD
        if self.rs485tometer.isOpen() is False:
            self.rs485tometer.open()
        self.cmd1_head = b'UUUU2'
        self.cmd2_address = b'\x01'
        self.meter_float = 0.0
        self.cmd3_position = pack('f', self.meter_float)

    def grouper(self, iterable, n, fillvalue=0):
        "Collect data into fixed-length chunks or blocks"
        # Taken from itertools recipes
        # https://docs.python.org/2/library/itertools.html#recipes
        # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
        args = [iter(iterable)] * n
        return itertools.zip_longest(fillvalue=fillvalue, *args)

    def stop(self):
        self.__running.clear()

    def run(self):
        while self.__running.is_set():
            if self.next_due < time.time():
                # print("start poll")
                self.poll()
                self.next_due = time.time() + self.frequency
                # time.sleep(0.05)
        return

    def poll(self):
        try:
            slave = self.server.get_slave(self.slaveid)

            # COILS control coils by rsv modbus value
            self.coils_value = list(slave.get_values('COILS', 0, 16))
            if self.coils_value != self.last_coils_value:
                for i in range(16):
                    if self.coils_value[i] == 1:
                        self.mcp23s17_u2.digitalWrite(i, MCP23S17.LEVEL_HIGH)
                    else:
                        self.mcp23s17_u2.digitalWrite(i, MCP23S17.LEVEL_LOW)
                self.last_coils_value = copy.copy(self.coils_value)
                # for some modbus and spi reason, reversed the coils list  __zrd
                # reversed_coils_value = list(reversed(self.coils_value))
                # byte_strings = (''.join(bit_group) for bit_group in self.grouper(map(str, reversed_coils_value), 8))
                # bytes = [int(byte_string, 2) for byte_string in byte_strings]
                # resp = self.spi.xfer(bytes)

            # RS485 control meters by rsv modbus holding reg value
            self.h_reg_value = list(slave.get_values('HOLDING_REGISTERS', 0, 16))
            if self.h_reg_value != self.last_h_reg_value:
                # find out different element and control output
                for i in range(len(self.h_reg_value)):
                    if self.h_reg_value[i] > 3240 or self.h_reg_value[i] < 0:
                        print("Error: HOLDING_REGISTERS[%d]=%f, value error" % (i, self.h_reg_value[i]))
                        slave.set_values('HOLDING_REGISTERS', i, 0)
                        slave.get_values('HOLDING_REGISTERS', i, 1)
                        pass
                    elif self.h_reg_value[i] == self.last_h_reg_value[i]:
                        pass
                    else:
                        self.meter_float = self.h_reg_value[i]
                        self.cmd3_position = pack('f', self.meter_float)
                        # self.cmd2_address = i
                        self.rs485tometer.write(self.cmd1_head)
                        # address = b'i'
                        # self.rs485tometer.write(b'\x06')
                        # address = bytes([i])
                        # address2 = b'\x01'
                        # address = pack("B", i)
                        self.rs485tometer.write(pack("B", i))
                        self.rs485tometer.write(self.cmd3_position)
                self.last_h_reg_value = copy.copy(self.h_reg_value)
        except Exception as exc:
            print("OutputLoopThread Error: %s", exc)


class InputLoopThread(threading.Thread):
    def __init__(self, server, slaveid, rotary_number, rotary_pin):
        # multi threading things
        super(InputLoopThread, self).__init__()
        self.__running = threading.Event()
        self.__running.set()
        self.server = server
        self.slaveid = slaveid
        self.rotary_number = rotary_number
        self.rotary_pin = rotary_pin
        self.pulse_count = [32000] * self.rotary_number
        GPIO.setmode(GPIO.BCM)
        for i in range(self.rotary_number):
            GPIO.setup(self.rotary_pin[i][0], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.rotary_pin[i][1], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.rotary_pin[i][2], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            # GPIO.setup(self.rotary_pin[i][0], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            # GPIO.setup(self.rotary_pin[i][1], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            # GPIO.setup(self.rotary_pin[i][2], GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # di input port init
        self.di_value = [0]*16
        self.di_lastvalue = [0]*16


    def stop(self):
        self.__running.clear()
        GPIO.remove_event_detect(self.clockPin)

    def run(self):
        GPIO.add_event_detect(self.rotary_pin[0][0], GPIO.BOTH, callback=self.PinACallback_chn0, bouncetime=5)
        GPIO.add_event_detect(self.rotary_pin[0][2], GPIO.FALLING, callback=self.PinDCallback_chn0, bouncetime=300)
        GPIO.add_event_detect(self.rotary_pin[1][0], GPIO.BOTH, callback=self.PinACallback_chn1, bouncetime=5)
        GPIO.add_event_detect(self.rotary_pin[1][2], GPIO.FALLING, callback=self.PinDCallback_chn1, bouncetime=300)
        GPIO.add_event_detect(self.rotary_pin[2][0], GPIO.BOTH, callback=self.PinACallback_chn2, bouncetime=5)
        GPIO.add_event_detect(self.rotary_pin[2][2], GPIO.FALLING, callback=self.PinDCallback_chn2, bouncetime=300)
        GPIO.add_event_detect(self.rotary_pin[3][0], GPIO.BOTH, callback=self.PinACallback_chn3, bouncetime=5)
        GPIO.add_event_detect(self.rotary_pin[3][2], GPIO.FALLING, callback=self.PinDCallback_chn3, bouncetime=300)

        while self.__running.is_set():
            # time.sleep(10)
            slave = self.server.get_slave(self.slaveid)
            slave.set_values('HOLDING_REGISTERS', 0, self.pulse_count[0])
            slave.set_values('HOLDING_REGISTERS', 2, self.pulse_count[1])
            slave.set_values('HOLDING_REGISTERS', 4, self.pulse_count[2])
            slave.set_values('HOLDING_REGISTERS', 6, self.pulse_count[3])
            values = slave.get_values('HOLDING_REGISTERS', 0, 8)
        return

    def PinACallback_chn0(self, pin):

        if GPIO.input(self.rotary_pin[0][0]) == 1:
            data = GPIO.input(self.rotary_pin[0][1])
            if data == 1:
                self.pulse_count[0] = self.pulse_count[0] - 1
            else:
                self.pulse_count[0] = self.pulse_count[0] + 1
        else:
            data = GPIO.input(self.rotary_pin[0][1])
            if data == 1:
                self.pulse_count[0] = self.pulse_count[0] + 1
            else:
                self.pulse_count[0] = self.pulse_count[0] - 1
        # print(self.pulse_count)

    def PinDCallback_chn0(self, pin):
        # print("ch0_key_press!")
        slave = self.server.get_slave(self.slaveid)
        slave.set_values('HOLDING_REGISTERS', 1, 1)
        # values = slave.get_values('HOLDING_REGISTERS', 1, 1)

    def PinACallback_chn1(self, pin):

        if GPIO.input(self.rotary_pin[1][0]) == 1:
            data = GPIO.input(self.rotary_pin[1][1])
            if data == 1:
                self.pulse_count[1] = self.pulse_count[1] - 1
            else:
                self.pulse_count[1] = self.pulse_count[1] + 1
        else:
            data = GPIO.input(self.rotary_pin[1][1])
            if data == 1:
                self.pulse_count[1] = self.pulse_count[1] + 1
            else:
                self.pulse_count[1] = self.pulse_count[1] - 1
        # print(self.pulse_count)

    def PinDCallback_chn1(self, pin):
        # print("ch1_key_press!")
        slave = self.server.get_slave(self.slaveid)
        slave.set_values('HOLDING_REGISTERS', 3, 1)
        # values = slave.get_values('HOLDING_REGISTERS', 3, 1)

    def PinACallback_chn2(self, pin):

        if GPIO.input(self.rotary_pin[2][0]) == 1:
            data = GPIO.input(self.rotary_pin[2][1])
            if data == 1:
                self.pulse_count[2] = self.pulse_count[2] - 1
            else:
                self.pulse_count[2] = self.pulse_count[2] + 1
        else:
            data = GPIO.input(self.rotary_pin[2][1])
            if data == 1:
                self.pulse_count[2] = self.pulse_count[2] + 1
            else:
                self.pulse_count[2] = self.pulse_count[2] - 1
                # print(self.pulse_count)

    def PinDCallback_chn2(self, pin):
        # print("ch1_key_press!")
        slave = self.server.get_slave(self.slaveid)
        slave.set_values('HOLDING_REGISTERS', 5, 1)
        # values = slave.get_values('HOLDING_REGISTERS', 3, 1)

    def PinACallback_chn3(self, pin):

        if GPIO.input(self.rotary_pin[3][0]) == 1:
            data = GPIO.input(self.rotary_pin[3][1])
            if data == 1:
                self.pulse_count[3] = self.pulse_count[3] - 1
            else:
                self.pulse_count[3] = self.pulse_count[3] + 1
        else:
            data = GPIO.input(self.rotary_pin[3][1])
            if data == 1:
                self.pulse_count[3] = self.pulse_count[3] + 1
            else:
                self.pulse_count[3] = self.pulse_count[3] - 1
                # print(self.pulse_count)

    def PinDCallback_chn3(self, pin):
        # print("ch1_key_press!")
        slave = self.server.get_slave(self.slaveid)
        slave.set_values('HOLDING_REGISTERS', 7, 1)
        # values = slave.get_values('HOLDING_REGISTERS', 3, 1)
    # def poll(self):
    #     try:
    #         slave = self.server.get_slave(self.slaveid)
    #         # read DI input
    #         for i in range(16):
    #             if self.mcp23s17_u1.digitalRead(i) == MCP23S17.LEVEL_HIGH:
    #                 self.di_value[i] = 1
    #             else:
    #                 self.di_value[i] = 0
    #         if self.di_value != self.di_lastvalue:
    #             # change to list copy
    #             # self.di_lastvalue = self.di_value
    #             self.di_lastvalue = copy.copy(self.di_value)
    #             slave.set_values('DISCRETE_INPUTS', 0, self.di_value)
    #             values = slave.get_values('DISCRETE_INPUTS', 0, len(self.di_value))
    #         # read angvalue
    #         # print(self.read_angvalue())
    #         for i in range(len(self.tle5012_pord_data_lst)):
    #             slave.set_values('READ_INPUT_REGISTERS', i, self.read_angvalue()[i])
    #         values = slave.get_values('READ_INPUT_REGISTERS', 0, 12)
    #
    #     except Exception as exc:
    #         print("InputLoopThread Error: %s", exc)

#
# class StatusHoldingThread(threading.Thread):
#
#     def __init__(self, ip, q, mcp_handle):
#         # change for multi threading
#         super(StatusHoldingThread, self).__init__()
#         self.__running = threading.Event()
#         self.__running.set()
#         self.mcp23s17_u3 = mcp_handle
#         self.ipaddr = ip
#         self.frequency = 9
#         self.next_due = 0
#         self.queue = q
#
#     def stop(self):
#         self.__running.clear()
#
#     def run(self):
#         while self.__running.is_set():
#
#             self.mcp23s17_u3.digitalWrite(13, MCP23S17.LEVEL_LOW)
#             time.sleep(0.05)
#             self.mcp23s17_u3.digitalWrite(13, MCP23S17.LEVEL_HIGH)
#             time.sleep(3)
#
#             # check network interface status
#             if self.next_due < time.time():
#                 self.next_due = time.time() + self.frequency
#                 # gw = os.popen("ip -4 route show default").read().split()
#                 # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#                 # s.connect((gw[2], 0))
#                 # ipaddr_newest = s.getsockname()[0]
#                 # # print("IP:", ipaddr_newest)
#                 # s.close()
#                 ipaddr_newest = os.popen(
#                     "ifconfig | grep 'inet addr:' | grep -v '127.0.0.1' | cut -d: -f2 | awk '{print $1}' | head -1").read()
#                 if ipaddr_newest != self.ipaddr:
#                     print("network interface changed")
#                     # restart_program()
#                     self.queue.put(1)
#                     # return
#                 else:
#                     print(".")
#         return


# def restart_program(thread1, thread2, thread3, server):
#     thread1.stop()
#     thread2.stop()
#     thread_3.stop()
#     server.stop()
#     GPIO.cleanup()
#     python = sys.executable
#     os.execl(python, python, * sys.argv)


def main():
    """main"""
    slaveid = 1
    logger = modbus_tk.utils.create_logger(name="console", record_format="%(message)s")

    try:
        # get current ipaddr
        # gw = os.popen("ip -4 route show default").read().split()
        # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # # s.settimeout(CHECK_TIMEOUT)
        # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # # S.bind(('', UDP_PORT))
        # s.connect((gw[2], 0))
        # ipaddr = s.getsockname()[0]
        # print("IP:", ipaddr)
        # s.close()
        # time.sleep(1)
        # ipaddr = "192.168.1.112"
        ipaddr = os.popen(
            "ifconfig | grep 'inet addr:' | grep -v '127.0.0.1' | cut -d: -f2 | awk '{print $1}' | head -1").read()
        print("IP:", ipaddr)

        # Create the server
        # server = modbus_tcp.TcpServer(address='192.168.1.111')
        server = modbus_tcp.TcpServer(address=ipaddr)
        logger.info("esimtech modbus server running...")
        logger.info("enter 'quit' for closing the server")

        server.start()

        slave_1 = server.add_slave(slaveid)
        slave_1.add_block('HOLDING_REGISTERS', cst.HOLDING_REGISTERS, 0, 16)
        slave_1.add_block('DISCRETE_INPUTS', cst.DISCRETE_INPUTS, 0, 16)
        slave_1.add_block('READ_INPUT_REGISTERS', cst.READ_INPUT_REGISTERS, 0, 16)
        slave_1.add_block('COILS', cst.COILS, 0, 16)
        # 初始化HOLDING_REGISTERS值
        # 命令行读取COILS的值 get_values 1 2 0 5
        init_value = 0x0
        length = 16
        init_value_list = [init_value]*length
        slave = server.get_slave(1)
        slave.set_values('HOLDING_REGISTERS', 0, init_value_list)

        thread_1 = InputLoopThread(server, slaveid, rotary_number, rotary_pin_list)
        thread_1.start()
        # thread_2 = OutputLoopThread(server, slaveid, mcp_u2)
        # thread_2.start()
        # thread_3 = StatusHoldingThread(ipaddr, q, mcp_u3)
        # thread_3.start()

        # block here until get message
        q.get(True)
        print("restart program")
        # restart_program()
        thread_1.stop()
        # thread_2.stop()
        # thread_3.stop()
        server.stop()
        GPIO.cleanup()
        time.sleep(1)
        python = sys.executable
        os.execl(python, python, *sys.argv)

    finally:
        thread_1.stop()
        # thread_2.stop()
        # thread_3.stop()
        server.stop()
        GPIO.cleanup()


if __name__ == "__main__":
    main()
