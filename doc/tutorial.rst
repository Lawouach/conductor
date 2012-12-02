========
Overview
========

conductor aims at providing simple processus communication 
and management through a simple API and a clean management of signals.

The idea behind conductor is to provide a basic code structure to
manage the life cycle of your processus. Usually application have the following
basic steps:

* initialization
* main loop
* cleanup
* shutdown

conductor tries to provide an interface to manage each of those steps cleanly
so that, for instance, if you send a SIGINT (typically via a Ctrl-C) signa conductor
will catch it and performs a clean shutdown, allowing the application to cleanup
properly.

In addition conductor offers a bus for your application to
communicate internally in an unobtrusive way as we will see later on.

You might consider conductor if you want common processus management to be taken
cared of without too much impact on your own application.

A quick introduction
====================

Let's imagine we have the following application:

.. code-block :: python 

   import time

   class MyApp(object):
        def __init__(self):
            self.running = False
        
    	def run(self):
            self.running = True
            while self.running:
 	        self.do_something()
                time.sleep(3)

    	def do_something(self):
            print "hello"

    	def stop(self):
            self.running = False
	    print "stopped cleanly"

   if __name__ == '__main__':
      app = MyApp()
      try:
          app.run()
      except KeyboardInterrupt:
          app.stop()

Obviously this isn't really much of an application but 
it shows a rather common pattern:

* application creation
* application main loop
* when a KeyboardInterrupt exception is trapped, the application is stopped

This is all very nice but what happens when the application receives
a different signal like a SIGHUP? In such case, the ``stop`` method of the
application isn't called.

Let's integrate conductor to your application:

.. code-block :: python 

   import time
   from conductor.task import Task

   class MyApp(object):
       def do_something(self):
           print "hello"

   class MyAppTask(Task):
       def __init__(self, bus=None):
           Task.__init__(self, bus)
           self.app = MyApp()

       def start_task(self):
           self.bus.subscribe("main", self.process_app)
           self.next = time.time() + 3

       def stop_task(self):
           print "stopped cleanly"
           self.bus.unsubscribe("main", self.process_app)

       def process_app(self):
           if time.time() >= self.next:
               self.app.do_something()
               self.next = time.time() + 3

   if __name__ == '__main__':
       from conductor.process import Process

       p = Process()
       t = MyAppTask()
       p.register_task(t)
       p.run()

Well the code isn't exactly smaller of course and you had
to create more objects that you had in the first place but now
your code will behave more properly when receiving signals.

Setting up the process
**********************

Let's break it down by making our way up.

.. code-block :: python 

   if __name__ == '__main__':
       from conductor.process import Process

       p = Process()
       t = MyAppTask()
       p.register_task(t)
       p.run()

conductor offers several classes that represent a 
process type. By type conductor actually refers to
the kind of main loop your application is interested in. 
For instance, a Tornado, asyncore or Kamaelia based main loops.

The default process type is based on the CherryPy main loop.

Registering tasks as process units
**********************************

Once you have created a process instance, you register tasks to it.
Each task is a unit managed by the process. This unit can be and
do anything that your application requires, it's merely an envelop
to ensure the proper behavior within the process itself.

Defining your task means subclassing the ``conductor.task.Task`` class
and defining some specific methods, namely:

 * start_task
 * stop_task
 * reset_task

None of those are compulsory but the first two are probably the minimum
if you want your task to achieve anything within the process.

Our task here uses the ``start_task`` method to subscribe the
``process_app`` method with the bus main channel. The bus is managed
by the process the task is registered with.

Each time the main loop performs a cycle, the bus publishes to the
main channel and each subscriber is notified. In our case, meaning
the ``process_app`` method is called.

And that is all. We have transformed our dull application into
a still dull application but that behaves gently with its environment.

.. note:: 
   **Tasks are not application** but are only there to provide entry points
   to manage your application from a process point of view. Therefore, the 
   application logic should not be part of the task itself.


Running your tasks in a subprocess
**********************************

The ``conductor.process.Process`` class is a subclass of
``multiprocessing.Process`` and therefore allows your to fire up
your process as a forked process of the main one.

To do so, you only need to change the last line to:

.. code-block :: python 

   p.start()

You can check that you indeed have two running processes. 

Supervising your child process
******************************

If you choose to use that fetaure you might be interested in supervising
the child process so that it stops when the parent does.

.. code-block :: python 

   if __name__ == '__main__':
       from conductor.process import Process
       from conductor.supervisor import Supervisor

       p = Process()
       s = Supervisor()
       p.register_task(s)
    
       c = Process()
       s.supervise(c)
       t = MyAppTask()
       c.register_task(t)
       c.start()

       p.run()

Here we create two ``conductor.process.Process`` instances. The 
first one handles the main process and the second one handles the
child process. By supervising it you make sure it will be
killed properly when the parent does.

Logging
*******

conductor allows your process to be associated to a logger interface,
usually one using the ``logging`` standard module.

.. code-block :: python 

   if __name__ == '__main__':
       from conductor.process import Process
       from conductor.supervisor import Supervisor
       from conductor.lib.logger import open_logger

       p = Process()
       p.logger = open_logger(stdout=True, logger_name="main")
       s = Supervisor()
       p.register_task(s)
    
       c = Process()
       c.logger = open_logger(stdout=True, logger_name="child")
       s.supervise(c)
       t = MyAppTask()
       c.register_task(t)
       c.start()

       p.run()

Here we log both processes with distinct logger instances.
The ``conductor.lib.open_logger`` function takes several
parameters that permi to create console and file logger handlers.

Getting process system information
**********************************

You might be interested in getting process information of one of your
process, conductor offers a task that will log CPU and memory info.

.. note:: 

   This tasks requires the `psutil <http://code.google.com/p/psutil/>`_ module to be availalble in
   the python path.

.. code-block :: python 

   if __name__ == '__main__':
       from conductor.process import Process
       from conductor.supervisor import Supervisor
       from conductor.lib.logger import open_logger
       from conductor.lib.sysinfo import ConsoleSysInfoTask

       p = Process()
       p.logger = open_logger(stdout=True, logger_name="main")
       s = Supervisor()
       p.register_task(s)
    
       c = Process()
       c.logger = open_logger(stdout=True, logger_name="child")
       s.supervise(c)

       i = ConsoleSysInfoTask()
       i.monitoring_freq = 3

       t = MyAppTask()
       c.register_task(t)

       c.start()

       p.run()

This task will log every three seconds info about CPU and memory usage.
