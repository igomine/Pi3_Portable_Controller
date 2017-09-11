import RPi.GPIO as GPIO
import time

# GPIO fix for making CE signal work
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(11, GPIO.OUT)
GPIO.setup(10, GPIO.OUT)

while True:
    GPIO.output(11, GPIO.LOW)
    GPIO.output(11, GPIO.HIGH)
    GPIO.output(10, GPIO.LOW)
    GPIO.output(10, GPIO.HIGH)