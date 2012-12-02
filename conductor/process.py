# -*- coding: utf-8 -*-
__docformat__ = "restructuredtext en"
import os
import sys
import logging

try:
    from multiprocessing import Process as _Process
    from multiprocessing import active_children
except ImportError:
    def activate_children():
        return []
    
    class _Process(object):
        @property
        def pid(self):
            return os.getpid()

__all__ = ['Process', 'AxonProcess', 'CherryPyProcess',
           'TornadoProcess', 'AsyncoreProcess']

class Process(_Process):
    """
    Represents a process that can run tasks.
    """
    def __init__(self):
        _Process.__init__(self)
        self.logger = None
        self.daemon = False
        self.interval = 0.1

        from cherrypy.process.wspbus import Bus
        self.bus = Bus()
        self.bus.subscribe('log', self.log)

    def notatexit(self):
        """
        Prevents the process's bus to trap atexit.
        """
        import atexit
        handler = (self.bus._clean_exit, (), {})
        if handler in atexit._exithandlers:
            atexit._exithandlers.remove(handler)

    def register_task(self, task):
        """
        Subscribes `task` with `self.bus`.
        """
        self.log('Registering task: %s' % task.__class__)
        task.proc = self
        task.bus = self.bus
        task.subscribe()

    def unregister_task(self, task):
        """
        Unsubscribes `task` from the bus so that it isn't run
        whenever the bus starts or stops.
        """
        self.log('Unregistering task: %s' % task.__class__)
        task.proc = None
        task.unsubscribe()
        task.bus = None

    def run(self):
        """
        Start the bus and blocks on the bus.
        """
        self.log("Process PID: %d" % (self.pid or os.getpid(),))

        from cherrypy.process import plugins
        sig = plugins.SignalHandler(self.bus)
        if sys.platform[:4] == 'java':
            # See http://bugs.jython.org/issue1313
            sig.handlers['SIGINT'] = self._jython_handle_SIGINT
        sig.subscribe()

        if self.daemon:
            plugins.Daemonizer(self.bus).subscribe()

        self.bus.start()
        self.bus.block(interval=self.interval)

    def log(self, msg, level=logging.INFO):
        if self.logger:
            self.logger.log(level, msg)

    def _jython_handle_SIGINT(self, signum=None, frame=None):
        # See http://bugs.jython.org/issue1313
        self.bus.log('Keyboard Interrupt: shutting down bus')
        self.bus.exit()

class SynchronizingProcess(Process):
    def __init__(self):
        Process.__init__(self)
        from conductor.lib.bus import SynchronizingBus
        self.bus = SynchronizingBus()
        self.bus.subscribe('log', self.log)
        self.bus.subscribe('main', self.check_children)
        
    def check_children(self):
        if not active_children():
            self.bus.log("No more children still running, let's exit the main process")
            self.bus.unsubscribe('main', self.check_children)
            self.bus.exit()
            
class SynchronizedProcess(Process):
    def __init__(self, condition):
        Process.__init__(self)
        from conductor.lib.bus import SynchronizedBus
        self.bus = SynchronizedBus(cond=condition)
        self.bus.subscribe('log', self.log)
            
class AsyncoreProcess(Process):
    """
    Represents a process that can run asyncore tasks.
    
    The blocking model is based on the asyncore loop.
    """
    def __init__(self):
        Process.__init__(self)
        self.timeout = 30.0
        self.interval = 0.02

        import select
        if hasattr(select, "poll"):
            from asyncore import poll2
            self.poll = poll2
        else:
            from asyncore import poll
            self.poll = poll
        
    def run(self):
        """
        Start the bus and blocks on the Axon scheduler.
        """
        self.log("AsyncoreProcess PID: %d" % (self.pid or os.getpid(),))

        self.bus.subscribe('main', self.loop_once)
        
        from cherrypy.process import plugins
        sig = plugins.SignalHandler(self.bus)
        if sys.platform[:4] == 'java':
            # See http://bugs.jython.org/issue1313
            sig.handlers['SIGINT'] = self._jython_handle_SIGINT
        sig.subscribe()
        self.bus.start()
        self.bus.block(interval=self.interval)

    def loop_once(self):
        self.poll(self.timeout)
            
class AxonProcess(Process):
    """
    Represents a process that can run Axon/Kamaelia tasks.
    
    The blocking model is based on the Axon.
    """
    def __init__(self):
        Process.__init__(self)
        self.interval = 0.02

    def run(self):
        """
        Start the bus and blocks on the Axon scheduler.
        """
        self.log("AxonProcess PID: %d" % (self.pid or os.getpid(),))

        from conductor.lib.keepalive import KeepSchedulerAlive
        self.keepalive = KeepSchedulerAlive(bus=self.bus)
        self.keepalive.activate()

        from cherrypy.process import plugins
        sig = plugins.SignalHandler(self.bus)
        if sys.platform[:4] == 'java':
            # See http://bugs.jython.org/issue1313
            sig.handlers['SIGINT'] = self._jython_handle_SIGINT
        sig.subscribe()
        self.bus.start()

        try:
            from Axon.Scheduler import scheduler 
            scheduler.run.runThreads(slowmo = self.interval)
        except KeyboardInterrupt:
            pass
        self.bus.exit()

class TornadoProcess(Process):
    """
    Represents a process that can run Tornado tasks.
    
    The blocking model is based on the Tornado's ioloop.
    """
    def __init__(self):
        Process.__init__(self)

    def run(self):
        """
        Start the bus and blocks on the Axon scheduler.
        """
        self.log("TornadoProcess PID: %d" % (self.pid or os.getpid(),))

        from cherrypy.process import plugins
        sig = plugins.SignalHandler(self.bus)
        if sys.platform[:4] == 'java':
            # See http://bugs.jython.org/issue1313
            sig.handlers['SIGINT'] = self._jython_handle_SIGINT
        sig.subscribe()

        self.bus.start()

        try:
            from tornado import ioloop
            self.ioloop = ioloop.IOLoop.instance()
            self.ioloop.add_callback(self.publish_main)
            self.ioloop.start()
        except KeyboardInterrupt:
            pass

        ioloop.IOLoop.instance().stop()
        self.bus.exit()

    def publish_main(self):
        self.bus.publish("main")
        self.ioloop.add_callback(self.publish_main)

class CherryPyProcess(Process):
    """
    Represents a process that can run CherryPy tasks.
    
    The blocking model is based on the CherryPy engine.
    """
    def __init__(self):
        Process.__init__(self)
        self.config = None

        import cherrypy
        self.bus = cherrypy.engine
        
        if sys.platform[:4] == 'java':
            import socket
            socket.IPPROTO_TCP = 6
            
            # see http://www.cherrypy.org/ticket/944
            import threading
            from cherrypy.process.plugins import ThreadManager
            class PatchedThreadManager(ThreadManager):
                def acquire_thread(self):
                    thread_ident = threading.local()
                    if thread_ident not in self.threads:
                        # We can't just use _get_ident as the thread ID
                        # because some platforms reuse thread ID's.
                        i = len(self.threads) + 1
                        self.threads[thread_ident] = i
                        self.bus.publish('start_thread', i)

            cherrypy.engine.thread_manager.unsubscribe()
            cherrypy.engine.thread_manager = PatchedThreadManager(cherrypy.engine)
            cherrypy.engine.thread_manager.subscribe()


            # See http://bugs.jython.org/issue1417
            import cherrypy.lib.reprconf
            class PatchedParser(cherrypy.lib.reprconf.Parser):
                def as_dict(self, raw=False, vars=None):
                    """Convert an INI file to a dictionary"""
                    # Load INI file into a dict
                    result = {}
                    for section in self.sections():
                        if section not in result:
                            result[section] = {}
                        for option in self.options(section):
                            value = self.get(section, option, raw, vars)
                            try:
                                value = unrepr(value)
                            except Exception, x:
                                try:
                                    value = eval(value)
                                except Exception, x:
                                    msg = ("Config error in section: %r, option: %r, "
                                           "value: %r. Config values must be valid Python." %
                                           (section, option, value))
                                    raise ValueError(msg, x.__class__.__name__, x.args)
                            result[section][option] = value
                    return result
            cherrypy.lib.reprconf.Parser = PatchedParser

        if hasattr(cherrypy.engine, "signal_handler"):
            if sys.platform[:4] == 'java':
                # The JVM seems to not allow this signal to be overriden
                del cherrypy.engine.signal_handler.handlers['SIGUSR1']

                # See http://bugs.jython.org/issue1313
                cherrypy.engine.signal_handler.handlers['SIGINT'] = self._jython_handle_SIGINT

            cherrypy.engine.signal_handler.subscribe()
        
        if hasattr(cherrypy.engine, "console_control_handler"):
            cherrypy.engine.console_control_handler.subscribe()

        cherrypy.config.update({'engine.autoreload_on': False,
                                'checker.on': False,
                                'log.screen': False,
                                'tools.log_headers.on': False,
                                'request.show_tracebacks': False,
                                'request.show_mismatched_params': False})

        if sys.platform[:4] == 'java':
            cherrypy.config.update({'server.nodelay': False})

    def update_config(self, conf):
        import cherrypy
        cherrypy.config.update(conf)
          
    def run(self):
        """
        Start the cherrypy.engine and blocks on it
        """
        import cherrypy
        if self.config:
            cherrypy.config.update(self.config)

        cherrypy.log("CherryPyProcess PID: %d" % (self.pid or os.getpid(),))
        cherrypy.engine.start()
        cherrypy.engine.block()

    def log(self, msg, level=logging.INFO):
        self.bus.log(msg, level=level)
