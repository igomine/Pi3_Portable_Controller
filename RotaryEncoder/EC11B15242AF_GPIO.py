import RPi.GPIO as GPIO
import time

PIN_A = 2
PIN_B = 3
PIN_KEY = 10
pulse_count = 0



def PIN_A_Callback(pin):
    global pulse_count
    if GPIO.input(PIN_A) == 1:
        data = GPIO.input(PIN_B)
        if data == 1:
            pulse_count = pulse_count - 1
        else:
            pulse_count = pulse_count + 1
    else:
        data = GPIO.input(PIN_B)
        if data == 1:
            pulse_count = pulse_count + 1
        else:
            pulse_count = pulse_count - 1
    print(pulse_count)

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(PIN_A, GPIO.BOTH, callback=PIN_A_Callback, bouncetime=5)
while True:
    time.sleep(1)
