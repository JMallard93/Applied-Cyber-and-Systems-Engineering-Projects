# multi-threaded TCP Server

import socket
import threading

IP = '0.0.0.0'  # our listening address and port, 0.0.0.0 means the server will listen on all available network interfaces
PORT = 9998


def main():
    # our main server socket object, AF_INET = use standard IPv4 address, SOCK_STREAM = use TCP
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # bind() associates IP addresses and port numbers. now the socket is tied to 0.0.0.0:9998
    server.bind((IP, PORT))
    # start listening, with a maximum backlog of 5 connections before rejecting new connections
    server.listen(5)
    print(f'[*] Listening on {IP}:{PORT}')

    while True:
        client, address = server.accept()  # blocking line, the program will wait here until a client tries to connect. When it does it will store the client and address information. The address information will be a tuple with IP address and port, e.g. ('192.168.1.10', 9797)
        print(f'[*] Accepted connection from {address[0]}:{address[1]}')
        # multi-threading. threading.Thread() creates a thread object. target=handle_client specifies the new thread should execute the handle_client function (which is defined below main()). (client,) is the argument for handle_client, the comma causes (client,) to be treated as a tuple
        client_handler = threading.Thread(target=handle_client, args=(client,))
        client_handler.start()  # starts the newly created thread


def handle_client(client_socket):  # how the server will communicate with the client
    with client_socket as sock:  # this "with" statement ensures that the connection will be closed, even if there's an error in the next code block
        # another blocking line, the thread will wait here until the client sends data
        request = sock.recv(1024)
        # decodes the received byte string into readable text and prints it
        print(f'[*] Received: {request.decode("utf-8")}')
        # the "b" indicates a byte string, the server sends an ACK message back to the client
        sock.send(b'ACK')


if __name__ == '__main__':
    main()
