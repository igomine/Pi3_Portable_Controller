import sys
import time

from ads1256 import pyads1256

ads = pyads1256.ADS1256()
ads.init()
idNumber = ads.ReadID()
print("\nADS1256 reported ID value: {}".format(idNumber))

print("\nPress CTRL-C to interrupt..")

try:
    while True:
        ads.SetInputMux(ads.MUX_AIN0, ads.MUX_AINCOM)
        time.sleep(0.2)  # Multiple of line frequency period
        val = ads.ReadADC()
        sys.stdout.write("AIN_0 value: {:d} -- ".format(val))

        # print Voltage
        vtemp = val*100/167
        print("Voltage: %d.%d %d V" % (vtemp/1000000, vtemp%1000000/1000, vtemp%1000))

        # ads.SetInputMux(ads.MUX_AIN1, ads.MUX_AINCOM)
        # time.sleep(0.2)
        # val = ads.ReadADC()
        # sys.stdout.write("AIN_1 value: {:d}\n".format(val))
        # sys.stdout.flush()

        time.sleep(0.3)

except KeyboardInterrupt:
    print("exit")
    ads.spi_close()




