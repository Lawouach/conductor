# -*- coding: utf-8 -*-
from carrot.messaging import Publisher
from conductor.task import Task

__all__ = ["PublisherTask"]

class PublisherTask(Task):
    def __init__(self, bus=None):
        Task.__init__(self, bus)

    def start_task(self):
        self.bus.log("Starting AMQP publisher provider task")
        self.bus.subscribe("get-amqp-publisher", self.get_publisher)
    start_task.priority = 11
        
    def stop_task(self):
        self.bus.log("Stopping AMQP publisher provider task")
        self.bus.unsubscribe("get-amqp-publisher", self.get_publisher)
        
    def get_publisher(self, broker, **kwargs):
        return Publisher(broker, **kwargs)
    stop_task.priority = 89
