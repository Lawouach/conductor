==============
Under the hood
==============

The process bus
***************

Internally conductor is heavily architectured around the
`CherryPy process bus API <http://www.cherrypy.org/wiki/WSPBSpec>`_.
The bus process isn't actually tied to the HTTP server coming with CherryPy,
but is provided by the same package. The bus project
can be used outside of any HTTP context.

Each time you initialize a process it gets its own bus to which
tasks are subscribed to and therefore can publish to as well. 
The bus processing is explained in the 
`CherryPy spec <http://www.cherrypy.org/wiki/WSPBSpec#TheBusobject>`_.


Task as bus subscribers and publishers
**************************************

conductor tasks are actually bus process `plugins as provided by CherryPy <http://www.cherrypy.org/browser/trunk/cherrypy/process/plugins.py>`_. Technically speaking, CherryPy plugins can be used along
with conductor process, tasks only extend the plugin interface by
providing a few helper methods. This means you can happily use 
the plugins bundled with CherryPy.

Tasks, or plugins, let you subscribe and unsubscribe from
the bus you attach them to. Both operations are automatically
performed by the process when you register or unregister tasks.
