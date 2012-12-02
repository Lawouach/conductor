# -*- coding: utf-8 -*-
from conductor.task import Task

__all__ = ['WebApplicationTask']

class WebApplicationTask(Task):
    def __init__(self, bus=None):
        Task.__init__(self, bus)

    def start(self):
        Task.start(self)
    start.priority = 30
    
    def stop(self):
        Task.stop(self)
    stop.priority = 80
    
    def start_task(self):
        self.bus.log("Starting web application manager")

        self.bus.subscribe('mount-webapp', self.mount)
        self.bus.subscribe('unmount-webapp', self.unmount)
        self.bus.subscribe('unmount-all-webapps', self.unmount_all)
        
    def stop_task(self):
        self.bus.log("Stopping web application manager")

        self.bus.unsubscribe('mount-webapp', self.mount)
        self.bus.unsubscribe('unmount-webapp', self.unmount)
        self.bus.unsubscribe('unmount-all-webapps', self.unmount_all)

        self.unmount_all()
        
    def mount(self, script_name, app, conf=None):
        raise NotImplemented()

    def unmount(self, script_name):
        raise NotImplemented()
        
    def unmount_all(self):
        raise NotImplemented()
