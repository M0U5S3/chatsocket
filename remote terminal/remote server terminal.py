import socket
import hashlib
from getpass import getpass

HOST = input("Host: (or input \"ls\" for load save) ")
PORT = 9091
ADDR = (HOST, PORT)
HEADER = 64

if HOST == "ls":
    with open("data/host.txt", "r") as f:
        HOST = f.read()
        print(HOST)
        ADDR = (HOST, PORT)
elif input("save host ip? y/n ") == "y":
    print("saving ip")
    with open("data/host.txt", "w") as f:
        f.write(HOST)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect(ADDR)

def psend(s, message):
    s.send(str(len(str(message))).encode('utf-8') + b" " * (HEADER - len(str(len(str(message))).encode('utf-8'))))
    s.send(message.encode('utf-8'))

password = hashlib.sha256(getpass("Administrator password: ").encode('utf-8')).hexdigest()
psend(s, password)

reply = s.recv(1024).decode('utf-8')

if reply == "INVALID":
    quit()

while True:
    command = input(">>>")
    if command == "quit":
        s.close()
        quit()
    elif command == "help":
        print('\n--==* COMMANDS *==--\n\n'
              'help | displays all commands and their usage\n'
              'quit | safely disconnects from the server and closes the window\n'
              'kill | safely save messages, disconnect clients and kill the server\n'
              'pswd | change the administrator password\n'
              'msg user {user.ip} | privately message a user\n'
              'msg room {room} | message a room\n'
              'msg all | message all users\n'
              'getrooms | returns a list of all rooms that are active\n'
              'getusers | returns a list of active user nicknames and their ip\n'
              'lookup {user.ip} | returns user ip, nickname, room, blacklist status etc\n'
              'blacklist | show blacklisted IPs\n'
              'ban {user.ip} | add user to the blacklist\n'
              'nickname | change your displayed nickname (defaulted to \'admin\')\n')
    elif command == "kill":
        psend(s, command)
        quit()
    elif command == "pswd":
        psend(s, command)

        oldpswd = hashlib.sha256(getpass("Old password: ").encode('utf-8')).hexdigest()
        psend(s, oldpswd)

        if s.recv(1024).decode("utf-8") == "INVALID":
            quit()

        newpswd = hashlib.sha256(getpass("New password: ").encode('utf-8')).hexdigest()
        psend(s, newpswd)
    else:
        print("Invalid syntax | type help for a list of commands")
