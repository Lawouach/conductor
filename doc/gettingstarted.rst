.. _getting_started:

============
Requirements
============

Minimum
=======
* Python 2.5+
* cherrypy 3.2.0+ http://www.cherrypy.org/

XMPP support
============
* headstock 0.4.1 http://trac.defuze.org/wiki/headstock

Kamaelia
========
If you want to run the Kamaelia client:

* Kamaelia 0.9.6+ http://www.kamaelia.org/Home

Tornado
=======
If you want to run the Tornado client:

* Tornado 0.2+ http://www.tornadoweb.org/

==========
Installing
==========

From a packaged release
=======================

.. code-block:: bash 

   $ easy_install -U conductor


From the source code 
=====================

.. code-block:: bash 
   
   $ svn co https://svn.defuze.org/oss/conductor/ conductor-trunk
   $ cd conductor-trunk 
   $ python setup.py install
