# custom Python Netcat utility (BHP Net Tool) designed to act as a versatile network swiss-army knife — supporting TCP client connections,
# server listening modes, file uploads, remote command execution, and interactive command shells.

import argparse  # parsing command-line arguments
import socket  # low level network functionality, like setting up a TCP connection or listening on a port
import shlex  # safely splitting strings into meaningful chunks, or tokens, like a shell does
# process creation and interaction, like running a shell command and recording the output
import subprocess
import sys  # system level functions, like sys.exit()
import textwrap  # formatting utility
import threading  # threading, or running code concurrently


def execute(cmd):  
    cmd = cmd.strip()  # removes whitespace around the cmd string
    if not cmd:  # error handling in case no cmd is given
        return
    output = subprocess.check_output(
        shlex.split(cmd), stderr=subprocess.STDOUT)
    # subprocess.check_output() will run cmd as a subprocess, wait for it to finish, then capture the output in bytes
    # shlex.split(cmd) will break the cmd string into a list of arguments that the shell can read/understand
    # stderr=subprocess.STDOUT merges the stderr and stdout streams together so we can capture errors and display them

    return output.decode()  # .decode() is necessary since the output is in bytes


if __name__ == '__main__':
    # argument parser and initialization
    parser = argparse.ArgumentParser(
        description='BHP Net Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''Example:
                        netcat.py -t 192.168.1.108 -p 5555 -l -c # command shell
                        netcat.py -t 192.168.1.108 -p 5555 -l -u=mytest.txt # upload to file
                        netcat.py -t 192.168.1.108 -p 5555 -l -e=\"cat /etc/passwd\" # execute command
                        echo 'ABC | .\netcat.py -t 192.168.1.108 -p 135 # echo text to server port 135
                        netcat.py -t 192.168.1.108 -p 5555 # connect to server
        '''))
parser.add_argument('-c', '--command', action='store_true',
                    help='command shell')
parser.add_argument('-e', '--execute', help='execute specified command')
parser.add_argument('-l', '--listen', action='store_true', help='listen')
parser.add_argument('-p', '--port', type=int, default=5555, help='specified port')
parser.add_argument(
    '-t', '--target', default='192.168.1.203', help='specified IP')
parser.add_argument('-u', '--upload', help='upload file')
args = parser.parse_args()
if args.listen:
    buffer = ''
else:
    buffer = sys.stdin, read()

nc = NetCat(args, buffer.encode())
nc.run()


class NetCat:
    def __init__(self, args, buffer=None):
        self.args = args
        self.buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create a TCP socket
        # configuration to reuse local addresses to avoid errors if listener is restarted quickly
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 

    def run(self):
        if self.args.listen: # if listen flag is active, start as a server in listener mode
            self.listen()
        else:
            self.send() # otherwise act as client and connect outward

    # client mode 
    def send(self):
        self.socket.connect((self.args.target, self.args.port)) # connects to remote target IP and port
        if self.buffer:
            self.socket.send(self.buffer) # if data was already given via stdin, send immediately upon connection

        try:
            while True: # open loop to maintain interactive session
                recv_len = 1 # trackers for incoming data
                response = ''
                while recv_len: # loop to read data from server in 4096 byte chunks until complete
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 4096: # if chunk is less than 4096, then this is the end of the data
                        break
                if response:
                    print(response) # print server's response to the terminal
                    buffer = input('> ') # prompt user for a command
                    buffer += '\n'
                    self.socket.send(buffer.encode()) # that is then sent back to the server
        except KeyboardInterrupt:
            print('User terminated.')
            self.socket.close()
            sys.exit()

    # server mode
    def listen(self):
        self.socket.bind((self.args.target, self.args.port)) # binds socket to the local address/port
        self.socket.listen(5) # listen with a backlog of 5
        while True: # loop to accept incoming client connections
            client_socket, _ = self.socket.accept()
            client_thread = threading.Thread( # spawn a thread whenever we get a connection to handle it
                target=self.handle, args=(client_socket,)
            )
            client_thread.start()

    # what happens when a client connects based on flags passed
    def handle(self, client_socket):
        if self.args.execute: # if '-e' was passed we 'execute'
            output = execute(self.args.execute) # execute the command on our local system 
            client_socket.send(output.encode()) # send output back to client

        elif self.args.upload: # if '-u' was passed then it's for a file upload
            file_buffer = b''
            while True:
                data = client_socket.recv(4096) # receive data in 4096 byte chunks
                if data:
                    file_buffer += data # save that data to the buffer
                else:
                    break

            with open(self.args.upload, 'wb') as f: # open a file, then write the buffer to disk
                f.write(file_buffer)
            message = f'Saved file {self.args.upload}'
            client_socket.send(message.encode()) # sent success message to client

        elif self.args.command: # if '-c' was passed we open a remote interactive shell, allowing client to send commands
            cmd_buffer = b''
            while True: # loop to accept multiple commands from lient
                try:
                    client_socket.send(b'BHP: #> ') # prompts the client like a terminal
                    while '\n' not in cmd_buffer.decode(): # as long as client hasn't pressed 'enter', keep accepting data
                        cmd_buffer += client_socket.recv(64) # add received data to buffer
                    response = execute(cmd_buffer.decode()) # once a full command is received, execute it and capture output
                    if response: # if command produced output, encode it and send back to the client
                        client_socket.send(response.encode())
                    cmd_buffer = b'' # clear the buffer, ready for next command
                except Exception as e: # catches network exceptions or a dropped connection
                    print(f'server killed {e}')
                    self.socket.close()
                    sys.exit()
