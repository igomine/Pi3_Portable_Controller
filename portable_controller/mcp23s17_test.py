from RPiMCP23S17.MCP23S17 import MCP23S17
import time

mcp_U3 = MCP23S17(bus=0x00, ce=0x00, deviceID=0x02)
mcp_U2 = MCP23S17(bus=0x00, ce=0x00, deviceID=0x01)
mcp_U2.open()
mcp_U3.open()

for x in range(0, 16):
    mcp_U3.setDirection(x, mcp_U3.DIR_OUTPUT)
    mcp_U2.setDirection(x, mcp_U2.DIR_OUTPUT)

print("Starting blinky on all pins (CTRL+C to quit)")

while (True):
    for x in range(0, 16):
        mcp_U2.digitalWrite(x, MCP23S17.LEVEL_HIGH)
        mcp_U3.digitalWrite(x, MCP23S17.LEVEL_HIGH)
    time.sleep(1)

    for x in range(0, 16):
        mcp_U2.digitalWrite(x, MCP23S17.LEVEL_LOW)
        mcp_U3.digitalWrite(x, MCP23S17.LEVEL_LOW)
    time.sleep(1)

    # the lines below essentially have the same effect as the lines above
    # mcp1.writeGPIO(0xFFF)
    # mcp2.writeGPIO(0xFFF)
    # time.sleep(1)
    #
    # mcp1.writeGPIO(0x000)
    # mcp2.writeGPIO(0x0000)
    # time.sleep(1)