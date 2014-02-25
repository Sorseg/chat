from Queue import Queue
import asynchat
import asyncore
import json
import socket
import threading
import sys

TERMINATOR = '\n\n'


class Host(asyncore.dispatcher):
    def __init__(self, interface, port):
        asyncore.dispatcher.__init__(self)
        self.messages = Queue()
        self.users = {}
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((interface, port))
        self.listen(20)

    def handle_accept(self):
        sock, addr = self.accept()
        ServerHandler(self, sock)

    def close(self):
        asyncore.dispatcher.exit(self)
        raise asyncore.ExitNow


class ServerHandler(asynchat.async_chat):
    def __init__(self, host, connection):
        asynchat.async_chat.__init__(self, connection)
        self.login = None
        self.found_terminator = self._greet
        self.host = host
        self.data = []
        self.set_terminator(TERMINATOR)

    def _greet(self):
        login = json.loads(''.join(self.data)).get('login', None)
        self.data = []
        self.login = login
        if login is None:
            self.login_error()
        else:
            self.host.users[login] = self
            self.found_terminator = self._chat

    def collect_incoming_data(self, data):
        self.data.append(data)

    def _chat(self):
        try:
            msg = json.loads(''.join(self.data))
        except ValueError:
            self.invalid()

        msg['from'] = self.login
        msg_type = msg.get('type', None)
        if msg_type == 'message':
            self.host.messages.put(msg)
        elif msg_type is None:
            self.invalid()

    def send_message(self, msg):
        self.push(json.dumps(msg)+TERMINATOR)

    def login_error(self):
        msg = {'type': 'error'}
        if self.login is None:
            msg['cause'] = 'no login'
        else:
            msg['cause'] = 'invalid login'

        self.send_message(msg)

    def invalid(self):
        msg = {'type': 'error',
               'cause': 'invalid message'}

        self.send_message(msg)


class Client(asynchat.async_chat):
    def __init__(self, addr, port):
        self.messages = Queue()
        asynchat.async_chat.__init__(self)
        self.set_terminator(TERMINATOR)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.connect((addr, port))

    def send_message(self, msg):
        self.push(json.dumps(msg)+TERMINATOR)

    def login(self, login):
        self.send_message({'login': login})

