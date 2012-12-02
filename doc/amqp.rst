============
AMQP support
============

conductor comes with a AMQP extension which permits 
your application to connect and consume or publish
AMQP messages.

.. note:: 

   conductor requires `carrot <http://pypi.python.org/pypi/carrot/>`_  to 
   be installed for the AMQP support.

conductor offers three different tasks related to AMQP:

* ``conductor.protocol.amqp.broker.AMQPBrokerTask`` which takes care of creating, releasing and retrieving connections to the AMQP server.
* ``conductor.protocol.amqp.consumer.ConsumerTask`` making it simple to create AMQP consumers.
* ``conductor.protocol.amqp.consumer.PublisherTask`` making it simple to create AMQP publishers.

The ``AMQPBrokerTask`` task holds a pool of connections from which you can
get connection by publishing to the ``"get-amqp-broker"`` channel of
the task bus. Thus, retrieving a connection can be done as follow:

.. code-block :: python 

   connection = bus.publish("get-amqp-broker").pop()

Once you've finished with the connection, you must release it as follow:

.. code-block :: python 

   bus.publish("release-amqp-broker", connection)

This will not close the connection but make it available within the pool once more.
The pool will close all its opened connections when the task stops.


.. note:: 
   The result of the call to publish is actually a list which explains the ``pop()`` call.

The ``ConsumerTask`` tasks subcribes to the ``"get-amqp-consumer"`` channel
to which you should publish if you want to get a consumer instance. Its parameters
are a connection and the parameters that ``carrot.messaging.Consumer`` takes.

The ``PublisherTask`` tasks subcribes to the ``"get-amqp-publisher"`` channel
to which you should publish if you want to get a publisher instance. Its parameters
are a connection and the parameters that ``carrot.messaging.Publisher`` takes.

The next section will demonstrate how you may create a simple 
task which consumes messages it publishes.


PubSub task with AMQP
=====================

Note that we bend to the rule saying that tasks are not application for the sake
of conciseness.

.. code-block :: python 

    from conductor.process import Process
    from conductor.lib.logger import open_logger
    from conductor.protocol.amqp.broker import AMQPBrokerTask
    from conductor.protocol.amqp.consumer import ConsumerTask
    from conductor.protocol.amqp.publisher import PublisherTask

    class PubSub(Task):
        def __init__(self, bus=None):
            Task.__init__(self, bus)

        def start_task(self):
            self.broker =  self.bus.publish("get-amqp-broker").pop()
            self.publisher = self.bus.publish("get-amqp-publisher", self.broker,
                                              exchange="X", routing_key="K").pop()
            self.consumer = self.bus.publish("get-amqp-consumer", self.broker, queue="Q",
                                             routing_key="K", exchange="X").pop()
            self.bus.subscribe("main", self.pub_and_print)

        def stop_task(self):
            self.bus.unsubscribe("main", self.pub_and_print)
            self.consumer.close()
            self.publisher.close()
            self.bus.publish("release-amqp-broker", broker)

        def pub_and_print(self):
            self.publisher.send("hello")
            self.bus.log(self.consumer.fetch())


    p = Process()
    p.interval = 0
    p.logger = open_logger(stdout=True,
                           logger_name="main")

    t = AMQPBrokerTask()
    t.settings.hostname = "localhost"
    t.settings.username = "test"
    t.settings.password = "test"
    t.settings.vhost = "/"
    p.register_task(t)

    c = ConsumerTask()
    p.register_task(c)

    o = PublisherTask()
    p.register_task(o)

    m = PubSub()
    p.register_task(m)
    
    p.run()
