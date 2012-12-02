# -*- coding: utf-8 -*-
import tornado
import tornado.httpserver
import tornado.web

from conductor.task import Task
from conductor.protocol.http import WebApplicationTask

__all__ = ['TornadoServerTask", "TornadoApplicationTask']

class TornadoServerTask(Task):
    def __init__(self, bus=None):
        Task.__init__(self, bus)
        app = tornado.web.Application([])
        self.server = tornado.httpserver.HTTPServer(app)
        self.port = 8888

    def start(self):
        Task.start(self)
    start.priority = 25
    
    def stop(self):
        Task.stop(self)
    stop.priority = 85
    
    def start_task(self):
        self.bus.log("Starting the Tornado HTTP server")
        self.bus.subscribe('get-http-server', self.get_server)
        self.server.listen(self.port)

    def stop_task(self):
        self.bus.log("Stopping the Tornado HTTP server")
        self.bus.unsubscribe('get-http-server', self.get_server)

    def get_server(self):
        return self.server

class TornadoApplicationTask(WebApplicationTask):
    def __init__(self, bus=None):
        WebApplicationTask.__init__(self, bus)

    def start_task(self):
        self.server = self.bus.publish('get-http-server').pop()
        WebApplicationTask.start_task(self)
        
    def stop_task(self):
        WebApplicationTask.stop_task(self)
        self.server = None
        
    def mount(self, pattern, handler, host=""):
        self.server.request_callback.add_handlers(host, [(pattern, handler)])
        self.bus.log("Mounted Tornado web handler at '%s'" % (pattern or '/',))
        self.bus.publish("mounted-webapp", handler)

    def unmount(self, pattern):
        self.bus.log("Unmounted Tornado web handler from '%s'" % (pattern or '/',))
        self.bus.publish("unmounted-webapp", pattern)
        
    def unmount_all(self):
        if self.server:
            self.bus.log("Unmounting all web handlers")
            for (pattern, handler) in self.server.request_callback.handlers:
                self.bus.publish("unmounted-webapp", handler)
            self.server.request_callback.handlers = []

if __name__ == '__main__':
    import tornado.web
    from conductor.process import TornadoProcess
    from conductor.task import Task
    from conductor.lib.logger import open_logger
    from conductor.protocol.http.webtornado import TornadoServerTask, \
         TornadoApplicationTask
    
    p = TornadoProcess()
    p.logger = open_logger(stdout=True, logger_name="main")

    s = TornadoServerTask()
    p.register_task(s)

    a = TornadoApplicationTask()
    p.register_task(a)

    class MainHandler(tornado.web.RequestHandler):
        def get(self):
            self.write("Hello, world")

    class DemoTask(Task):
        def start_task(self):
            self.bus.publish("mount-webapp", r"/",  MainHandler)

    p.register_task(DemoTask())

    p.run()
