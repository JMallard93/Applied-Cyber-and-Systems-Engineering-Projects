# Quick-and-Dirty TCP Client

import socket

target_host = "www.google.com"
target_port = 80

# create a socket object
# AF_INET = use standard IPv4 address, SOCK_STREAM = use TCP
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect the client
client.connect((target_host, target_port))

# send some data
# the "b" before the string indicates that it's a byte string. Data sent over sockets must be in bytes
client.send(b"GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")

# receive some data
response = client.recv(4096)

# we have to decode() for readability, since the response will be a byte string
print(response.decode())
client.close()
