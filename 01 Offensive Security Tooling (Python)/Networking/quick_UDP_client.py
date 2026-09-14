# Quick-and-Dirty UDP Client

import socket

target_host = "127.0.0.1"
target_port = 9997

# create a socket object
# AF_INET = use standard IPv4 address, SOCK_STREAM = use TCP
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# send some data
client.sendto(b"AAABBBCCC", (target_host, target_port))

# receive some data
data, addr = client.recvfrom(4096)

# we have to decode() for readability, since the response will be a byte string
print(data.decode())
client.close()
