import asynchat


class Host(asynchat.async_chat):
    def __init__(self, interface, port):
        self.interface = interface
        self.port = port

    def collect_incoming_data(self, data):
        print data
