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
        self.client.login('user')
        asyncore_loop()

    def tearDown(self):
        try:
            self.client.close()
            self.host.close()
            asyncore_loop()
        except asyncore.ExitNow:
            pass

    def test_login(self):
        self.assertIn('user', self.host.users.keys())

    def test_client_to_server(self):
        self.client.send_message({'type': 'msg', 'text': 'TEST'})
        asyncore_loop()
        self.assertEqual('TEST', self.host.messages[-1]['text'])

    def test_server_to_client(self):
        self.host.send_message({'type': 'msg', 'text': 'HELLO'})
        asyncore_loop()
        self.assertEqual('HELLO', self.client.messages[-1]['text'])

    def test_malformed_to_server(self):
        self.client.send_message({'tpe': 'msg', 'text': 'TEST'})
        asyncore_loop()
        self.assertEqual('error', self.client.messages[-1]['type'])

    def test_malformed_to_client(self):
        self.host.send_message({'te': 'msg', 'text': 'HELLO'})
        asyncore_loop()
        self.assertEqual('error', self.host.messages[-1]['type'])

class TestMultiUser(unittest.TestCase):
    def setUp(self):
        self.host = network.Host('', PORT)
        self.client1 = network.Client('127.0.0.1', PORT)
        self.client1.login('user')
        self.client2 = network.Client('127.0.0.1', PORT)
        self.client2.login('user')
        asyncore_loop()

    def tearDown(self):
        try:
            self.host.close()
            self.client1.close()
            self.client2.close()
            asyncore_loop()
        except asyncore.ExitNow:
            pass

    def test_two_users(self):
        self.assertIn('user1', self.host.users.keys())



