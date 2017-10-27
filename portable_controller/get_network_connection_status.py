import socket
import os
import fcntl
import struct

# method 1
# gw = os.popen("ip -4 route show default").read().split()
# s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# s.connect((gw[2], 0))
# ipaddr = s.getsockname()[0]
# print("IP:", ipaddr)

# method 2

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(  fcntl.ioctl(  s.fileno(), 0x8915, struct.pack(bytes, ifname[:15])  ) [20:24] )


out = os.popen("ifconfig | grep 'inet addr:' | grep -v '127.0.0.1' | cut -d: -f2 | awk '{print $1}' | head -1").read()
print(out)


# print(get_ip_address("eth0"))