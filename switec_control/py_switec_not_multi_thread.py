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
import threading
import random

# // This table defines the acceleration curve.
# // 1st value is the speed step, 2nd value is delay in microseconds
# // 1st value in each row must be > 1st value in subsequent row
# // 1st value in last row should be == maxVel, must be <= maxVel
# RESET_STEP_MICROSEC = 800
RESET_STEP_MICROSEC = 8000
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

# // State  3 2 1 0   Value

#            R   L
# // 0      1 0 0 1   0x9
# // 1      0 0 0 1   0x1
# // 2      0 1 1 1   0x7
# // 3      0 1 1 0   0x6
# // 4      1 1 1 0   0xE
# // 5      1 0 0 0   0x8
stateMap = [0x9, 0x1, 0x7, 0x6, 0xE, 0x8]


class SwitecX25(object):

    def __init__(self):
        # multi threading things
        # super(SwitecX25, self).__init__()
        # self.__running = threading.Event()
        # self.__running.set()
        # io connect to switec motor
        # self.pins = [6, 13, 26, 19]
        self.pins = [26, 19, 6, 13]
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
        self.steps = 810                   # total steps available
        self.time0 = None                     # time when we entered this state
        self.microDelay = None               # microsecs until next state
        self.vel = 0                        # steps travelled under acceleration
        self.dir = 0                        # direction -1,0,1
        self.stopped = True                 # true if stopped
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
            time.sleep(RESET_STEP_MICROSEC/1000000)
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
            # self.time0 = time.time()
            self.time0 = time.clock()
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
            # case 1 : moving towards target (maybe under accel or decel)
            if delta < self.vel:            # time to declerate
                self.vel -= 1
            elif self.vel < self.maxVel:    # accelerating
                self.vel += 1
            else:
                pass                        # at full speed - stay there
        # case 2 : at or moving away from target (slow down!)
        else:
            self.vel -= 1

        # vel now defines delay
        i = 0
        while self.accelTable[i][0] < self.vel:
            i += 1
        self.microDelay = self.accelTable[i][1]
        # self.time0 = time.time()
        self.time0 = time.clock()

    def setposition(self, pos):
        if pos >= self.steps:
            pos = self.steps - 1
        self.targetStep = pos
        if self.stopped:
            self.stopped = False
            # self.time0 = time.time()
            self.time0 = time.clock()
            self.microDelay = 0

    def update(self):
        if not self.stopped:
            # delta = (time.time() - self.time0)*1000000
            delta = (time.clock() - self.time0) * 1000000
            if delta >= self.microDelay:
                self.advance()

    def updateblocking(self):
        while self.stopped:
            delta = time.time() - self.time0
            if delta >= self.microDelay:
                self.advance()

    def stop(self):
        self.__running.clear()

    def run(self):
        while self.__running.is_set():
            if not self.stopped:
                # delta = (time.time() - self.time0)*1000000
                delta = (time.clock() - self.time0) * 1000000
                if delta >= self.microDelay:
                    self.advance()
        return


def main():
    thread_1 = SwitecX25()
    thread_1.zero()
    thread_1.setposition(405)

    # flag = 1
    # thread_1.start()
    # while True:
    #     pass

    # meter_float = random.uniform(0, 810)
    # print("current position:%d" % meter_float)
    # thread_1.setposition(meter_float)



    # motor1 = SwitecX25()
    try:
        while True:
            thread_1.update()
            # time.sleep(3)
            # meter_float = random.uniform(0, 810)
            # print("current position:%d" % meter_float)
            # thread_1.setposition(meter_float)
    finally:
        thread_1.stop()
        GPIO.cleanup()


if __name__ == "__main__":
    main()
