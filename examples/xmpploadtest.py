# -*- coding: utf-8 -*-
import os, os.path
from glob import iglob

from conductor.lib.logger import open_logger
from conductor.process import AsyncoreProcess
from conductor.protocol.xmpp import XMPPProcessTask

from headstock.lib.cot import Cot

class LoadTestTask(XMPPProcessTask):
    def __init__(self, bus=None, cots=None):
        XMPPProcessTask.__init__(self, bus)
        self.cots = cots
        
    def add_extensions(self):
        self.client.register(Cot(self.bus, self.cots))
    
def run():
    p = AsyncoreProcess()
    p.interval = 0.002
    p.logger = open_logger(stdout=True)

    ids = range(0, 1)
    for i in ids:
        cots = iglob(os.path.join(os.curdir, 'cots', '*.cot'))
        t = LoadTestTask(cots=cots)
        t.settings.username = "test%d" % i
        t.settings.password = "test"
        t.settings.domain = "localhost"
        t.settings.resource = "conductor"
        t.settings.hostname = "localhost"
        t.settings.log_stdout = True
        t.settings.register = True
        t.settings.unregister = True
        p.register_task(t)
    
    p.run ()

if __name__ == '__main__':
    run()
