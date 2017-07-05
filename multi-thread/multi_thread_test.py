#!/usr/bin/env python
# -*- coding: utf_8 -*-
"""

"""

import sys
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_tcp
import RPi.GPIO as GPIO
from threading import Thread
import time


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
        # GPIO.setup(tle5012_port_data, GPIO.OUT, initial=GPIO.HIGH)
        # GPIO.setup(tle5012_port_sclk, GPIO.OUT, initial=GPIO.HIGH)
        # GPIO.setup(tle5012_port_cs, GPIO.OUT, initial=GPIO.HIGH)

    def run(self):
        while True:
            if self.next_due < time.time():
                # print("start poll")
                self.poll()
                self.next_due = time.time() + self.frequency

    def poll(self):
        try:
            slave = self.server.get_slave(self.slaveid)
            self.coils_value = slave.get_values('coils', 0, 8)
            if self.coils_value != self.last_coils_value:
                self.last_coils_value = self.coils_value
                for i in range(8):
                    print(str(self.coils_value[i]))
        except Exception as exc:
            print("Error: %s", exc)


class InputLoopThread(Thread):
    frequency = 0.01
    next_due = 0
    tle5012_port_data = 21
    tle5012_port_sclk = 20
    tle5012_port_cs = 16
    tmp = 0
    tmp_crc = 0
    ang_val = 0

    def __init__(self, server, slaveid):
        # change for multi threading
        super(InputLoopThread, self).__init__()
        self.server = server
        self.slaveid = slaveid
        # tle5012 port init
        tle5012_port_data = 21
        tle5012_port_sclk = 20
        tle5012_port_cs = 16
        self.tmp = 0
        self.tmp_crc = 0
        self.ang_val = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(tle5012_port_data, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(tle5012_port_sclk, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(tle5012_port_cs, GPIO.OUT, initial=GPIO.HIGH)

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

    def poll(self):
        try:
            slave = self.server.get_slave(self.slaveid)
            slave.set_values('0', 0, self.read_angvalue())
            values = slave.get_values('0', 0, 1)
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
        slave_1.add_block('0', cst.HOLDING_REGISTERS, 0, 100)
        slave_1.add_block('1', cst.DISCRETE_INPUTS, 0, 100)
        slave_1.add_block('coils', cst.COILS, 0, 100)
        # 初始化HOLDING_REGISTERS值
        # 命令行读取COILS的值 get_values 1 2 0 5
        init_value = 0xff
        length = 8
        init_value_list = [init_value]*length
        slave = server.get_slave(1)
        slave.set_values('0', 0, init_value_list)

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
