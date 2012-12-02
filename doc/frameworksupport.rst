==========================
Various frameworks support
==========================

If your application is based on various frameworks such 
as `Kamaelia <http://www.kamaelia.org/Home>`_, 
`asyncore <http://docs.python.org/library/asyncore.html#module-asyncore>`_
or `Tornado <http://www.tornadoweb.org/>`_, you still may
find conductor useful as it comes with specific
process implementations for each of them.

Asyncore integration
====================

Let's imagine you wish to integrate conductor with an application
using the asyncore framework. This means being able
to run the asyncore loop.

For instance, let's imagine you want to poll for a feed using HTTP,
you would have a similar piece of code:

.. code-block :: python 

    import time
    import socket
    import asyncore
    from urllib2 import urlparse
    from conductor.task import Task

    class FeedPoller(asyncore.dispatcher):
        def __init__(self, url):
            asyncore.dispatcher.__init__(self)
            p = urlparse.urlparse(url)

            self.path = p.path
            self.host = p.netloc.split(':')[0]
            self.port = p.port or 80

            self.feed = None

        def handle_close(self):
            self.close()

        def handle_read(self):
            self.feed = self.recv(8192)

        def writable(self):
            return (len(self.buffer) > 0)

        def handle_write(self):
            sent = self.send(self.buffer)
            self.buffer = self.buffer[sent:]

        def poll(self):
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect((self.host, self.port))
            self.buffer = 'GET %s HTTP/1.0\r\nHost: %s\r\n\r\n' % (self.path, self.host)

    class FeedPollerTask(Task):
        def __init__(self, url, bus=None):
            Task.__init__(self, bus)
            self.poller = FeedPoller(url)
            self.poll_freq = 3

        def start_task(self):
            self.bus.subscribe("main", self.poll_feed)
            self.next = time.time() + self.poll_freq

        def stop_task(self):
            self.bus.unsubscribe("main", self.poll_feed)

        def poll_feed(self):
            if time.time() >= self.next:
                self.poller.poll()
                self.next = time.time() + self.poll_freq
        poll_feed.priority = 70

    if __name__ == '__main__':
        from conductor.process import AsyncoreProcess
        from conductor.lib.logger import open_logger
        from conductor.lib.sysinfo import ConsoleSysInfoTask

        p = AsyncoreProcess()
        p.logger = open_logger(stdout=True, logger_name="main")

        i = ConsoleSysInfoTask()
        i.monitoring_freq = 3
        p.register_task(i)

        t = FeedPollerTask(url="http://www.reddit.com/r/Python/.rss")
        p.register_task(t)

        p.run()


As you can see, this example uses a different process class, namely 
``conductor.process.AsyncoreProcess``.


Tornado integration
===================

conductor lets you integrate with the Tornado main loop so that
you can run either its HTTP server or simply use its nifty 
event dispatching. 

For instance, let's imagine you want to poll for a feed using HTTP,
you would have a similar piece of code:

.. code-block :: python 

    import time
    import socket
    from urllib2 import urlparse
    from tornado import iostream
    from conductor.task import Task

    class FeedPoller(object):
        def __init__(self, url):
            p = urlparse.urlparse(url)

            self.path = p.path
            self.host = p.netloc.split(':')[0]
            self.port = p.port or 80

            self.feed = None

        def connect(self):
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            self.sock.connect((self.host, self.port))
            self.stream = iostream.IOStream(self.sock)

        def on_headers(self, data):
            headers = {}
            for line in data.split("\r\n"):
                parts = line.split(":")
                if len(parts) == 2:
                    headers[parts[0].strip()] = parts[1].strip()
            self.stream.read_bytes(int(headers["Content-Length"]), self.on_body)

        def on_body(self, data):
            self.feed = data
            self.stream.close()

        def poll(self):
            self.connect()
            self.stream.write('GET %s HTTP/1.0\r\nHost: %s\r\n\r\n' % (self.path, self.host))
            self.stream.read_until("\r\n\r\n", self.on_headers)

    class FeedPollerTask(Task):
        def __init__(self, url, bus=None):
            Task.__init__(self, bus)
            self.poller = FeedPoller(url)
            self.poll_freq = 3

        def start_task(self):
            self.bus.subscribe("main", self.poll_feed)
            self.next = time.time() + self.poll_freq

        def stop_task(self):
            self.bus.unsubscribe("main", self.poll_feed)

        def poll_feed(self):
            if time.time() >= self.next:
                self.poller.poll()
                self.next = time.time() + self.poll_freq
        poll_feed.priority = 70

    if __name__ == '__main__':
        from conductor.process import TornadoProcess
        from conductor.lib.logger import open_logger
        from conductor.lib.sysinfo import ConsoleSysInfoTask

        p = TornadoProcess()
        p.logger = open_logger(stdout=True, logger_name="main")

        i = ConsoleSysInfoTask()
        i.monitoring_freq = 3
        p.register_task(i)

        t = FeedPollerTask(url="http://www.reddit.com/r/Python/.rss")
        p.register_task(t)

        p.run()


Kamaelia integration
====================

conductor integrates rather easily with the Kamaelia framework
and therefore with any Axon based component.

For instance, let's imagine you want to poll for a feed using HTTP,
you would have a similar piece of code:

.. code-block :: python 

    import time
    from Axon.Component import component
    from Axon.Ipc import shutdownMicroprocess, producerFinished
    from Kamaelia.Protocol.HTTP.HTTPClient import SimpleHTTPClient
    from Kamaelia.Util.Clock import CheapAndCheerfulClock
    from conductor.task import Task

    class FeedPoller(component):
        Inboxes = {"inbox"        : "",
                   "poll"         : "",
                   "control"      : "stops the component"}

        Outboxes = {"outbox"      : "",
                    "signal"      : "Shutdown signal"}

        def __init__(self, url):
            super(FeedPoller, self).__init__()
            self.url = url
            self.feed = None

        def initializeComponent(self):
            client = SimpleHTTPClient()
            self.link((client, 'outbox'), (self, 'inbox'))
            self.link((self, 'outbox'), (client, 'inbox'))
            self.addChildren(client)
            client.activate()

            clock = CheapAndCheerfulClock(interval=3.0)
            self.link((clock, 'outbox'), (self, 'poll'))
            self.addChildren(clock)
            clock.activate()

            return 1

        def main(self):
            yield self.initializeComponent()

            while 1:
                if self.dataReady("control"):
                    mes = self.recv("control")

                    if isinstance(mes, shutdownMicroprocess) or \
                           isinstance(mes, producerFinished):
                        self.send(producerFinished(), "signal")
                        break

                if self.dataReady("poll"):
                    self.recv("poll")
                    self.send(self.url, "outbox")

                if self.dataReady("inbox"):
                    self.feed = self.recv("inbox")

                if not self.anyReady():
                    self.pause()

                yield 1

    class FeedPollerTask(Task):
        def __init__(self, url, bus=None):
            Task.__init__(self, bus)
            self.poller = FeedPoller(url)

        def start_task(self):
            self.poller.activate()

    if __name__ == '__main__':
        from conductor.process import AxonProcess
        from conductor.lib.logger import open_logger
        from conductor.lib.sysinfo import ConsoleSysInfoTask

        p = AxonProcess()
        p.logger = open_logger(stdout=True, logger_name="main")

        i = ConsoleSysInfoTask()
        i.monitoring_freq = 3
        p.register_task(i)

        t = FeedPollerTask(url="http://www.reddit.com/r/Python/.rss")
        p.register_task(t)

        p.run()


Note that here we don't actually use the main channel directly
to perform the polling but we use the Kamaelia framework instead.

However that doesn't mean other tasks that have registered to the 
main channel won't be able to run as, internally, the ``AxonProcess`` 
will ensure it is always published to.
