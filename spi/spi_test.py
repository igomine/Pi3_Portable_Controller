'''
    stange, first not work, later work well, same code
'''
import spidev
import time


bus = 0
device = 0
spi = spidev.SpiDev(bus, device)
spi.open(0, 0)

# print(spi.mode)
# print(spi.threewire)
# print(spi.cshigh)
# print(spi.bits_per_word)
# print(spi.lsbfirst)
spi.mode = 0b11
spi.max_speed_hz = 50


spi.cshigh = False


# 0xff select all the bit-sel ,0xa4 send to seg-sel
spi_send = [0x00, 0xc0]


try:
    while True:
        resp = spi.xfer(spi_send)
        time.sleep(1)
except KeyboardInterrupt:
    print("exit")
    spi.close()
