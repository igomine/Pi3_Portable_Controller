import RPi.GPIO as GPIO
import time
"""
rs485 debug log, add by zrd, 2017.6.29
  read rotate value, transplant code from stm32, tzy
"""

""" Wiring Diagram
 +-----+-----+---------+------+---+---Pi 2---+---+------+---------+-----+-----+
 | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
 +-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
 |     |     |    3.3v |      |   |  1 || 2  |   |      | 5v      |     |     |
 |   2 |   8 |   SDA.1 |   IN | 1 |  3 || 4  |   |      | 5V      |     |     |
 |   3 |   9 |   SCL.1 |   IN | 1 |  5 || 6  |   |      | 0v      |     |     |
 |   4 |   7 | GPIO. 7 |   IN | 1 |  7 || 8  | 1 | ALT0 | TxD     | 15  | 14  |
 |     |     |      0v |      |   |  9 || 10 | 1 | ALT0 | RxD     | 16  | 15  |
 |  17 |   0 | GPIO. 0 |   IN | 0 | 11 || 12 | 1 | IN   | GPIO. 1 | 1   | 18  |
 |  27 |   2 | GPIO. 2 |   IN | 1 | 13 || 14 |   |      | 0v      |     |     |
 |  22 |   3 | GPIO. 3 |   IN | 0 | 15 || 16 | 0 | IN   | GPIO. 4 | 4   | 23  |
 |     |     |    3.3v |      |   | 17 || 18 | 0 | IN   | GPIO. 5 | 5   | 24  |
 |  10 |  12 |    MOSI | ALT0 | 0 | 19 || 20 |   |      | 0v      |     |     |
 |   9 |  13 |    MISO | ALT0 | 0 | 21 || 22 | 0 | IN   | GPIO. 6 | 6   | 25  |
 |  11 |  14 |    SCLK | ALT0 | 0 | 23 || 24 | 1 | OUT  | CE0     | 10  | 8   |
 |     |     |      0v |      |   | 25 || 26 | 1 | OUT  | CE1     | 11  | 7   |
 |   0 |  30 |   SDA.0 |   IN | 1 | 27 || 28 | 1 | IN   | SCL.0   | 31  | 1   |
 |   5 |  21 | GPIO.21 |   IN | 1 | 29 || 30 |   |      | 0v      |     |     |
 |   6 |  22 | GPIO.22 |   IN | 1 | 31 || 32 | 0 | IN   | GPIO.26 | 26  | 12  |
 |  13 |  23 | GPIO.23 |   IN | 0 | 33 || 34 |   |      | 0v      |     |     |
 |  19 |  24 | GPIO.24 |   IN | 0 | 35 || 36 | 0 | IN   | GPIO.27 | 27  | 16  |
 |  26 |  25 | GPIO.25 |   IN | 0 | 37 || 38 | 0 | IN   | GPIO.28 | 28  | 20  |
 |     |     |      0v |      |   | 39 || 40 | 0 | IN   | GPIO.29 | 29  | 21  |
 +-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
 | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
 +-----+-----+---------+------+---+---Pi 2---+---+------+---------+-----+-----+

gpio define(bcm)
data    21
sclk    20
cs      16
"""
tle5012_port_data = 21
tle5012_port_sclk = 20
tle5012_port_cs = 16
tmp = 0
tmp_crc = 0
ang_val = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup(tle5012_port_data, GPIO.OUT, initial = GPIO.HIGH)
GPIO.setup(tle5012_port_sclk, GPIO.OUT, initial = GPIO.HIGH)
GPIO.setup(tle5012_port_cs, GPIO.OUT, initial = GPIO.HIGH)


def write5012(cmd):
    GPIO.output(tle5012_port_cs, GPIO.LOW)
    for i in range(16):
        GPIO.output(tle5012_port_sclk, GPIO.LOW)
        if cmd & 0x8000:
            GPIO.output(tle5012_port_data, GPIO.HIGH)
        else:
            GPIO.output(tle5012_port_data, GPIO.LOW)
        GPIO.output(tle5012_port_sclk, GPIO.HIGH)
        cmd <<= 1


def read_angvalue():
    global tmp, tmp_crc, ang_val
    tmp = 0
    tmp_crc = 0
    GPIO.setup(tle5012_port_data, GPIO.IN)
    for i in range(16):
        GPIO.output(tle5012_port_sclk, GPIO.HIGH)
        time.sleep(0.01)
        if GPIO.input(tle5012_port_data):
            tmp |= 0x0001
        else:
            tmp &= 0xfffe
        GPIO.output(tle5012_port_sclk, GPIO.LOW)
        tmp <<= 1
    for i in range(16):
        GPIO.output(tle5012_port_sclk, GPIO.LOW)
        time.sleep(0.01)
        if GPIO.input(tle5012_port_data):
            tmp_crc |= 0x0001
        else:
            tmp_crc &= 0xfffe
        GPIO.output(tle5012_port_sclk, GPIO.HIGH)
        tmp_crc <<= 1
    GPIO.output(tle5012_port_cs, GPIO.HIGH)
    ang_val = tmp & 0x7fff
    GPIO.setup(tle5012_port_data, GPIO.OUT)

try:
    while True:
        write5012(0x8021)
        read_angvalue()
        print("value:%d" % ang_val)
        time.sleep(0.5)
except KeyboardInterrupt:
    GPIO.cleanup()
    print("exit")


