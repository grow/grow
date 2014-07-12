#!/usr/bin/python

import os
import sys

# Allows "import grow" and "from grow import <name>".
sys.path.extend([os.path.join(os.path.dirname(__file__), '..', '..')])

import webapp2
from protorpc.wsgi import service
from grow.server import handlers
from grow.server import services

podserver_app = webapp2.WSGIApplication([
    ('/.*', handlers.PodHandler),
])
routes = [
    ('/_api/pods.*', services.PodService),
]
application = service.service_mappings(
    routes,
    service_prefix='/_api',
    registry_path='/_api/protorpc',
    append_wsgi_apps=[podserver_app])
