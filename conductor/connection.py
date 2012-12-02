# -*- coding: utf-8 -*-
import socket
import threading
import time
from multiprocessing.connection import Listener, Client

__all__ = ['ProcListener', 'ProcClient']

class ProcListener(threading.Thread):
    def __init__(self, addr, authkey):
        threading.Thread.__init__(self)
        self.running = False
        self.connections = []
        self.bus = None
        self.addr = addr
        self.authkey = authkey
        self.listener = Listener(addr, authkey=authkey)

        self.setDaemon(True)

    def run(self):
        self.bus.log("Listening for incoming connections")
        self.running = True
        while self.running:
            conn = self.listener.accept()
            self.connections.append(conn)

    def stop(self):
        if not self.running:
            return

        self.bus.log("Stopping listener")
        self.running = False
        for conn in self.connections:
            if conn:
                conn.close()

        # if the listener is blocked in the accept() call
        # it will lock the thread, so by connecting to it
        # we unblock it
        c = Client(self.addr, authkey=self.authkey)
        c.close()
            
        self.connections = []
        self.listener.close()

    def recv(self):
        return self.listener.recv()

class ProcClient(threading.Thread):
    def __init__(self, addr, authkey):
        threading.Thread.__init__(self)
        self.bus = None
        self.addr = addr
        self.authkey = authkey
        self.conn = None
        self.running = False

        self.setDaemon(True)

    def run(self):
        self.conn = None
        for i in range(0, 3):
            self.bus.log("Starting process client connection to: %s:%d" % self.addr)
            try:
                self.conn = Client(self.addr, authkey=self.authkey)
                break
            except:
                self.bus.log("", traceback=True)
                time.sleep(10.0)

        if not self.conn:
            self.bus.log("Failed to connect to %s:%d" % self.addr)
            return

        self.running = True
        while self.running:
            try:
                if self.conn.poll(1.0):
                    print self.conn.recv()
            except IOError:
                self.stop()
                break
                
    def stop(self):
        if not self.running:
            return

        self.bus.log("Stopping process client connection")
        if self.conn:
            self.running = False
            self.conn.close()
            self.conn = None

    def send(self, data):
        self.conn.send(data)

    def recv(self):
        return self.conn.recv()
