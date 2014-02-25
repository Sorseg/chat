import asyncore
import threading
import unittest
import time
import network


class TestNetwork(unittest.TestCase):
    PORT = 4466
    def setUp(self):
        self.host = network.Host('', self.PORT)
        self.client = network.Client('', self.PORT)
        self.client.login('user')
        time.sleep(0.1)
        threading.Thread(target=network.asyncore.loop).start()

    def tearDown(self):
        self.client.close()
        try:
            self.host.close()
        except asyncore.ExitNow:
            pass

    def test_login(self):
        self.assertIn('user', self.host.users)

    def test_send(self):
        self.client.send_message({'type': 'msg', 'text': 'TEST'})
        self.assertEqual('TEST', self.host.messages.get_nowait()['text'])
        self.host.send_message({'type': 'msg', 'text': 'HELLO'})
        self.assertEqual('HELLO', self.client.messages.get_nowait()['text'])
