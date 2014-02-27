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
        self.logger = logging.getLogger('host')

    def handle_accept(self):
        self.logger.info("Accepting connection...")
        pair = self.accept()
        if pair is None:
            self.logger.info("Unsuccessful")
            return
        sock, addr = pair

        self.logger.info("Connection accepted:"+str(addr))
        ServerHandler(self, sock)

    def __del__(self):
        self.close()

    def send_message(self, msg):
        self.logger.info('brdcst:'+repr(msg))
        for conn in self.users.values():
            conn.send_message(msg)

    def msg(self, msg):
        self.send_message({'type': 'msg', 'text': msg})


class ChatHandler(asynchat.async_chat):

    def __init__(self, connection=None):
        self.logger = logging.getLogger('?')
        self.data = []
        self.set_terminator(TERMINATOR)
        self.login = ''
        asynchat.async_chat.__init__(self, connection)

    def collect_incoming_data(self, data):
        self.data.append(data)

    def send_message(self, msg):
        self.push(json.dumps(msg)+TERMINATOR)

    def invalid(self):
        msg = {'type': 'msgerr',
               'cause': 'invalid'}

        self.send_message(msg)

    def found_terminator(self):
        try:
            msg = json.loads(''.join(self.data))
        except ValueError:
            self.logger.warn('Invalid message:'+repr(''.join(self.data)))
            self.invalid()
            return None
        finally:
            self.data = []
        msg_type = msg.get('type', None)
        self.logger.info("<-:"+"({}):".format(self.login)+repr(msg))
        if msg_type not in self.MESSAGETYPES:
            self.invalid()
            return None
        doer = getattr(self, 'do_'+msg_type, None)
        skip = False
        if doer and doer(msg) == 'skip':
            skip = True
        if not skip:
            self.messages.append(msg)

    def push(self, msg):
        self.logger.info('->:'+str(msg.strip()))
        asynchat.async_chat.push(self, msg)

    def quit(self):
        self.close()


class ServerHandler(ChatHandler):
    i = 1
    MESSAGETYPES = ['msg', 'msgerr', 'error', 'login']

    def __init__(self, host, connection):
        ChatHandler.__init__(self, connection)
        self.logger = logging.getLogger('srv'+str(self.i))
        ServerHandler.i += 1
        self.host = host
        self.messages = host.messages
        self.users = host.users

    def do_login(self, msg):
        login = msg.get('login', '')
        login = str(login).strip()
        self.logger.info("Login:"+repr(login))
        if any((not login, '\n' in login, len(login) > 30)):
            self.login_error()
        else:
            self.login = login
            i = 1
            while self.login in self.users:
                self.login = login + str(i)
                i += 1

            self.loginok()
            self.users[self.login] = self
        self.logger.debug("host users:"+str(self.users))

    def login_error(self):
        self.send_message({'type': 'loginerr', 'cause': 'badlogin'})

    def loginok(self):
        self.send_message({'type': 'loginok', 'login': self.login})
        self.send_message({'type': 'userlist', 'users': self.users.keys()})
        self.host.send_message({'type': 'login', 'user': self.login})

    def do_msg(self, msg):
        if not self.login:
            self.nologin()
        text = msg.get('text', '').lstrip('\n').rstrip()
        if not text:
            self.logger.debug("skipping "+repr(msg))
            return 'skip'
        msg['text'] = text
        msg['from'] = self.login
        self.host.send_message(msg)

    def nologin(self):
        self.send_message({'type': 'msgerr', 'cause': 'nologin'})

    def do_msgerr(self, msg):
        msg['from'] = self.login
        self.messages.append(msg)

    def quit(self):
        ChatHandler.quit(self)
        self.host.send_message({'type': 'logout', 'user': self.login})
        self.users.pop(self.login, None)

    handle_close = quit


class Client(ChatHandler):
    MESSAGETYPES = ['msg', 'msgerr', 'error', 'login', 'logout', 'loginok', 'loginerr', 'userlist']
    i = 1

    def __init__(self, addr, port):
        self.users = []
        self.messages = []
        ChatHandler.__init__(self)
        self.logger = logging.getLogger('clnt'+str(self.i))
        Client.i += 1
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.connect((addr, port))

    def perform_login(self, login):
        self.send_message({'login': login, 'type': 'login'})

    def msg(self, msg):
        self.send_message({'type': 'msg', 'text': msg})

    def do_loginok(self, msg):
        self.login = msg['login']

    def do_userlist(self, msg):
        self.users = msg['users']

    def do_logout(self, msg):
        u = msg['user']
        if u in self.users:
            self.users.remove(u)
