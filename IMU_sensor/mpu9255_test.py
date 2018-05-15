import sys, getopt

sys.path.append('.')
import RTIMU
import os.path
import time
import math
import RPi.GPIO as GPIO

# define the total num connect to rasp
total_channel_num = 3
# and also define the AD0 pin of each mpu9255 ,connect to which gpio pin
channel_ad0_via_gpio = [9, 10, 11]

SETTINGS_FILE = "RTIMULib"

print("Using settings file " + SETTINGS_FILE + ".ini")
if not os.path.exists(SETTINGS_FILE + ".ini"):
  print("Settings file does not exist, will be created")

s = RTIMU.Settings(SETTINGS_FILE)
imu = RTIMU.RTIMU(s)

print("IMU Name: " + imu.IMUName())



GPIO.setmode(GPIO.BCM)
for i in range(total_channel_num):
    GPIO.setup(channel_ad0_via_gpio[i], GPIO.OUT, initial=GPIO.HIGH)

for i in range(total_channel_num):
    GPIO.setup(channel_ad0_via_gpio[i], GPIO.OUT, initial=GPIO.LOW)
    if (not imu.IMUInit()):
        print(" %d# IMU Init Failed" % i)
        sys.exit(1)
    else:
        print(" %d# IMU Init Succeeded" % i)
        time.sleep(0.5)

while True:
    for i in range(total_channel_num):
        GPIO.setup(channel_ad0_via_gpio[i], GPIO.OUT, initial=GPIO.LOW)
        time.sleep(0.01)
        if imu.IMURead():
            data = imu.getIMUData()
            fusionPose = data["fusionPose"]
            if i == 2:
                print("channel %d, r: %f p: %f y: %f" % (i, math.degrees(fusionPose[0]),
                                                        math.degrees(fusionPose[1]), math.degrees(fusionPose[2])))
        GPIO.setup(channel_ad0_via_gpio[i], GPIO.OUT, initial=GPIO.HIGH)
        time.sleep(0.01)
