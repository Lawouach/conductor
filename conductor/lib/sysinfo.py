# -*- coding: utf-8 -*-
__docformat__ = "restructuredtext en"
import gc
import os
import time

try:
    import cPickle as pickle
except ImportError:
    import pickle

from conductor.task import Task

import psutil

__all__ = ['SysInfoTask', 'PickleSysInfoTask', 'ConsoleSysInfoTask']

class SysInfoTask(Task):
    def __init__(self, bus=None):
        Task.__init__(self, bus)
        self.monitoring_freq = 0
        import timedump
        self.dump = timedump.Timedump()

        self._last = 0
        self._p = psutil.Process(os.getpid())
        
    def _get_storage(self):
        return self.dump.storage

    def _set_storage(self, storage):
        self.dump.storage = storage
        self.dump.clear()

    storage = property(_get_storage, _set_storage, doc="Gets and sets the current timedump storage")

    def start_task(self):
        if self.monitoring_freq > 0:
            self.bus.subscribe('main', self.monitor_task)
        self.bus.subscribe('sysinfo', self._dump_sysinfo)
        self.bus.subscribe('getsysinfo', self._gather_sysinfo)

    def stop_task(self):
        self.bus.unsubscribe('sysinfo', self._dump_sysinfo)
        self.bus.unsubscribe('getsysinfo', self._gather_sysinfo)
        self.bus.unsubscribe('main', self.monitor_task)
        from cherrypy.process import wspbus
        if self.bus.state == wspbus.states.EXITING:
            self.dump.done()

    def monitor_task(self):
        now = int(time.time())
        if now - self._last >= self.monitoring_freq:
            self._last = now
            self._dump_sysinfo(complete=True, cpu_times=True, 
                               cpu_usage=True, memory_info=True, 
                               memory_usage=True, gc_count=False)

    def _gather_sysinfo(self, cpu_times=False, cpu_usage=True, 
                        memory_info=False, memory_usage=True, 
                        gc_count=False):
        info = {}
        if cpu_times:
            info['times'] = self._p.get_cpu_times()
        if cpu_usage:
            info['cpu_usage'] = self._p.get_cpu_percent()
        if memory_info:
            info['memory'] = self._p.get_memory_info()
        if memory_usage:
            info['memory_usage'] = self._p.get_memory_percent()
        if gc_count:
            info['gc_count'] = gc.get_count()

        return info

    def _dump_sysinfo(self, key=None, complete=False, cpu_times=False, 
                      cpu_usage=True, memory_info=False, memory_usage=True, 
                      gc_count=False):
        try:
            if not key: key = str(os.getpid())
            info = self._gather_sysinfo(cpu_times, cpu_usage, memory_info, memory_usage, gc_count)
            self.dump.tick(key, info)
            if complete:
                self.dump.done(key)
        except:
            self._log("Couldn't process sysinfo", traceback=True)

    def _get_last_snapshot(self, key=None):
        return self.dump.last(key)

class PickleSysInfoTask(SysInfoTask):
    def __init__(self, bus=None):
        SysInfoTask.__init__(self, bus)
        self.filename = None
        self.stream = None
    
    def stop_task(self):
        SysInfoTask.stop_task(self)
        from cherrypy.process import wspbus
        if self.bus.state == wspbus.states.EXITING:
            self._pickle_dump()

    def _pickle_dump(self):
        try:
            if self.filename:
                self.stream = file(self.filename, 'wb')

            if self.stream:
                current = self.dump.aggregate(bypass_indices=False)
                self.dump.clear()
                pickle.dump(current, self.stream)
                if self.filename:
                    self.stream.close()
                    self.stream = None
        except:
            self._log("Couldn't pickle sysinfo dump", traceback=True)


class ConsoleSysInfoTask(Task):
    def __init__(self, bus=None):
        Task.__init__(self, bus)
        self.monitoring_freq = 0

        self._last = 0
        self._p = psutil.Process(os.getpid())
        
    def start(self):
        Task.start(self)
    start.priority = 45

    def stop(self):
        Task.stop(self)
    stop.priority = 85

    def start_task(self):
        if self.monitoring_freq > 0:
            self.bus.subscribe('main', self.monitor_task)

    def stop_task(self):
        self.bus.unsubscribe('main', self.monitor_task)

    def monitor_task(self):
        now = int(time.time())
        if now - self._last >= self.monitoring_freq:
            self._last = now
            self._dump_sysinfo()

    def _dump_sysinfo(self):
        try:
            log = "PID: %d, User: %2f, System: %2f, %%CPU: %2f, RSS: %s KB, VMS: %s KB, %%MEM: %2f"
            cpu0, cpu1 = self._p.get_cpu_times()
            mem0, mem1 = self._p.get_memory_info()
            log = log % (os.getpid(), cpu0, cpu1, self._p.get_cpu_percent(),
                         mem0/ 1024, mem1/ 1024, self._p.get_memory_percent())
            self._log(log)
        except:
            self._log("Couldn't process sysinfo", traceback=True)
