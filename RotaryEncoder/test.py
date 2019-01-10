from time import sleep
import RPi.GPIO as GPIO
from KY040 import KY040


CLOCKPIN = 14
DATAPIN = 15
SWITCHPIN = 10


def rotaryChange(direction, count):
    print("turned - " + str(count))


def switchPressed(count):
    print("button pressed - " + str(count))


GPIO.setmode(GPIO.BCM)

ky040 = KY040(CLOCKPIN, DATAPIN, SWITCHPIN, rotaryChange, switchPressed)

ky040.start()

try:
    while True:
        sleep(0.1)
finally:
    ky040.stop()
    GPIO.cleanup()
