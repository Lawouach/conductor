# -*- coding: utf-8 -*-
from carrot.messaging import Consumer
from conductor.task import Task

__all__ = ["ConsumerTask"]

class ConsumerTask(Task):
    def __init__(self, bus=None):
        Task.__init__(self, bus)

    def start(self):
        Task.start(self)
    start.priority = 12
    
    def stop(self):
        Task.start(self)
    stop.priority = 88
    
    def start_task(self):
        self.bus.log("Starting AMQP consumer provider task")
        self.bus.subscribe("get-amqp-consumer", self.get_consumer)
        
    def stop_task(self):
        self.bus.log("Stopping AMQP consumer provider task")
        self.bus.unsubscribe("get-amqp-consumer", self.get_consumer)
        
    def get_consumer(self, broker, **kwargs):
        return Consumer(broker, **kwargs)
