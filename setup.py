# -*- coding: utf-8 -*-
from distutils.command.install import INSTALL_SCHEMES
from setuptools import setup
 
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']
        
setup(name = "conductor",
      version = '0.1.5',
      description = "Various processing tools",
      maintainer = "Sylvain Hellegouarch",
      maintainer_email = "sh@defuze.org",
      url = "http://trac.defuze.org/wiki/conductor",
      download_url = "http://www.defuze.org/oss/conductor/",
      packages = ["conductor", "conductor.lib", "conductor.protocol", 
                  "conductor.protocol.xmpp", "conductor.protocol.http",
                  "conductor.protocol.amqp"],
      platforms = ["any"],
      license = 'BSD',
      long_description = "Various processing tools",
      install_requires= ["timedump>=0.1.0"],
      zip_safe=False
     )

