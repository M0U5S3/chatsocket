import socket
import hashlib
from getpass import getpass

HEADER = 64
TIMEOUT = 2
PORT = 9091


def psend(message):
    global s
    s.send(str(len(str(message))).encode('utf-8') + b" " * (HEADER - len(str(len(str(message))).encode('utf-8'))))
    s.send(message.encode('utf-8'))


def precv():
    global s
    recvheader = int(s.recv(HEADER).decode('utf-8'))
    message = s.recv(recvheader).decode('utf-8')
    return message


def restart():
    global host
    global ADDR
    global s
    global password
    while True:
        host = input("Host: (or input \"ls\" for load save) ")
        ADDR = (host, PORT)

        if host == "ls":
            with open("data/host.txt", "r") as f:
                host = f.read()
                print(host)
                ADDR = (host, PORT)
        elif input("save host ip? y/n ") == "y":
            print("saving ip")
            with open("data/host.txt", "w") as f:
                f.write(host)
        try:
            s.close()
        except:
            pass
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        try:
            s.connect(ADDR)
            break
        except TimeoutError:
            print("Server is offline or doesn't exist")
    password = hashlib.sha256(getpass("Administrator password: ").encode('utf-8')).hexdigest()
    psend(password)
    reply = precv()

    if reply == "INVALID":
        print("Password not accepted")
        quit()

while True:
    try:
        restart()

        def refresh():
            try:
                global s
                s.close()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(TIMEOUT)
                s.connect(ADDR)

                psend(password)
                reply = precv()
                if reply == "INVALID":
                    print("Password not accepted")
                    s.close()
                    quit()
                elif reply == "VALID":
                    print("refresh successful")
            except ConnectionResetError:
                restart()
            except TimeoutError:
                restart()

        while True:
            global host
            global ADDR
            global s
            command = input(">>> ")
            if command == "quit":
                s.close()
                quit()
            elif command == "help":
                print('\n--==* COMMANDS *==--\n\n'
                      'help | displays all commands and their usage\n'
                      'quit | safely disconnects from the server and closes the window\n'
                      'host | prints the host\n'
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
                      'lookup {user.ip} | returns user ip, nickname, room etc\n'
                      'blacklist | show blacklisted IPs\n'
                      'ban {user.ip} | add user to the blacklist\n'
                      'unban {user.ip} | remove user from the blacklist\n'
                      'nickname | change your displayed nickname (defaulted to \'Administrator\')\n'
                      'close | close all connections and prevent new ones apart from whitelisted IPs\n'
                      'open | allow new connections\n'
                      'disconnect all | disconnect all connected clients\n'
                      'disconnect user {user.ip} | disconnect user\n'
                      'clear | clear backed up messages\n'
                      'backup | backup messages'
                      )
            elif command == "kill":
                psend(command)
                quit()
            elif command == "host":
                print(host)
            elif command == "refresh":
                refresh()
            elif command == "lock":
                s.close()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(TIMEOUT)
                s.connect(ADDR)
                password = hashlib.sha256(getpass("Administrator password: ").encode('utf-8')).hexdigest()
                psend(password)
                reply = precv()

                if reply == "INVALID":
                    print("Password not accepted")
                    quit()
            elif command == "restart":
                restart()
            elif command == "stat":
                try:
                    psend(command)
                    print(precv())
                except ConnectionResetError:
                    print("OFFLINE")
                    option = input("Attempt refresh? y/n ")
                    if option == "y":
                        refresh()
                except TimeoutError:
                    print("Server took too long to reply")
                    option = input("Attempt refresh? y/n ")
                    if option == "y":
                        refresh()
                except ConnectionAbortedError:
                    print("OFFLINE")
                    option = input("Attempt refresh? y/n ")
                    if option == "y":
                        refresh()
            elif command == "pswd":
                psend(command)

                oldpswd = hashlib.sha256(getpass("Old password: ").encode('utf-8')).hexdigest()
                psend(oldpswd)

                if s.recv(1024).decode("utf-8") == "INVALID":
                    quit()

                newpswd = hashlib.sha256(getpass("New password: ").encode('utf-8')).hexdigest()
                psend(newpswd)
                password = newpswd
            elif command[:9] == "msg user ":
                psend(command)
                reply = precv()
                if reply == "INVALID":
                    print("UserNotFoundError: user does not exist")
                if reply == "VALID":
                    psend(input(f"[DM {command[9:].rstrip()}] "))

            elif command[:9] == "msg room ":
                psend(command)
                psend(input(f"[broadcast room \"{command[9:].rstrip()}\"] "))
            elif command == "msg all":
                psend(command)
                psend(input(f"[broadcast globally] "))
            elif command == "getrooms":
                psend(command)
                print(precv())
            elif command == "getusers":
                psend(command)
                print(precv())
            elif command[:7] == "lookup ":
                psend(command)
                print(precv())
            elif command[:4] == "ban ":
                psend(command)
                print("operation successful")
            elif command[:6] == "unban ":
                psend(command)
                print("operation successful")
            elif command == "blacklist":
                psend(command)
                print(precv())
            else:
                print("Invalid syntax | type help for a list of commands")
    except ConnectionResetError:
        print("Connection reset | Attempting refresh")
        try:
            refresh()
        except NameError:
            print("Refresh failed")
            try:
                continue
            except Exception as e:
                raise e
    except ConnectionAbortedError:
        print("Connection aborted | Attempting refresh")
        try:
            refresh()
        except NameError:
            print("Refresh failed")
            try:
                continue
            except Exception as e:
                raise e
