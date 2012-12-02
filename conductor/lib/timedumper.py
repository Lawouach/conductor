# -*- coding: utf-8 -*-
__docformat__ = "restructuredtext en"
import os.path
import copy

from conductor.task import Task
import timedump

try:
    import cPickle as pickle
except ImportError:
    import pickle

__all__ = ['TimedumpTask', 'PickleTimedumpTask']

class TimedumpTask(Task):
    def __init__(self, bus=None, pause_timedump=False, drop_storage=True):
        Task.__init__(self, bus)
        if pause_timedump:
            timedump.current.pause()

        self.drop_storage = drop_storage

    def _get_storage(self):
        return timedump.current.storage

    def _set_storage(self, storage):
        timedump.current.storage = storage
        timedump.current.clear()

    storage = property(_get_storage, _set_storage, doc="Gets and sets the current timedump storage")

    def start(self):
        Task.start(self)
    start.priority = 40

    def stop(self):
        Task.stop(self)
    stop.priority = 90

    def exit(self):
        Task.exit(self)
    exit.priority = 90

    def stop_task(self):
        from cherrypy.process import wspbus
        if self.bus.state == wspbus.states.EXITING:
            self.done()

    def done(self):
        if self.drop_storage:
            timedump.storage.drop()


class PickleTimedumpTask(TimedumpTask):
    def __init__(self, bus=None, pause_timedump=False, drop_storage=True):
        TimedumpTask.__init__(self, bus, pause_timedump, drop_storage)

        self.filename = None
        self.stream = None

    def __update_run(self, current, other):
        for k in other:
            if k not in current:
                current[k] = other[k]
            elif isinstance(current[k], dict) and isinstance(other[k], dict):
                self.__update_run(current[k], other[k])
            elif isinstance(current[k], list) and isinstance(other[k], list):
                for i in range(0, 4):
                    current[k][i].extend(other[k][i])

    def done(self):
        try:
            existing = None
            if self.filename:
                if os.path.exists(self.filename):
                    f = file(self.filename, 'rb')
                    try:
                        existing = pickle.load(f)
                    finally:
                        f.close()
                self.stream = file(self.filename, 'wb')

            if self.stream:
                current = timedump.current.aggregate(bypass_indices=False)
                if self.drop_storage:
                    timedump.current.clear()
                    timedump.current.storage.drop()
                if existing and isinstance(existing, dict):
                    current = copy.deepcopy(current)
                    existing = copy.deepcopy(existing)
                    self.__update_run(current, existing)

                pickle.dump(current, self.stream)
                if self.filename:
                    self.stream.close()
                    self.stream = None
        except:
            self._log("Couldn't pickle timedump", traceback=True)
