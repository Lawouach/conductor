# -*- coding: utf-8 -*-
import cherrypy
from cherrypy import _cpconfig

from conductor.task import Task
from conductor.protocol.http import WebApplicationTask

__all__ = ['CherryPyProcessTask', 'CherryPyWSGITask']

class CherryPyProcessTask(WebApplicationTask):
    def __init__(self, bus=None, conf=None):
        WebApplicationTask.__init__(self, bus)
        self.conf = conf or {}

    def mount(self, script_name, app, conf=None):
        webapp = None
        try:
            _conf = self.conf.copy()
            _cpconfig.merge(_conf, self.conf)   
            webapp = cherrypy.tree.mount(app, script_name, _conf)
            self.bus.log("Mounted web application '%s' at '%s'" % (app.__class__, script_name or '/'))
        except:
            cherrypy.log("Failed mounting '%s' at '%s'" % (app.__class__, script_name or '/'),
                         traceback=True)
        else:
            if webapp:
                self.bus.publish("mounted-webapp", webapp)

    def unmount(self, script_name):
        webapp = None
        try:
            webapp = cherrypy.tree.apps[script_name]
            del cherrypy.tree.apps[script_name]
        except KeyError:
            pass
        else:
            if webapp:
                self.bus.log("Unmounted web application from '%s'" % (script_name or '/',))
                self.bus.publish("unmounted-webapp", webapp)
        
    def unmount_all(self):
        self.bus.log("Unmounting all web applications")
        for webapp in cherrypy.tree.apps.values():
            self.bus.publish("unmounted-webapp", webapp)
        cherrypy.tree.apps.clear()

class CherryPyWSGITask(WebApplicationTask):
    def mount(self, script_name, app, conf=None):
        webapp = None
        try:
            cherrypy.tree.graft(app, script_name)
            self.bus.log("Mounted WSGI application '%s' at '%s'" % (app.__class__, script_name or '/'))
        except:
            cherrypy.log("Failed mounting '%s' at '%s'" % (app.__class__, script_name or '/'),
                         traceback=True)
        else:
            self.bus.publish("mounted-webapp", app)

    def unmount(self, script_name):
        webapp = None
        try:
            webapp = cherrypy.tree.apps[script_name]
            del cherrypy.tree.apps[script_name]
        except KeyError:
            pass
        else:
            if webapp:
                self.bus.log("Unmounted WSGI application from '%s'" % (script_name or '/',))
                self.bus.publish("unmounted-webapp", webapp)
        
    def unmount_all(self):
        self.bus.log("Unmounting all web applications")
        for webapp in cherrypy.tree.apps.values():
            self.bus.publish("unmounted-webapp", webapp)
        cherrypy.tree.apps.clear()

if __name__ == '__main__':
    import cherrypy
    from conductor.process import CherryPyProcess
    from conductor.task import Task
    from conductor.protocol.http.webcherrypy import CherryPyProcessTask
    
    p = CherryPyProcess()
    p.config = {'log.screen': True}

    a = CherryPyProcessTask()
    p.register_task(a)

    class Demo(object):
        @cherrypy.expose
        def index(self):
            return "Hello, World"

    class DemoTask(Task):
        def start_task(self):
            self.bus.publish("mount-webapp", "/",  Demo())

    p.register_task(DemoTask())

    p.run()
