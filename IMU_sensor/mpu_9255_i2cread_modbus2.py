import sys, getopt

sys.path.append('.')
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
import smbus

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

q = queue.Queue(10)


class InputLoopThread(threading.Thread):
    frequency = 0.05
    next_due = 0
    tmp = 0
    tmp_crc = 0
    ang_val = 0

    def __init__(self, server, slaveid, mpu9255_channel_num, ad0_via_gpio):
        # multi threading things
        super(InputLoopThread, self).__init__()
        self.__running = threading.Event()
        self.__running.set()
        self.server = server
        self.slaveid = slaveid
        self.total_channel_num = mpu9255_channel_num
        self.ad0_via_gpio = ad0_via_gpio

        GPIO.setmode(GPIO.BCM)
        GPIO.cleanup()

        for i in range(self.total_channel_num):
            GPIO.setup(self.ad0_via_gpio[i], GPIO.OUT, initial=GPIO.HIGH)

        for i in range(self.total_channel_num):
            GPIO.setup(self.ad0_via_gpio[i], GPIO.OUT, initial=GPIO.LOW)
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

    def read_byte(self, adr):
        return bus.read_byte_data(address, adr)

    def read_word(self, adr):
        high = bus.read_byte_data(address, adr)
        low = bus.read_byte_data(address, adr + 1)
        val = (high << 8) + low
        return val

    def read_word_2c(self, adr):
        val = self.read_word(adr)
        if val >= 0x8000:
            return -((65535 - val) + 1)
        else:
            return val

    def stop(self):
        self.__running.clear()

    def run(self):
        while self.__running.is_set():
            if self.next_due < time.time():
                # print("start poll")
                self.poll()
                self.next_due = time.time() + self.frequency
                # self.next_due = time.time() + self.poll_interval*0.001
        return

    def poll(self):
        slave = self.server.get_slave(self.slaveid)
        for i in range(total_channel_num):
            GPIO.setup(channel_ad0_via_gpio[i], GPIO.OUT, initial=GPIO.LOW)
            time.sleep(0.01)
            try:
                accel_xout = self.read_word_2c(accel_xout_h)  # We just need to put H byte address
                accel_yout = self.read_word_2c(accel_yout_h)  # as we are reading the word data
                accel_zout = self.read_word_2c(accel_zout_h)
                print("%d# channel: %d, %d, %d" % (i, accel_xout, accel_yout, accel_zout))
            except Exception as exc:
                print("%d# channel: failed" % i)
            GPIO.setup(channel_ad0_via_gpio[i], GPIO.OUT, initial=GPIO.HIGH)
            time.sleep(0.01)
            if accel_xout > 0:
                sign_xout = 0
            else:
                sign_xout = 1
            if accel_yout > 0:
                sign_yout = 0
            else:
                sign_yout = 1
            if accel_zout > 0:
                sign_zout = 0
            else:
                sign_zout = 1
            slave.set_values('READ_INPUT_REGISTERS', i*6, sign_xout)
            slave.set_values('READ_INPUT_REGISTERS', i*6+1, accel_xout)
            slave.set_values('READ_INPUT_REGISTERS', i*6+2, sign_yout)
            slave.set_values('READ_INPUT_REGISTERS', i*6+3, accel_yout)
            slave.set_values('READ_INPUT_REGISTERS', i*6+4, sign_zout)
            slave.set_values('READ_INPUT_REGISTERS', i*6+5, accel_zout)
            values = slave.get_values('READ_INPUT_REGISTERS', 0, 6*total_channel_num)




def main():
    """main"""
    slaveid = 1
    logger = modbus_tk.utils.create_logger(name="console", record_format="%(message)s")

    try:

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
        slave_1.add_block('READ_INPUT_REGISTERS', cst.READ_INPUT_REGISTERS, 0, 6*total_channel_num)
        slave_1.add_block('COILS', cst.COILS, 0, 16)
        # 初始化HOLDING_REGISTERS值
        # 命令行读取COILS的值 get_values 1 2 0 5
        init_value = 0x0
        length = 16
        init_value_list = [init_value]*length
        slave = server.get_slave(1)
        slave.set_values('HOLDING_REGISTERS', 0, init_value_list)

        thread_1 = InputLoopThread(server, slaveid, total_channel_num, channel_ad0_via_gpio)
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
        # thread_3.join()
        # while True:
        #     cmd = sys.stdin.readline()
        #     args = cmd.split(' ')
        #
        #     if cmd.find('quit') == 0:
        #         sys.stdout.write('bye-bye\r\n')
        #         break
        #
        #     elif args[0] == 'add_slave':
        #         slave_id = int(args[1])
        #         server.add_slave(slave_id)
        #         sys.stdout.write('done: slave %d added\r\n' % slave_id)
        #
        #     elif args[0] == 'add_block':
        #         slave_id = int(args[1])
        #         name = args[2]
        #         block_type = int(args[3])
        #         starting_address = int(args[4])
        #         length = int(args[5])
        #         slave = server.get_slave(slave_id)
        #         slave.add_block(name, block_type, starting_address, length)
        #         sys.stdout.write('done: block %s added\r\n' % name)
        #
        #     elif args[0] == 'set_values':
        #         slave_id = int(args[1])
        #         name = args[2]
        #         address = int(args[3])
        #         values = []
        #         for val in args[4:]:
        #             values.append(int(val))
        #         slave = server.get_slave(slave_id)
        #         slave.set_values(name, address, values)
        #         values = slave.get_values(name, address, len(values))
        #         sys.stdout.write('done: values written: %s\r\n' % str(values))
        #
        #     elif args[0] == 'get_values':
        #         slave_id = int(args[1])
        #         name = args[2]
        #         address = int(args[3])
        #         length = int(args[4])
        #         slave = server.get_slave(slave_id)
        #         values = slave.get_values(name, address, length)
        #         sys.stdout.write('done: values read: %s\r\n' % str(values))
        #
        #     else:
        #         sys.stdout.write("unknown command %s\r\n" % args[0])
    finally:
        thread_1.stop()
        # thread_2.stop()
        # thread_3.stop()
        server.stop()
        GPIO.cleanup()


if __name__ == "__main__":
    main()
