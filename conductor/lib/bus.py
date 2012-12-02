# -*- coding: utf-8 -*-
import atexit
import os
import sys
import threading
from multiprocessing import Condition
from cherrypy.process.wspbus import Bus, states

from conductor.task import Task

__all__ = ['SynchronizingBus', 'SynchronizedBus',
           'SubBusTask', 'NoAtexitBus']

class SynchronizingBus(Bus):
    def __init__(self, sync_delay=1):
        Bus.__init__(self)
        self.sync_delay = sync_delay
        self.condition = Condition()

    def start(self):
        import time
        time.sleep(self.sync_delay)
        self.log("Releasing children")
        self.condition.acquire()
        self.condition.notify_all()
        self.condition.release()
        Bus.start(self)

class SynchronizedBus(Bus):
    def __init__(self, cond):
        Bus.__init__(self)
        self.condition = cond
        
    def start(self):
        self.log("Syncing on main process")
        self.condition.acquire()
        self.condition.wait()
        self.condition.release()
        Bus.start(self)

class NoAtexitBus(Bus):
    def start(self):
        Bus.start(self)

        handler = (self._clean_exit, (), {})
        if handler in atexit._exithandlers:
            atexit._exithandlers.remove(handler)

class SubBusTask(Task):
    def __init__(self, bus=None):
        Task.__init__(self, bus)
        self.tasked_bus = NoAtexitBus()

    def start_task(self):
        self.tasked_bus.log = self._log
        self.tasked_bus.start()

    def stop_task(self):
        #def null_log(msg, level=0, traceback=False): pass
        #self.tasked_bus.log = null_log
        if self.tasked_bus.state in (states.STARTING, states.STARTED):
            self.tasked_bus.publish('stop')
            self.tasked_bus.stop()
        elif self.tasked_bus.state == states.STOPPED:
            self.tasked_bus.publish('exit')
            self.tasked_bus.exit()

    def register_sub_task(self, task):
        self._log('Registering %s sub-task: %s' % (self.__class__, task.__class__))
        task.bus = self.tasked_bus
        task.subscribe()

    def unregister_sub_task(self, task):
        self._log('Unregistering %s sub-task: %s' % (self.__class__, task.__class__))
        task.unsubscribe()
        task.bus = None

if __name__ == '__main__':
    import os
    import random
    
    from conductor.process import SynchronizingProcess, SynchronizedProcess
    from conductor.task import Task
    from conductor.lib.logger import open_logger

    p = SynchronizingProcess()
    p.logger = open_logger(stdout=True, logger_name="main")
    
    class WillSendExitEventually(Task):
        def start_task(self):
            self.bus.subscribe("main", self.loop)
            
        def stop_task(self):
            self.bus.unsubscribe("main", self.loop)
            
        def loop(self):
            if random.randint(0, 100) > 95:
                self.bus.exit()
            else:
                self.bus.log("wait for it !")

    class DummyTask(Task):
        def __init__(self, bus=None, index=0):
            Task.__init__(self, bus)
            self.index = index
            
        def start_task(self):
            self.bus.log("STARTING INDEX: %s PID: %s" % (self.index, os.getpid()))

        def stop_task(self):
            self.bus.log("STOPPING INDEX: %s PID: %s" % (self.index, os.getpid()))

    for i in range(0, 3):
       c = SynchronizedProcess(condition=p.bus.condition)
       c.notatexit()
       c.logger = open_logger(stdout=True, logger_name="%d" % i)
       c.register_task(WillSendExitEventually())
       c.register_task(DummyTask(index=i))
       c.start()

    p.run()
