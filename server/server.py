import socket
import threading
import time
import pickle

host = socket.gethostbyname(socket.gethostname())
PORT = 9090
TERM_PORT = 9091
ADDR = (host, PORT)
TERM_ADDR = (host, TERM_PORT)
HEADER = 64

# \ = end of path, --_>> = send, --_<< = recv
PCOLS = {

    'NICK': {'ROOT': "/PCOL/NICK>>\\", 'DENY': "/PCOL/NICK>>/DENIED>>\\", 'VALIDATE': "/PCOL/NICK>>/VALID>>\\"},
    'ROOM_CODE': {'ROOT': "/PCOL/CODE>>\\"},
    'DISCONNECT': {'ROOT': "/PCOL/DCON>>\\"}

}

ROOT_PCOLS = [PCOLS[i]['ROOT'] for i in PCOLS.keys()]

ALL_PCOLS = []
for i in PCOLS.keys():
    for x in PCOLS[i].keys():
        ALL_PCOLS.append(PCOLS[i][x])

class User:
    def __init__(self, cs, address, nickname, room):
        self.cs = cs
        self.address = address
        self.ip = self.address[0]
        self.nickname = nickname
        self.room = str(room)
    def targeted_send(self, msg, target_user, save=True):
        if msg in ALL_PCOLS:
            msg = "​" + msg
        #length = str(len(str(msg))).encode('utf-8') + b" " * (HEADER - len(str(len(str(msg))).encode('utf-8')))
        length = str(len(str(msg))).rjust(HEADER, " ").encode('utf-8')  # works
        target_user.cs.send(length)
        target_user.cs.send(msg.encode('utf-8'))
        if save:
            messages.append((msg, self.room))

    def precv(self):
        recvheader = int(self.cs.recv(HEADER).decode('utf-8'))
        message = self.cs.recv(recvheader).decode('utf-8')
        return message

    def broadcast(self, message, roomonly=True, is_pcol=False):

        if roomonly:
            print(f"[RO_BROADCAST] " + message)
            for user in users:
                if user.room == self.room:
                    if message in ALL_PCOLS and not is_pcol:
                        if user == self:
                            self.targeted_send(f"Nice try {self.nickname}", user, save=False)
                            self.targeted_send(("​" + message), user)
                        else:
                            self.targeted_send(("​" + message), user)
                    elif not is_pcol:
                        self.targeted_send(message, user)
        else:
            print(f"[ALL_BROADCAST] " + message)
            for user in users:
                if message in ALL_PCOLS and not is_pcol:
                    self.targeted_send(("​" + message), user)
                elif not is_pcol:
                    self.targeted_send(message, user)

    def fetch(self):
        room_messages = []
        for msg in messages:
            if msg[1] == self.room:
                room_messages.append(msg[0])
        for msg in room_messages:
            self.targeted_send(msg, self, save=False)

def backup_chat():
    print("[BACK_UP] Backing up chat")
    with open('data/messages.txt', 'wb') as f:
        pickle.dump(messages, f)

def protocol(protocol, cs=None):

    def broadcast_pcol(pcol):
        for client in clients:
            length = str(len(str(pcol))).encode('utf-8') + b" " * (HEADER - len(str(len(str(pcol))).encode('utf-8')))
            client.send(length)
            client.send(pcol.encode("utf-8"))

    def send_pcol(pcol):
        length = str(len(str(pcol))).encode('utf-8') + b" " * (HEADER - len(str(len(str(pcol))).encode('utf-8')))
        cs.send(length)
        cs.send(pcol.encode("utf-8"))

    def recv_pcol():
        recvheader = int(cs.recv(HEADER).decode('utf-8'))
        message = cs.recv(recvheader).decode('utf-8')
        return message


    if protocol == 'REQ_NICKNAME':
        send_pcol(ROOT_PCOLS[0])
        nickname = recv_pcol().strip(" ").strip("\n")
        if len(nickname) > 10:
            send_pcol(PCOLS['NICK']['DENY'])
            cs.close()
            return False
        elif len(nickname) <= 10:
            send_pcol(PCOLS['NICK']['VALIDATE'])
            return nickname

    elif protocol == 'REQ_ROOM_CODE':
        send_pcol(ROOT_PCOLS[1])
        room_code = recv_pcol()
        return room_code

    elif protocol == 'DISCONNECT_CLIENTS':
        try:
            broadcast_pcol(ROOT_PCOLS[2])
        except ConnectionAbortedError:
            pass

def handle(user):
    time.sleep(1)
    user.fetch()
    user.broadcast(f"{user.nickname} joined the chat!")
    user.targeted_send(f"--== Connected to {host} | room code: \'{user.room}\' ==--", user, save=False)
    while True:
        try:
            message = user.precv().strip('\n ')
            message = f"[{user.nickname} @ {time.strftime('%H:%M', time.localtime())}] " + message
            if user.ip in blacklist:
                user.broadcast(f"{user.nickname} is banned", roomonly=False)
                raise Exception
            user.broadcast(message)
        except Exception:
            users.remove(user)
            user.cs.close()
            print(f"[DISCONNECTION] [{user.ip}: {user.nickname}] disconnected")
            user.broadcast(f"{user.nickname} left the chat!")
            break

def terminal_listen():
    global blacklist
    while True:
        try:
            client, address = term_s.accept()
            try:
                length = client.recv(HEADER).decode('utf-8')
                password = client.recv(int(length)).decode('utf-8')
            except ConnectionResetError:
                client.close()
                continue
            with open("data/terminalpass.txt", "r") as f:
                if password == f.read().rstrip('\n'):
                    length = str(len(str("VALID"))).rjust(HEADER, " ").encode('utf-8')  # works
                    client.send(length)
                    client.send("VALID".encode('utf-8'))
                    print(f"[CONNECTED] {address[0]} connected via an admin terminal")
                    admin = User(client, address, "Administrator", "1")

                    def precv():
                        return client.recv(int(client.recv(HEADER).decode('utf-8'))).decode('utf-8')

                    while True:
                        try:
                            command = precv()
                            if command == "kill":
                                backup_chat()
                                try:
                                    protocol('DISCONNECT_CLIENTS')
                                    print(f"[TERMINAL] {address[0]} safely disconnected all clients")
                                except UnboundLocalError:
                                    print(f"[TERMINAL] {address[0]} tried to disconnect clients but there are none")
                                print(f"[TERMINAL] {address[0]} killed server")
                                exit(0)
                            elif command == "pswd":
                                oldpassw = precv()
                                with open("data/terminalpass.txt", "r+") as f:
                                    if oldpassw == f.read().rstrip('\n'):
                                        client.send("VALID".encode('utf-8'))
                                        newpassw = precv()
                                        f.truncate(0)
                                        f.seek(0)
                                        f.write(newpassw)
                                        print(f"[TERMINAL] {address[0]} changed password to {newpassw}")
                                    else:
                                        client.send("INVALID".encode('utf-8'))
                            elif command == "stat":
                                admin.targeted_send("ONLINE", admin, save=False)
                            elif command[:9] == "msg user ":
                                userfound = False
                                for user in users:
                                    if user.ip == command[9:]:
                                        target = user
                                        userfound = True
                                        break
                                if userfound:
                                    admin.targeted_send("VALID", admin, save=False)
                                    password = precv()
                                    admin.targeted_send(f"[{admin.nickname}(ADMIN)(DM) @ {time.strftime('%H:%M', time.localtime())}] " + password, target)
                                else:
                                    admin.targeted_send("INVALID", admin, save=False)

                            elif command[:9] == "msg room ":
                                admin.room = command[9:]
                                msg = precv()
                                admin.broadcast(f"[{admin.nickname}(ADMIN) @ {time.strftime('%H:%M', time.localtime())}] " + msg)
                            elif command == "msg all":
                                msg = precv()
                                admin.broadcast(f"[{admin.nickname}(ADMIN)(GLOBAL) @ {time.strftime('%H:%M', time.localtime())}] " + msg, roomonly=False)
                            elif command == "getrooms":
                                rooms = ""
                                for user in users:
                                    rooms += f' "{user.room}",'
                                if rooms != "":
                                    admin.targeted_send(rooms[1:-1], admin, save=False)
                                else:
                                    admin.targeted_send("No active rooms", admin, save=False)
                            elif command == "getusers":
                                userstring = ""
                                for user in users:
                                    userstring += f" ({user.ip}, {user.nickname}),"
                                if rooms != "":
                                    admin.targeted_send(userstring[1:-1], admin, save=False)
                                else:
                                    admin.targeted_send("No active users", admin, save=False)
                            elif command[:7] == "lookup ":
                                found = False
                                for user in users:
                                    if user.ip == command[7:]:
                                        found = True
                                        break
                                if found:
                                    admin.targeted_send(f"IP = '{user.ip}', Nickname = '{user.nickname}', Room = '{user.room}'", admin, save=False)
                                else:
                                    admin.targeted_send("User is non-existent or is offline", admin, save=False)
                            elif command[:4] == "ban ":
                                with open('data/blacklist.txt', 'wb') as f:
                                    blacklist.append(command[4:])
                                    pickle.dump(blacklist, f)
                            elif command[:6] == "unban ":
                                with open('data/blacklist.txt', 'wb') as f:
                                    blacklist = [value for value in blacklist if value != command[6:]]
                                    pickle.dump(blacklist, f)
                            elif command == "blacklist":
                                with open('data/blacklist.txt', 'rb') as f:
                                    admin.targeted_send(str(pickle.load(f)), admin, save=False)
                            elif command[:9] == "nickname ":
                                admin.nickname = command[9:]

                        except Exception as e:
                            client.close()
                            print("[ERROR] server terminal error")
                            print(e)
                            break
                else:
                    length = str(len(str("INVALID"))).rjust(HEADER, " ").encode('utf-8')  # works
                    client.send(length)
                    client.send("INVALID".encode('utf-8'))

        except Exception as e:
            print("[ERROR] server terminal error")
            print(e)
            try:
                admin.cs.close()
            except UnboundLocalError:
                pass

def accept():
    try:
        while True:
            client, address = server.accept()
            if address[0] in blacklist:
                client.close()
                print(f"[CONNECTION] Access denied {address[0]}")
                continue
            clients.append(client)
            print(f"[CONNECTION] {address[0]} connected.")

            try:
                nickname = protocol('REQ_NICKNAME', cs=client)
                if not nickname:
                    continue
                room_code = protocol('REQ_ROOM_CODE', cs=client)

            except ConnectionResetError:
                client.close()
                continue

            user = User(client, address, nickname, room_code)
            users.append(user)

            print(f"[ACTION_NICKNAME] {user.ip} set nickname to {user.nickname}.")

            thread = threading.Thread(target=handle, args=(user,))
            thread.start()
    except Exception as e:
        print("[ERROR] server error")
        backup_chat()
        try:
            protocol('DISCONNECT_CLIENTS')
        except UnboundLocalError:
            pass
        raise e

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
server.listen()
print(f"[STARTING] Listening on {host}, port {PORT}")
print(f"[STARTING] Listening on {host}, port {TERM_PORT}")

term_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
term_s.bind(TERM_ADDR)
term_s.listen(1)

users = []
clients = []

try:
    print("[BACK_UP] Retrieving chat backups")
    with open('data/messages.txt', 'rb') as f:
        messages = pickle.load(f)
except EOFError:
    messages = []

try:
    print("[BACK_UP] retrieving blacklist")
    with open('data/blacklist.txt', 'rb') as f:
        blacklist = pickle.load(f)
except EOFError:
    blacklist = []

print("[STARTING] Server starting...")
thread = threading.Thread(target=terminal_listen)
thread.start()
accept()
