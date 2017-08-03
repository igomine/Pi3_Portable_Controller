import wiringpi as gpio
import time
for i in range(5):
    t1 = gpio.micros()
    t1 = gpio.micros()
    # gpio.delayMicroseconds(500)
    time.sleep(0.0005)
    t2 = gpio.micros()
    print(t2-t1)
