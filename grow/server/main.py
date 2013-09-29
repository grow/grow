#!/usr/bin/python

import appengine_config
import webapp2
from protorpc.wsgi import service
from grow.server import handlers
from grow.server import services

podserver_app = webapp2.WSGIApplication([
    ('/_grow/.*', handlers.ConsoleHandler),
    ('/.*', handlers.PodHandler),
])

services_app = service.service_mappings([
    ('/_api/pods.*', services.PodService),
], registry_path='/_api/protorpc', append_wsgi_apps=[podserver_app])
