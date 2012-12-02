# -*- coding: utf-8 -*-
from conductor.task import Task
from conductor.lib.system import kill_proc

__all__ = ['Supervisor']

class Supervisor(Task):
    def __init__(self, bus=None):
        Task.__init__(self, bus)
        self.supervised = []

    def supervise(self, proc):
        self.supervised.append(proc)

    def stop_task(self):
        self._kill_supervised()
        
    def _kill_supervised(self):
        for proc in self.supervised:
            self.bus.log("Killing %d" % proc.pid)
            if proc.is_alive():
                kill_proc(proc.pid)
                proc.join()
        self.supervised = []
