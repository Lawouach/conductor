# -*- coding: utf-8 -*-
__docformat__ = "restructuredtext en"
import os
import time

from bridge import Element as E
from bridge.common import XMPP_IBR_NS, XMPP_STANZA_ERROR_NS,\
     XMPP_SASL_NS
from headstock.lib.jid import JID
from headstock.lib.stanza import Stanza
from headstock.lib.utils import generate_unique

from conductor.task import Task


__all__ = ['XMPPProcessTask', 'XMPPClientSettings']

CONNECTING = 0
CONNECTED = 1
DISCONNECTED = 2
COMPLETED = 3

class XMPPClientSettings(object):
    """
    XMPP client connection settings.
    """
    def __init__(self):
        self.username = None
        self.password = None
        self.domain = None
        self.resource = None
        self.hostname = None
        self.port = 5222
        self.tls = False
        self.register = False
        self.unregister = False
        self.log_dir = None
        self.log_stdout = False

class XMPPProcessTask(Task):
    """
    XMPP processing task.
    
    :Parameters:
      - `bus`: WSPBus instance to which this task subscribes to.
    """
    def __init__(self, bus=None):
        Task.__init__(self, bus)
        self.client = None
        self.settings = XMPPClientSettings()

    def start_task(self):
        """
        Starts the XMPP process task.
        """
        self.setup_client()
        self.start_client()

    def stop_task(self):
        if self._check():
            if self.settings.unregister:
                self.bus.unsubscribe('main', self._restart)
                self._log("Unregistering XMPP client")
                self.unregister()
                self.bus.publish("main")
                self._log("Stopping XMPP client")
                while self._check():
                    self.bus.publish("main")
                    time.sleep(0.005)
                self.client = None
                self._log("XMPP client stopped")
            else:
                self.stop_client()
            
    def setup_client(self):
        """
        Setups the XMPP client.
        """
        self._log("Setting up XMPP client")
        self.init_client()
        self.add_extensions()

    def start_client(self):
        """
        If `self.client` is not `None`, calls `start()` on it.
        """
        if self.client:
            self._log("Starting XMPP client")
            self.bus.subscribe('main', self._restart)
            self.client.start()

    def stop_client(self):
        """
        If `self.client` is not `None`, calls `stop()` on it.
        Sets `self.client` to `None` afterwards.
        """
        if self.client:
            self.bus.unsubscribe('main', self._restart)
            self._log("Stopping XMPP client")
            self.client.stop()
            while self.client and self.client.running:
                time.sleep(0.005)
            self.client = None
            self._log("XMPP client stopped")

    def restart_client(self):
        """
        Performs the following actions:
          * Stops the client
          * Setup the client
          * Start the client
        """
        self._log("Restarting XMPP client")
        self.stop_client()
        self.setup_client()
        self.start_client()
        
    def init_client(self):
        """
        Initializes the XMPP client instance.
        """
        from headstock.client import AsyncClient

        jid = JID(self.settings.username, self.settings.domain, self.settings.resource)
        self.client = AsyncClient(unicode(jid), self.settings.password,
                                  hostname=self.settings.hostname, port=self.settings.port,
                                  tls=self.settings.tls, registercls=None)
        log_path = None
        if self.settings.log_dir:
            log_path = "%s.log" % os.path.join(self.settings.log_dir, self.settings.username)
        self.client.set_log(path=log_path, stdout=self.settings.log_stdout)

        if self.settings.register:
            self.client.stream.register = True
            self.client.swap_handler(self.register, "register",
                                     "http://jabber.org/features/iq-register",
                                     once=True, forget=False)
            self.client.swap_handler(self.handle_registration, "query",
                                     XMPP_IBR_NS, once=True)
            self.client.swap_handler(self.handle_conflict, "conflict",
                                     XMPP_STANZA_ERROR_NS, once=True)
            self.client.swap_handler(self.handle_not_authorized, "not-authorized",
                                     XMPP_SASL_NS, once=True)

    def _restart(self):
        if not self.client or not self.client.running:
            self.restart_client()
    
    def _check(self):
        if not self.client:
            return False
        return self.client.running
        
    def add_extensions(self):
        """
        Override this method to add XMPP support you require.
        """
        pass
    
    def register(self, e):
        iq = Stanza.get_iq(stanza_id=generate_unique())
        E(u'register', namespace=XMPP_IBR_NS, parent=iq)
        self.client.send_stanza(iq)
    
    def unregister(self):
        stanza_id = generate_unique()
        iq = Stanza.set_iq(stanza_id=stanza_id)
        query = E(u'query', namespace=XMPP_IBR_NS, parent=iq)
        E(u'remove', namespace=XMPP_IBR_NS, parent=query)
        self.client.register_on_iq(self.unregistered, type=u'result',
                                   id=stanza_id, once=True)
        self.client.send_stanza(iq)
        
    def unregistered(self, e):
        pass

    def registered(self, e):
        self._log("XMPP client registered successfully")
        self.settings.register = False

    def handle_registration(self, e):
        iq = Stanza.set_iq(stanza_id=e.xml_parent.get_attribute_value('id'))
        query = E(u'query', namespace=XMPP_IBR_NS, parent=iq)
        E(u'username', content=self.settings.username, namespace=XMPP_IBR_NS, parent=query)
        E(u'password', content=self.settings.password, namespace=XMPP_IBR_NS, parent=query)

        self.client.register_on_iq(self.registered, type=u'result',
                                   id=e.xml_parent.get_attribute_value('id'), once=True)
        
        self.client.send_stanza(iq)
    
    def handle_conflict(self, e):
        self.settings.register = False
        self.restart_client()

    def handle_not_authorized(self, e):
        pass
        
class XMPPTornadoProcessTask(XMPPProcessTask):
    def init_client(self):
        """
        Initializes the XMPP client instance.
        """
        from headstock.client import TornadoClient
        
        registercls = None
        if self.settings.register:
            from headstock.register import Register
            registercls = Register
        
        jid = JID(self.settings.username, self.settings.domain, self.settings.resource)
        self.client = TornadoClient(unicode(jid), self.settings.password,
                                    hostname=self.settings.hostname, port=self.settings.port,
                                    tls=self.settings.tls, registercls=registercls)
        log_path = None
        if self.settings.log_dir:
            log_path = "%s.log" % os.path.join(self.settings.log_dir, self.settings.username)
        self.client.set_log(path=log_path, stdout=self.settings.log_stdout)

class XMPPAxonProcessTask(XMPPProcessTask):
    def init_client(self):
        """
        Initializes the XMPP client instance.
        """
        from headstock.client import KamaeliaClient
        
        registercls = None
        if self.settings.register:
            from headstock.register import Register
            registercls = Register
        
        jid = JID(self.settings.username, self.settings.domain, self.settings.resource)
        self.client = KamaeliaClient(unicode(jid), self.settings.password,
                                     hostname=self.settings.hostname, port=self.settings.port,
                                     tls=self.settings.tls, registercls=registercls)
        log_path = None
        if self.settings.log_dir:
            log_path = "%s.log" % os.path.join(self.settings.log_dir, self.settings.username)
        self.client.set_log(path=log_path, stdout=self.settings.log_stdout)

if __name__ == '__main__':
    from conductor.lib.logger import open_logger
    from conductor.process import AsyncoreProcess
    
    p = AsyncoreProcess()
    p.logger = open_logger(stdout=True)

    for i in range(0, 1000):
        t = XMPPProcessTask()
        t.settings.username = "test%d" % i
        t.settings.password = "test"
        t.settings.domain = "localhost"
        t.settings.resource = "conductor"
        t.settings.hostname = "localhost"
        t.settings.log_stdout = False#True
        t.settings.register = False
        t.settings.unregister = True
        p.register_task(t)
    
    p.run ()
    
