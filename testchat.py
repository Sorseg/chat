import asyncore
import logging
import unittest
import sys
import network

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

def asyncore_loop():
    asyncore.loop(0, count=10)

class TestNetwork(unittest.TestCase):
    PORT = 4469

    def setUp(self):
        self.host = network.Host('', self.PORT)
        self.client = network.Client('127.0.0.1', self.PORT)

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
        self.skipTest("not implemented")

    def test_malformed_to_client(self):
        self.skipTest("not implemented")

