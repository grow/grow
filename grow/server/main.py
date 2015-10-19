#!/usr/bin/python

import os
import sys

# Allows "import grow" and "from grow import <name>".
sys.path.extend([os.path.join(os.path.dirname(__file__), '..', '..')])

import webapp2
from protorpc.wsgi import service
from grow.server import handlers


class Response(webapp2.Response):
  default_conditional_response = True


class WSGIApplication(webapp2.WSGIApplication):
  response_class = Response


def CreateWSGIApplication(pod=None, debug=False):
  podserver_app = WSGIApplication([
      ('/.*', handlers.PodHandler),
  ], debug=debug)
  podserver_app.registry['pod'] = pod
  routes = []
  return service.service_mappings(
      routes,
      service_prefix='/_api',
      registry_path='/_api/protorpc',
      append_wsgi_apps=[podserver_app])
