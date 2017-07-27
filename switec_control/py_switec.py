#!/usr/bin/env python
# -*- coding: utf_8 -*-
"""
    success to build up a modbus server by modbus tk
    poll the input and control output(spi), work with modbus server in multi-threading
    test by modbus poll in pc through wifi
        2017.7.14 zrd
"""

import RPi.GPIO as GPIO
import time


RESET_STEP_MICROSEC = 800
defaultAccelTable = [
    [20, 3000],
    [50, 1500],
    [100, 1000],
    [150,  800],
    [300,  600]
]
# 二维数组的行数
DEFAULT_ACCEL_TABLE_SIZE = 5

# // experimentation suggests that 400uS is about the step limit
# // with my hand-made needles made by cutting up aluminium from
# // floppy disk sliders.  A lighter needle will go faster.
#
# // State  3 2 1 0   Value
# // 0      1 0 0 1   0x9
# // 1      0 0 0 1   0x1
# // 2      0 1 1 1   0x7
# // 3      0 1 1 0   0x6
# // 4      1 1 1 0   0xE
# // 5      1 0 0 0   0x8
stateMap = [0x9, 0x1, 0x7, 0x6, 0xE, 0x8]


class SwitecX25(object):

    def __init__(self):
        # io connect to switec motor
        self.pins = [6, 13, 26, 19]
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(6, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(13, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(26, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(19, GPIO.OUT, initial=GPIO.LOW)

        self.pinCount = 4
        self.stateCount = 6
        # 6 steps
        self.currentState = 0
        # step we are currently at
        self.currentStep = 0
        # target we are moving to
        self.targetStep = 0
        self.steps = 3240            # total steps available
        self.time0=None           # time when we entered this state
        self.microDelay =None       # microsecs until next state
        self.vel = 0              # steps travelled under acceleration
        self.dir = 0                      # direction -1,0,1
        self.stopped = True               # true if stopped
        self.accelTable = defaultAccelTable

        # python另外增加的变量

        # 从c++不太好处理的两个变量
        # unsigned short (*accelTable)[2] # accel table can be modified.
        self.maxVel = 300           # fastest vel allowed

    def writeio(self):
        mask = stateMap[self.currentState]
        for i in range(self.pinCount):
            if mask & 0x01 == True:
                j = GPIO.HIGH
            else:
                j = GPIO.LOW
            GPIO.output(self.pins[i], j)
            mask >>= 1

    def stepup(self):
        if self.currentStep < self.steps:
            self.currentStep += 1
            self.currentState = (self.currentState + 1) % self.stateCount
            self.writeio()

    def stepdown(self):
        if self.currentStep > 0:
            self.currentStep -= 1
            self.currentState = (self.currentState + 5) % self.stateCount
            self.writeio()

    def zero(self):
        self.currentStep = self.steps - 1
        for i in range(self.steps):
            self.stepdown()
            time.sleep(RESET_STEP_MICROSEC*0.000001)
        self.currentStep = 0
        self.targetStep = 0
        self.vel = 0
        self.dir = 0

# // This function determines the speed and accel
# // characteristics of the motor.  Ultimately it
# // steps the motor once (up or down) and computes
# // the delay until the next step.  Because it gets
# // called once per step per motor, the calcuations
# // here need to be as light-weight as possible, so
# // we are avoiding floating-point arithmetic.
# //
# // To model acceleration we maintain vel, which indirectly represents
# // velocity as the number of motor steps travelled under acceleration
# // since starting.  This value is used to look up the corresponding
# // delay in accelTable.  So from a standing start, vel is incremented
# // once each step until it reaches maxVel.  Under deceleration
# // vel is decremented once each step until it reaches zero.

    def advance(self):
        if self.currentStep == self.targetStep and self.vel == 0:
            self.stopped = True
            self.dir = 0
            self.time0 = time.time()
            return
        if self.vel == 0:
            if self.currentStep < self.targetStep:
                self.dir = 1
            else:
                self.dir = -1
            self.vel = 1
        if self.dir > 0:
            self.stepup()
        else:
            self.stepdown()

        if self.dir > 0:
            delta = self.targetStep - self.currentStep
        else:
            delta = self.currentStep - self.targetStep

        if delta > 0:
            if delta < self.vel:
                self.vel -= 1
            elif self.vel < self.maxVel:
                self.vel += 1
            else:
                pass
        else:
            self.vel -= 1

        i = 0
        while self.accelTable[i][0] < self.vel:
            i += 1
        self.microDelay = self.accelTable[i][1]
        self.time0 = time.time()

    def setposition(self, pos):
        if pos >= self.steps:
            pos = self.steps - 1
        self.targetStep = pos
        if self.stopped:
            self.stopped = False
            self.time0 = time.time()
            self.microDelay = 0

    def update(self):
        if not self.stopped:
            delta = (time.time() - self.time0)*1000000
            if delta >= self.microDelay:
                self.advance()

    def updateblocking(self):
        while self.stopped:
            delta = time.time() - self.time0
            if delta >= self.microDelay:
                self.advance()


def main():
    motor1 = SwitecX25()
    try:
        motor1.zero()
        motor1.setposition(3240/2)

        while True:
            motor1.update()
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
