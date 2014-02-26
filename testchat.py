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


logging.basicConfig(level=logging.INFO, stream=sys.stdout)

PORT = 4469


def asyncore_loop():
    asyncore.loop(0, count=200)


class TestNetwork(unittest.TestCase):

    def setUp(self):
        self.host = network.Host('', PORT)
        self.client = network.Client('127.0.0.1', PORT)

    def tearDown(self):
        asyncore.close_all()

    def test_nologin(self):
        self.client.msg('TEST')
        asyncore_loop()
        self.assertEqual({'type': 'msgerr', 'cause': 'nologin'},
                         self.client.messages[-1],
                         self.client.messages[-1])

    def test_login(self):
        self.client.perform_login('user')
        asyncore_loop()
        self.assertIn({'type': 'loginok', 'login': 'user'}, self.client.messages)

        self.assertIn('user', self.host.users.keys())

    def test_loginerror(self):
        self.client.send_message({'type': 'login', 'login': ''})
        asyncore_loop()
        self.assertEqual({'type': 'loginerr', 'cause': 'badlogin'},
                         self.client.messages[-1],
                         self.client.messages[-1])

    def test_trim(self):
        self.client.perform_login('user')
        self.client.msg('\n\n  TEST  \n\n')
        asyncore_loop()
        self.assertEqual({'type': 'msg', 'text': '  TEST', 'from': 'user'},
                         self.client.messages[-1],
                         self.client.messages[-1])

    def test_client_to_server(self):
        self.client.perform_login('user')
        self.client.msg('TEST')
        asyncore_loop()
        self.assertEqual({'type': 'msg', 'text': 'TEST', 'from': 'user'},
                         self.host.messages[-1],
                         self.host.messages[-1])

    def test_server_to_client(self):
        self.client.perform_login('user')
        asyncore_loop()
        self.host.msg('HELLO')
        asyncore_loop()
        self.assertEqual({'type': 'msg', 'text': 'HELLO'},
                         self.client.messages[-1],
                         self.client.messages[-1])

    def test_malformed_to_server(self):
        self.client.perform_login('user')
        self.client.send_message({'tpe': 'msg', 'text': 'TEST'})
        asyncore_loop()
        self.assertEqual({'type': 'msgerr', 'cause': 'invalid'},
                         self.client.messages[-1],
                         self.client.messages[-1])

    def test_malformed_to_client(self):
        self.client.perform_login('user')
        asyncore_loop()
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
        asyncore.close_all()

    def test_same_login(self):
        self.client1.perform_login('user')
        asyncore_loop()
        self.client2.perform_login('user')
        asyncore_loop()
        self.assertIn({'type': 'loginok', 'login': 'user1'}, self.client2.messages)
        self.assertIn('user1', self.host.users.keys())

    def test_login_different_users(self):
        self.client1.perform_login('user1')
        asyncore_loop()
        self.client2.perform_login('user2')
        asyncore_loop()
        self.assertEqual('user2', self.client1.messages[-1]['user'])

    def test_userlist(self):
        self.client1.perform_login('user1')
        asyncore_loop()
        self.client2.perform_login('user2')
        asyncore_loop()
        self.assertIn('user1', self.client2.users)

    def test_logoff(self):
        self.client1.perform_login('user1')
        asyncore_loop()
        self.client2.perform_login('user2')
        asyncore_loop()
        self.client1.quit()
        asyncore_loop()

        self.assertNotIn('user1', self.client2.users)