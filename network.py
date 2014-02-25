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


class ChatHandler(asynchat.async_chat):

    def __init__(self, connection = None):
        self.data = []
        self.set_terminator(TERMINATOR)
        asynchat.async_chat.__init__(self, connection)


    def collect_incoming_data(self, data):
        logging.debug("Data incoming:"+repr(data))
        self.data.append(data)

    def send_message(self, msg):
        self.push(json.dumps(msg)+TERMINATOR)

    def invalid(self):
        msg = {'type': 'error',
               'cause': 'invalid message'}

        self.send_message(msg)

    def found_terminator(self):
        try:
            msg = json.loads(''.join(self.data))
        except ValueError:
            logging.warn('Wrong message:'+repr(msg))
            self.invalid()
            return None
        finally:
            self.data = []
        msg_type = msg.get('type', None)
        if msg_type not in self.MESSAGETYPES:
            self.invalid()
            return None
        getattr(self, 'do_'+msg_type)(msg)
        return msg


class ServerHandler(ChatHandler):
    MESSAGETYPES = ['msg', 'error', 'login']

    def __init__(self, host, connection):
        ChatHandler.__init__(self, connection)
        self.login = None
        self.host = host

    def do_login(self, msg):
        login = msg.get('login', None)
        self.login = login
        logging.info("Login:"+repr(login))
        if login is None:
            self.login_error()
        else:
            self.host.users[login] = self
        logging.debug("host users:"+str(self.host.users))

    def found_terminator(self):
        msg = ChatHandler.found_terminator(self)
        if not msg:
            return
        logging.info("Message from: "+self.login+": "+repr(msg))

    def send_message(self, msg):
        self.push(json.dumps(msg)+TERMINATOR)

    def login_error(self):
        msg = {'type': 'error'}
        if self.login is None:
            msg['cause'] = 'no login'
        else:
            msg['cause'] = 'invalid login'

        self.send_message(msg)

    def do_msg(self, msg):
        self.host.messages.append(msg)

    do_error = do_msg


class Client(ChatHandler):
    MESSAGETYPES=['msg', 'error', 'login', 'logout']

    def __init__(self, addr, port):
        self.users = []
        self.messages = []
        ChatHandler.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.connect((addr, port))

    def login(self, login):
        self.send_message({'login': login, 'type': 'login'})

    def do_msg(self, msg):
        self.messages.append(msg)

    do_error = do_msg

