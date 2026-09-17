# Custom network proxy that intercepts, inspects, hex-dumps, and relays TCP traffic between a local client
# and a remote server, allowing for real-time packet modification and analysis.

import sys
import socket
import threading

# filters each ASCII value, if it's printable then keep it, otherwise replace non-printable bytes with dots for readability
HEX_FILTER = ''.join(
	[(len(repr(chr(i))) == 3) and chr(i) or '.' for i in range(256)])

# formats binary/string data into standard hexadecimal and printable text
def hexdump(src, length=16, show=True):
	if isinstance(src, bytes): # converts byte data into a string if necessary
		src = src.decode()

	results = list() # initialize a list for the formatted lines of the hexdump
	for i in range(0, len(src), length): # loops through the data in 16 byte chunks
		word = str(src[i:i+length]) # turns the chunk of data into a string

		printable = word.translate(HEX_FILTER) # if it's a non-printable character, turn it into a dot using HEX_FILTER
		hexa = ' '.join([f'{ord(c):02X}' for c in word]) # converts each character into into it's hexadecimal
		hexwidth = length*3 # formatting
		results.append(f'{i:04x}  {hexa:<{hexwidth}} {printable}') # puts the results into one row
	# if show is True, print each row to the console. Otherwise return the list of formatted strings
	if show:
		for line in results:
			print(line)
	else:
		return results

# response modification handler
def receive_from(connection):
	buffer = b"" # initialize an empty byte string buffer
	connection.settimeout(5) # set a 5 second timeout for if the sender stops talking
	try:
		while True: # continuously look for data from the socket
			data = connection.recv(4096) # read 4096 bytes at a time, creating a chunk
			if not data: # break out of the loop if the connection is closed
				break
			buffer += data # appends the data chunk to our buffer
	except Exception as e: # silently catch timeouts or socket errors
		pass
	return buffer

# packet handler, add code to modify packet
def request_handler(buffer):
	# perform packet modifications
	return buffer

# packet handler, add code to modify packet
def response_handler(buffer):
	# perform packet modifications
	return buffer

# core proxy function
def proxy_handler(client_socket, remote_host, remote_port, receive_first):
	remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create new TCP socket
	remote_socket.connect((remote_host, remote_port)) # establist connection to remote host

	if receive_first: # checks if we need to grab a greeting banner from remote server before waiting for client (protocol dependent)
		remote_buffer = receive_from(remote_socket) # pulls initial data
		hexdump(remote_buffer) # prints hex dump of that data

	remote_buffer = response_handler(remote_buffer) # modify the buffer with response_handler()
	if len(remote_buffer): # if data was received 
		print("[<==] Sending %d bytes to localhost." % len(remote_buffer)) # log that there was a response (which is the print statement)
		client_socket.send(remote_buffer) # and send to the client

	# loop for packet relay
	while True:
		local_buffer = receive_from(client_socket) # receive data from the local client
		if len(local_buffer): # if the client sent data
			line = "[==>] Received %d bytes from localhost." % len(local_buffer)
			print(line) # log that there was a response
			hexdump(local_buffer) # and print its hexdump

			local_buffer = request_handler(local_buffer) # modify the buffer with response_handler()
			remote_socket.send(local_buffer) # forward to the remote server
			print("[==>] Sent to remote.") 

		# same as previous block, but we're receiving data from the remote server, instead of the local client
		remote_buffer = receive_from(remote_socket)
		if len(remote_buffer):
			print("[<==] Received %d bytes from remote." % len(remote_buffer))
			hexdump(remote_buffer)

			remote_buffer = response_handler(remote_buffer)
			client_socket.send(remote_buffer)
			print("[<==] Sent to localhost.")

		if not len(local_buffer) or not len(remote_buffer): # if either side drops connection or doesn't send data
			client_socket.close() # close both connections
			remote_socket.close()
			print("[*] No more data. Closing connections.")
			break

# server listening setup
def server_loop(local_host, local_port,
		remote_host, remote_port, receive_first):
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # creates TCP socket
	try:
		server.bind((local_host, local_port)) # binds socket to specified local IP and port
	except Exception as e:
		print('problem on bind: %r' % e)

		print("[!!] Failed to listen on %s:%d" % (local_host, local_port))
		print("[!!] Check for other listening sockets or correct permissions.")
		sys.exit(0)

	print("[*] Listening on %s:%d" % (local_host, local_port))
	server.listen(5) # starts listening for incoming client connections with a backlog of 5
	while True: # infinite loop accepting incoming connections
		client_socket, addr=server.accept() # accepts a client connection and stores the socket and address 
		
		line="> Received incoming connection from %s:%d" % (addr[0], addr[1]) # print out the local connection information
		print(line)
		
		proxy_thread=threading.Thread( # start a thread to talk to the remote host, threading in case of multiple connections
			target=proxy_handler,
			args=(client_socket, remote_host,
			remote_port, receive_first))
		proxy_thread.start()

def main():
	if len(sys.argv[1:]) != 5: # verifies that exactly 5 cmd line arguments are provided
		print("Usage: ./proxy.py [localhost] [localport]", end='')
		print("[remotehost] [remoteport] [receive_first]")
		print("Example: ./proxy.py 127.0.0.1 9000 10.12.132.1 9000 True")
		sys.exit(0)
	# assignment of arguments to variables
	local_host=sys.argv[1]
	local_port=int(sys.argv[2])
	remote_host=sys.argv[3]
	remote_port=int(sys.argv[4])
	receive_first=sys.argv[5]
	if "True" in receive_first:
		receive_first=True
	else:
		receive_first=False

	server_loop(local_host, local_port,
		remote_host, remote_port, receive_first)

if __name__ == '__main__':
	main()
