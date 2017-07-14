#!/usr/bin/env python
# -*- coding: utf_8 -*-
"""
    success to build up a modbus server by modbus tk
    poll the input and control output(spi), work with modbus server in multi-threading
    test by modbus poll in pc through wifi
        2017.7.14 zrd
"""

import sys
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_tcp
import RPi.GPIO as GPIO
from threading import Thread
import time
import spidev
import itertools


class OutputLoopThread(Thread):
    frequency = 0.01
    next_due = 0

    def __init__(self, server, slaveid):
        # change for multi threading
        super(OutputLoopThread, self).__init__()
        self.server = server
        self.slaveid = slaveid
        self.coils_value = None
        self.last_coils_value = None
        GPIO.setmode(GPIO.BCM)
        # spi output init
        self.spi = spidev.SpiDev(0, 0)
        self.spi.open(0, 0)
        self.spi.mode = 0b11
        self.spi.max_speed_hz = 50
        self.spi.cshigh = False
        # self.spi_snd = [0x0, 0x0]
        # GPIO.setup(tle5012_port_data, GPIO.OUT, initial=GPIO.HIGH)
        # GPIO.setup(tle5012_port_sclk, GPIO.OUT, initial=GPIO.HIGH)
        # GPIO.setup(tle5012_port_cs, GPIO.OUT, initial=GPIO.HIGH)

    def grouper(self, iterable, n, fillvalue=0):
        "Collect data into fixed-length chunks or blocks"
        # Taken from itertools recipes
        # https://docs.python.org/2/library/itertools.html#recipes
        # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
        args = [iter(iterable)] * n
        return itertools.zip_longest(fillvalue=fillvalue, *args)

    def run(self):
        while True:
            if self.next_due < time.time():
                # print("start poll")
                self.poll()
                self.next_due = time.time() + self.frequency
                # time.sleep(0.05)

    def poll(self):
        try:
            slave = self.server.get_slave(self.slaveid)
            self.coils_value = slave.get_values('COILS', 0, 16)
            if self.coils_value != self.last_coils_value:
                self.last_coils_value = self.coils_value
                # for some modbus and spi reason, reversed the coils list  __zrd
                reversed_coils_value = list(reversed(self.coils_value))
                byte_strings = (''.join(bit_group) for bit_group in self.grouper(map(str, reversed_coils_value), 8))
                bytes = [int(byte_string, 2) for byte_string in byte_strings]
                resp = self.spi.xfer(bytes)
                # for i in range(16):
                #     print(str(self.coils_value[i]))
        except Exception as exc:
            print("Error: %s", exc)


class InputLoopThread(Thread):
    frequency = 0.01
    next_due = 0
    tmp = 0
    tmp_crc = 0
    ang_val = 0

    def __init__(self, server, slaveid):
        # change for multi threading
        super(InputLoopThread, self).__init__()
        self.server = server
        self.slaveid = slaveid
        # tle5012 port init
        self.tle5012_port_data = 21
        self.tle5012_port_sclk = 20
        self.tle5012_port_cs = 16
        self.tmp = 0
        self.tmp_crc = 0
        self.ang_val = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.tle5012_port_data, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.tle5012_port_sclk, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.tle5012_port_cs, GPIO.OUT, initial=GPIO.HIGH)
        # di input port init
        self.di0_8_bcm = [4, 18, 17, 27, 22, 23, 24, 25, 5]
        self.di_value = 0
        self.di_lastvalue = 0
        GPIO.setup(self.di0_8_bcm, GPIO.IN)


    def write5012(self, cmd):
        GPIO.output(self.tle5012_port_cs, GPIO.LOW)
        for i in range(16):
            GPIO.output(self.tle5012_port_sclk, GPIO.LOW)
            if cmd & 0x8000:
                GPIO.output(self.tle5012_port_data, GPIO.HIGH)
            else:
                GPIO.output(self.tle5012_port_data, GPIO.LOW)
            GPIO.output(self.tle5012_port_sclk, GPIO.HIGH)
            cmd <<= 1

    def read_angvalue(self):
        self.write5012(0x8021)
        GPIO.setup(self.tle5012_port_data, GPIO.IN)
        for i in range(16):
            GPIO.output(self.tle5012_port_sclk, GPIO.HIGH)
            time.sleep(0.01)
            if GPIO.input(self.tle5012_port_data):
                self.tmp |= 0x0001
            else:
                self.tmp &= 0xfffe
            GPIO.output(self.tle5012_port_sclk, GPIO.LOW)
            self.tmp <<= 1
        for i in range(16):
            GPIO.output(self.tle5012_port_sclk, GPIO.LOW)
            time.sleep(0.01)
            if GPIO.input(self.tle5012_port_data):
                self.tmp_crc |= 0x0001
            else:
                self.tmp_crc &= 0xfffe
            GPIO.output(self.tle5012_port_sclk, GPIO.HIGH)
            self.tmp_crc <<= 1
        GPIO.output(self.tle5012_port_cs, GPIO.HIGH)
        ang_val = self.tmp & 0x7fff
        GPIO.setup(self.tle5012_port_data, GPIO.OUT)
        return ang_val

    def run(self):
        while True:
            if self.next_due < time.time():
                # print("start poll")
                self.poll()
                self.next_due = time.time() + self.frequency
                # time.sleep(0.05)

    def poll(self):
        try:
            slave = self.server.get_slave(self.slaveid)
            # read DI input
            for i in range(8):
                if GPIO.input(self.di0_8_bcm[i]):
                    self.di_value |= (1 << i)
            if self.di_value != self.di_lastvalue:
                self.di_lastvalue = self.di_value
            slave.set_values('DISCRETE_INPUTS', 0, self.di_value)
            # read angvalue
            slave.set_values('HOLDING_REGISTERS', 0, self.read_angvalue())
            values = slave.get_values('HOLDING_REGISTERS', 0, 1)

        except Exception as exc:
            print("Error: %s", exc)


def main():
    """main"""
    slaveid = 1
    logger = modbus_tk.utils.create_logger(name="console", record_format="%(message)s")

    try:
        # Create the server
        server = modbus_tcp.TcpServer(address='192.168.1.132')
        logger.info("running...")
        logger.info("enter 'quit' for closing the server")

        server.start()

        slave_1 = server.add_slave(slaveid)
        slave_1.add_block('HOLDING_REGISTERS', cst.HOLDING_REGISTERS, 0, 20)
        slave_1.add_block('DISCRETE_INPUTS', cst.DISCRETE_INPUTS, 0, 10)
        slave_1.add_block('COILS', cst.COILS, 0, 16)
        # 初始化HOLDING_REGISTERS值
        # 命令行读取COILS的值 get_values 1 2 0 5
        init_value = 0xff
        length = 8
        init_value_list = [init_value]*length
        slave = server.get_slave(1)
        slave.set_values('HOLDING_REGISTERS', 0, init_value_list)

        thread_1 = InputLoopThread(server, slaveid)
        thread_1.start()
        thread_2 = OutputLoopThread(server, slaveid)
        thread_2.start()

        while True:
            cmd = sys.stdin.readline()
            args = cmd.split(' ')

            if cmd.find('quit') == 0:
                sys.stdout.write('bye-bye\r\n')
                break

            elif args[0] == 'add_slave':
                slave_id = int(args[1])
                server.add_slave(slave_id)
                sys.stdout.write('done: slave %d added\r\n' % slave_id)

            elif args[0] == 'add_block':
                slave_id = int(args[1])
                name = args[2]
                block_type = int(args[3])
                starting_address = int(args[4])
                length = int(args[5])
                slave = server.get_slave(slave_id)
                slave.add_block(name, block_type, starting_address, length)
                sys.stdout.write('done: block %s added\r\n' % name)

            elif args[0] == 'set_values':
                slave_id = int(args[1])
                name = args[2]
                address = int(args[3])
                values = []
                for val in args[4:]:
                    values.append(int(val))
                slave = server.get_slave(slave_id)
                slave.set_values(name, address, values)
                values = slave.get_values(name, address, len(values))
                sys.stdout.write('done: values written: %s\r\n' % str(values))

            elif args[0] == 'get_values':
                slave_id = int(args[1])
                name = args[2]
                address = int(args[3])
                length = int(args[4])
                slave = server.get_slave(slave_id)
                values = slave.get_values(name, address, length)
                sys.stdout.write('done: values read: %s\r\n' % str(values))

            else:
                sys.stdout.write("unknown command %s\r\n" % args[0])
    finally:
        server.stop()
        GPIO.cleanup()


if __name__ == "__main__":
    main()
