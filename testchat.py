"""
->
{"type":"msg", "text":"test"}
<-
{"type":"msgerr", "cause":"(nologin|exception)"}
->
{"type":"login", "login":"user"}
<-
{"type":"loginok", "login":"user1"}
{"type":"loginerr", "cause":"(exception|full|banned|...)"}
{"type":"userlist", "users":["user","user2","user3"]}
{"type":"login", "user":"user4"}
{"type":"logoff", "user":"user2"}
->
{"type":"msg", "text":"\n\n\n   Hello World\n\n\n"}
<-
{"type":"msg", "from":"user1", "text":"   Hello World"}
{"type":"msg", "from":"user4", "text":"Hello, user1"}
{"type":"quit", "cause":"(exception|full|kicked|serverquit|...)"}
"""

import asyncore
import logging
import unittest
import sys

import network


logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

PORT = 4469


def asyncore_loop():
    asyncore.loop(0, count=20)


class TestNetwork(unittest.TestCase):

    def setUp(self):
        self.host = network.Host('', PORT)
        self.client = network.Client('127.0.0.1', PORT)

    def tearDown(self):
        try:
            self.client.close()
            self.host.close()
            asyncore_loop()
        except asyncore.ExitNow:
            pass

    def test_nologin(self):
        self.client.msg('TEST')
        asyncore_loop()
        self.assertEqual({'type': 'msgerr', 'cause': 'nologin'},
                         self.client.messages[-1],
                         self.client.messages[-1])

    def test_login(self):
        self.client.login('user')
        asyncore_loop()
        self.assertEqual({'type': 'loginok', 'login': 'user'},
                         self.client.messages[-1],
                         self.client.messages[-1],)

        self.assertIn('user', self.host.users.keys())

    def test_loginerror(self):
        self.client.send_message({'type': 'login', 'login': 0})
        asyncore_loop()
        self.assertEqual({'type': 'loginerr', 'cause': 'badlogin'},
                         self.client.messages[-1],
                         self.client.messages[-1])

    def test_trim(self):
        self.client.login('user')
        self.client.msg('\n\n  TEST  \n\n')
        asyncore_loop()
        self.assertEqual({'type': 'msg', 'text': '  TEST'},
                         self.client.messages[-1],
                         self.client.messages[-1])

    def test_client_to_server(self):
        self.client.login('user')
        self.client.msg('TEST')
        asyncore_loop()
        self.assertEqual({'type': 'msg', 'text': 'TEST'},
                         self.host.messages[-1],
                         self.host.messages[-1])

    def test_server_to_client(self):
        self.client.login('user')
        self.host.msg('HELLO')
        asyncore_loop()
        self.assertEqual({'type': 'msg', 'text': 'HELLO'},
                         self.client.messages[-1],
                         self.client.messages[-1])

    def test_malformed_to_server(self):
        self.client.login('user')
        self.client.send_message({'tpe': 'msg', 'text': 'TEST'})
        asyncore_loop()
        self.assertEqual({'type': 'msgerr', 'cause': 'invalid'},
                         self.client.messages[-1],
                         self.client.messages[-1])

    def test_malformed_to_client(self):
        self.client.login('user')
        self.host.send_message({'tepy': 'msg', 'text': 'HELLO'})
        asyncore_loop()
        self.assertEqual({'type': 'msgerr', 'cause': 'invalid', 'from': 'user'},
                         self.host.messages[-1],
                         self.host.messages[-1])


class TestMultiUser(unittest.TestCase):
    def setUp(self):
        self.host = network.Host('', PORT)
        self.client1 = network.Client('127.0.0.1', PORT)
        self.client2 = network.Client('127.0.0.1', PORT)
        asyncore_loop()

    def tearDown(self):
        try:
            self.client1.close()
            self.client2.close()
            self.host.close()
            asyncore_loop()
        except asyncore.ExitNow:
            pass

    def test_same_login(self):
        self.client1.login('user')
        self.client2.login('user')
        asyncore_loop()
        self.assertEqual({'type': 'loginok', 'login': 'user1'},
                         self.client2.messages[-1],
                         self.client2.messages[-1])

        self.assertIn('user1', self.host.users.keys())

    def test_login_different_users(self):
        self.client1.login('user1')
        self.client2.login('user2')
        self.assertEqual('user2', self.client1.messages[-1]['login'])



