import socket
import hashlib
from getpass import getpass

HOST = input("Host: (or input \"ls\" for load save) ")
PORT = 9091
ADDR = (HOST, PORT)
HEADER = 64
TIMEOUT = 2

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
s.settimeout(TIMEOUT)
s.connect(ADDR)

def psend(s, message):
    s.send(str(len(str(message))).encode('utf-8') + b" " * (HEADER - len(str(len(str(message))).encode('utf-8'))))
    s.send(message.encode('utf-8'))

def precv(s):
    recvheader = int(s.recv(HEADER).decode('utf-8'))
    message = s.recv(recvheader).decode('utf-8')
    return message

def restart():
    global HOST
    global ADDR
    global s
    global password
    HOST = input("Host: (or input \"ls\" for load save) ")
    ADDR = (HOST, PORT)

    if HOST == "ls":
        with open("data/host.txt", "r") as f:
            HOST = f.read()
            print(HOST)
            ADDR = (HOST, PORT)
    elif input("save host ip? y/n ") == "y":
        print("saving ip")
        with open("data/host.txt", "w") as f:
            f.write(HOST)
    try:
        s.close()
    except:
        pass
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(TIMEOUT)
    s.connect(ADDR)
    password = hashlib.sha256(getpass("Administrator password: ").encode('utf-8')).hexdigest()
    psend(s, password)
    reply = s.recv(1024).decode('utf-8')

    if reply == "INVALID":
        print("Password not accepted")
        quit()

def refresh():
    try:
        global s
        s.close()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        s.connect(ADDR)
        psend(s, password)
        reply = s.recv(1024).decode('utf-8')
        if reply == "INVALID":
            print("Password not accepted")
            s.close()
            quit()
        elif reply == "VALID":
            print("operation successful")
    except ConnectionResetError:
        restart()

password = hashlib.sha256(getpass("Administrator password: ").encode('utf-8')).hexdigest()
psend(s, password)

reply = s.recv(1024).decode('utf-8')

if reply == "INVALID":
    print("Password not accepted")
    quit()

while True:
    try:
        command = input(">>> ")
        if command == "quit":
            s.close()
            quit()
        elif command == "help":
            print('\n--==* COMMANDS *==--\n\n'
                  'help | displays all commands and their usage\n'
                  'quit | safely disconnects from the server and closes the window\n'
                  'refresh | attempt to refresh terminal connection\n'
                  'lock | locks terminal\n'
                  'restart | restarts terminal\n'
                  'stat | server status\n'
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
                  'nickname | change your displayed nickname (defaulted to \'Administrator\')\n')
        elif command == "kill":
            psend(s, command)
            quit()
        elif command == "refresh":
            refresh()
        elif command == "lock":
            s.close()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(TIMEOUT)
            s.connect(ADDR)
            password = hashlib.sha256(getpass("Administrator password: ").encode('utf-8')).hexdigest()
            psend(s, password)
            reply = s.recv(1024).decode('utf-8')

            if reply == "INVALID":
                print("Password not accepted")
                quit()
        elif command == "restart":
            restart()
        elif command == "stat":
            psend(s, command)
            try:
                print(precv(s))
            except [TimeoutError, ConnectionResetError] as e:
                if e == ConnectionResetError:
                    print("OFFLINE")
                elif e == TimeoutError:
                    print("Server took too long to reply")
                option = input("Attempt refresh? y/n ")
                if option == "y":
                    refresh()
        elif command == "pswd":
            psend(s, command)

            oldpswd = hashlib.sha256(getpass("Old password: ").encode('utf-8')).hexdigest()
            psend(s, oldpswd)

            if s.recv(1024).decode("utf-8") == "INVALID":
                quit()

            newpswd = hashlib.sha256(getpass("New password: ").encode('utf-8')).hexdigest()
            psend(s, newpswd)
            password = newpswd
        elif command[:9] == "msg user ":
            psend(s, command)
            reply = precv(s)
            if reply == "INVALID":
                print("UserNotFoundError: user does not exist")
            if reply == "VALID":
                psend(s, input(f"[DM {command[9:].rstrip()}] "))

        elif command[:9] == "msg room ":
            psend(s, command)
            psend(s, input(f"[broadcast room \"{command[9:].rstrip()}\"] "))
        elif command == "msg all":
            psend(s, command)
            psend(s, input(f"[broadcast globally] "))
        elif command == "getrooms":
            psend(s, command)
            print(precv(s))
        else:
            print("Invalid syntax | type help for a list of commands")
    except ConnectionResetError:
        print("Connection reset | Attempting refresh")
        refresh()
