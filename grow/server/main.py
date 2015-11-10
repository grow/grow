#!/usr/bin/python

import os
import sys

# Allows "import grow" and "from grow import <name>".
sys.path.extend([os.path.join(os.path.dirname(__file__), '..', '..')])

from grow.common import utils
from grow.server import handlers
from protorpc.wsgi import service
from werkzeug import wsgi
import webapp2


class Response(webapp2.Response):
  default_conditional_response = True


class WSGIApplication(webapp2.WSGIApplication):
  response_class = Response


def CreateWSGIApplication(pod=None, debug=False):
  podserver_app = WSGIApplication([
      ('/_grow/translations/(.*)', handlers.CatalogHandler),
      ('/_grow/translations', handlers.CatalogsHandler),
      ('/_grow/content', handlers.CollectionsHandler),
      ('/_grow', handlers.ConsoleHandler),
      ('/.*', handlers.PodHandler),
  ], debug=debug)
  podserver_app.registry['pod'] = pod
  api_routes = []
  api_app = service.service_mappings(
      api_routes,
      service_prefix='/_api',
      registry_path='/_api/protorpc',
      append_wsgi_apps=[podserver_app])
  static_path = os.path.join(utils.get_grow_dir(), 'server', 'frontend')
  return wsgi.SharedDataMiddleware(api_app, {
      '/_grow/static': static_path,
  })
