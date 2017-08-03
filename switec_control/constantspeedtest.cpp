
#define PIN_VCC     3
#define PIN_GND     4
#define PIN_SENSE  A0

#define FORWARD  1
#define REVERSE -1
#define SAFE_DELAY 1000
#define COUNT_DELAY 1000

int maxSteps = 2000;  // stop counting at this many steps

#include "SwitecX25.h"
#include "PhotoInterrupter.h"

SwitecX25 motor(315*3, 8,9,10,11);
PhotoInterrupter sensor(PIN_VCC,PIN_GND,PIN_SENSE);

/* Step the motor one or more step.
 * Reset motor.currentStep to support stopless motor.
 * By default steps forward 1 step.
 */
void stepMotor(int direction=FORWARD, unsigned int microSecondsDelay=SAFE_DELAY, int count=1)
{
  for (int i=0;i<count;i++) {
    if (direction==FORWARD) {
      motor.currentStep = 0;
      motor.stepUp();
    } else {
      motor.currentStep = 1;
      motor.stepDown();
    }
    delayMicroseconds(microSecondsDelay);
  }
}

/*
 * Turn the motor slowly in reverse until the sensor triggers.
 * Returns the number of steps stepped.
 * skipSteps indicates a number of steps to turn regardless of sensor setting.
 * Set skipSteps if the motor might be in the sensor trigger zone already.
 */
int countSteps(int skipSteps=0, int delay=SAFE_DELAY)
{
  int steps = 0;
  while (skipSteps>0 || sensor.IsLow() && steps<maxSteps) {
    stepMotor(REVERSE, delay);
    if (skipSteps>0) skipSteps--;
    steps++;
  }
  return steps;
}

/*
 * Turns the motor forward at constant speed and reports
 * the number of steps required to get back to zero point.
 */
void constantReverseTest(void)
{
  Serial.println("constantReverseTest");
  Serial.println("Is it repeatable?");
  int delay0 =  500;
  int delay1 = 2000;
  int ddelay =   20;
  int repeat =    5;
  int steps  =  500;

  unsigned short accelTable[][2] = {{steps, delay0}}; // steps, delay
  motor.accelTable = accelTable;
  motor.maxVel = steps; // dont read past first entry

  for (int delay=delay0; delay<=delay1; delay+=ddelay) {
    Serial.print(delay);
    countSteps(50);               // reset needle position
    unsigned long sumRealDelay = 0;
    accelTable[0][1] = delay;
    for (int i=0;i<repeat;i++) {
      motor.currentStep = 0;
      motor.setPosition(steps);
      unsigned long time0 = micros();
      while (!motor.stopped) motor.update();
      unsigned long elapsed = micros() - time0;
      delayMicroseconds(1000);  // give the motor time to overshoot before we rewind?  No, need min interval between signal change
      sumRealDelay += elapsed / (steps-1);
      int steps = countSteps(2, COUNT_DELAY);
      Serial.print(" | ");
      Serial.print(steps % 1080);
    }
    unsigned long realDelay = sumRealDelay / repeat;
    unsigned long stepsPerSecond = 1000000 / realDelay;  // steps per second
    unsigned long degreesPerSecond = 1000000 / 3 / realDelay;  // degrees per second
    Serial.print(" | ");
    Serial.print(realDelay);  // mean measured period
    Serial.print(" | ");
    Serial.print(stepsPerSecond);  // mean measured period
    Serial.print(" | ");
    Serial.print(degreesPerSecond);  // mean measured period
    Serial.println();
  }
}


void setup(void)
{
  Serial.begin(9600);
}

void loop(void)
{
  constantReverseTest();
}