# -*- coding: utf-8 -*-
from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

__all__ = ['KeepSchedulerAlive']

class KeepSchedulerAlive(component):
    Inboxes = {"inbox"    : "UNUSED",
               "control"  : "stops the component"}
    
    Outboxes = {"outbox"  : "UNUSED",
                "signal"  : "Shutdown signal"}

    def __init__(self, bus):
        super(KeepSchedulerAlive, self).__init__()
        self.bus = bus

    def main(self):
        yield 1
        self.link((self, 'outbox'), (self, 'inbox'))
        self.send(None, "outbox")
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                if isinstance(mes, shutdownMicroprocess) or \
                       isinstance(mes, producerFinished):
                    self.send(shutdownMicroprocess(), "signal")
                    break

            if self.dataReady("inbox"):
                self.recv("inbox")
                self.bus.publish("main")
                self.send(None, "outbox")

            if not self.anyReady():
                self.pause()
  
            yield 1

        self.bus = None
