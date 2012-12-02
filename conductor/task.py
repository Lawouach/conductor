# -*- coding: utf-8 -*-
import os
from cherrypy.process import plugins

__all__ = ['Task']

class Task(plugins.SimplePlugin):
    def __init__(self, bus=None):
        plugins.SimplePlugin.__init__(self, bus)
        self.proc = None
    
    def subscribe(self):
        self._log('Subscribing %s' % self.__class__)
        plugins.SimplePlugin.subscribe(self)
        self.bus.subscribe("start", self.start_task)
        self.bus.subscribe("stop", self.stop_task)
        self.bus.subscribe("reset", self.reset_task)

    def unsubscribe(self):
        self._log('Unsubscribing %s' % self.__class__)
        plugins.SimplePlugin.unsubscribe(self)
        self.bus.unsubscribe("start", self.start_task)
        self.bus.unsubscribe("stop", self.stop_task)
        self.bus.unsubscribe("reset", self.reset_task)

    def start(self):
        self._log("Starting task: %s" % repr(self.__class__))

    def stop(self):
        self._log("Stopping task: %s" % repr(self.__class__))
        
    def _log(self, msg, level=20, traceback=False):
        if self.bus:
            self.bus.log(msg, level=level, traceback=traceback)

    # Override those methods in your subclass
    def start_task(self):
        pass

    def stop_task(self):
        pass

    def reset_task(self):
        pass
