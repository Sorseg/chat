from Queue import Queue
import asynchat
import asyncore
import json
import socket
import logging

TERMINATOR = '\n\n'


class Host(asyncore.dispatcher):
    def __init__(self, interface, port):
        asyncore.dispatcher.__init__(self)
        self.messages = []
        self.users = {}
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((interface, port))
        self.listen(20)

    def handle_accept(self):
        logging.info("Accepting connection...")
        pair = self.accept()
        if pair is None:
            logging.info("Unsuccesfull")
            return
        sock, addr = pair

        logging.info("Connection accepted:"+str(addr))
        ServerHandler(self, sock)

    def close(self):
        asyncore.dispatcher.close(self)
        raise asyncore.ExitNow

    def __del__(self):
        self.close()

    def send_message(self, msg):
        for conn in self.users.values():
            conn.send_message(msg)


class ServerHandler(asynchat.async_chat):
    def __init__(self, host, connection):
        logging.info("Created handler")
        asynchat.async_chat.__init__(self, connection)
        self.login = None
        self.found_terminator = self._greet
        self.host = host
        self.data = []
        self.set_terminator(TERMINATOR)

    def _greet(self):
        logging.info("Greeting received")
        login = json.loads(''.join(self.data)).get('login', None)
        self.data = []
        self.login = login
        logging.info("Login:"+repr(login))
        if login is None:
            self.login_error()
        else:
            self.host.users[login] = self
            self.found_terminator = self._chat
        logging.info("host users:"+str(self.host.users))

    def collect_incoming_data(self, data):
        logging.debug("Data incoming:"+repr(data))
        self.data.append(data)

    def _chat(self):
        try:
            msg = json.loads(''.join(self.data))
        except ValueError:
            self.invalid()
            return
        finally:
            self.data = []
        logging.info("Chat message from: "+self.login+": "+repr(msg))

        msg['from'] = self.login
        msg_type = msg.get('type', None)
        if msg_type == 'msg':
            self.host.messages.append(msg)
        else:
            logging.warn("Missing or wrong message type")
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

    def __del__(self):
        self.close()


class Client(asynchat.async_chat):
    def __init__(self, addr, port):
        asynchat.async_chat.__init__(self)
        self.messages = []
        self.data = []
        self.set_terminator(TERMINATOR)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.connect((addr, port))

    def collect_incoming_data(self, data):
        self.data.append(data)

    def send_message(self, msg):
        self.push(json.dumps(msg)+TERMINATOR)

    def found_terminator(self):
        try:
            msg = json.loads(''.join(self.data))
            self.messages.append(msg)
        except ValueError:
            #self.invalid()
            pass

    def login(self, login):
        self.send_message({'login': login})

