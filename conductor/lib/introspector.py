# -*- coding: utf-8 -*-
__docformat__ = "restructuredtext en"

from conductor.task import Task

__all__ = ['IntrospectorTask']

class IntrospectorTask(Task):
    def __init__(self, bus=None):
        Task.__init__(self, bus)
        self.p = None
        self.visualiser_addr = None

    def start_task(self):
        from Axon.Introspector import Introspector
        from Kamaelia.Chassis.Pipeline import Pipeline
        from Kamaelia.Internet.TCPClient import TCPClient

        self.p = Pipeline(Introspector(),
                          TCPClient(*self.visualiser_addr))
        self.p.activate()

    def stop_task(self):
        from Axon.Ipc import shutdownMicroprocess
        from Kamaelia.Util.OneShot import OneShot

        o = OneShot(msg=shutdownMicroprocess())
        o.link((o, 'outbox'), (self.p, 'control'))
        o.activate()

