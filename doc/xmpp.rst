============
XMPP support
============

conductor comes with a XMPP extension which permits 
your application to add XMPP clients as tasks.

Simple XMPP client
==================

The following snippet will show you how to create
a XMPP client task that will register the client
when activated and unregister when stopping.

.. code-block :: python 

    from conductor.process import AsyncoreProcess
    from conductor.protocol.xmpp import XMPPProcessTask
    from conductor.lib.logger import open_logger
    
    p = AsyncoreProcess()
    p.logger = open_logger(stdout=True,
                           logger_name="main")
    
    t = XMPPProcessTask()
    t.settings.username = "test"
    t.settings.password = "test"
    t.settings.domain = "localhost"
    t.settings.resource = "conductor"
    t.settings.hostname = "localhost"
    t.settings.log_stdout = True
    t.settings.register = True
    t.settings.unregister = True
    p.register_task(t)

    p.run ()

As you can see not too difficult.

Extend the default XMPP client
==============================

By default the provided XMPP client will only
register, unregister and creates a session to the
XMPP server. In order to be more useful you need
to subclass the XMPPProcessTask and implement the
``add_extension`` method to register new behaviors
to the client.

The following example demonstrates how to build 
a echo client that will return messages to their
senders (in this example we assume the client
is already registered with contacts and we do not
unregister it when the client stops).

.. note:: 

   Read the `headstock documentation <http://trac.defuze.org/wiki/headstock>`_  to understand how to write XMPP handlers.

.. code-block :: python 

    import headstock
    from bridge import Element as E
    from bridge.common import XMPP_CLIENT_NS
    from conductor.protocol.xmpp import XMPPProcessTask

    class Echo(object):
        def ready(self, client):
            self.client = client

        @headstock.xmpphandler('message', XMPP_CLIENT_NS)
        def message(self, e):
            who = e.get_attribute_value('from')
            body = e.get_child('body', ns=e.xml_ns)

            # Echo the received message
            m = E(u"message", attributes={u'from': unicode(self.client.jid),
                                          u'to': who, u'type': u'chat',
                                          u'id': e.get_attribute_value('id')},
                  namespace=XMPP_CLIENT_NS)
            E(u'body', content=body.xml_text, namespace=XMPP_CLIENT_NS, parent=m)

            self.client.send_stanza(m)

    class EchoTask(XMPPProcessTask):
        def __init__(self, bus=None):
            XMPPProcessTask.__init__(self, bus)

        def add_extensions(self):
            self.client.register(Echo())

    if __name__ == '__main__':
        from conductor.lib.logger import open_logger
        from conductor.process import AsyncoreProcess

        p = AsyncoreProcess()
        p.logger = open_logger(stdout=True,
                               logger_name="main")

        t = EchoTask()
        t.settings.username = "test"
        t.settings.password = "test"
        t.settings.domain = "localhost"
        t.settings.resource = "conductor"
        t.settings.hostname = "localhost"
        t.settings.log_stdout = True
        t.settings.register = False
        t.settings.unregister = False
        p.register_task(t)

        p.run ()
