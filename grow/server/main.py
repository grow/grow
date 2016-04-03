#!/usr/bin/python

import os
import sys

# Allows "import grow" and "from grow import <name>".
sys.path.extend([os.path.join(os.path.dirname(__file__), '..', '..')])

from grow.common import utils
from grow.server import handlers
from protorpc.wsgi import service
from werkzeug import routing
from werkzeug import exceptions
from werkzeug import wsgi
from werkzeug import wrappers


class PodServer(object):

    def __init__(self, pod):
        self.pod = pod
        self.url_map = routing.Map([
            routing.Rule('/', endpoint=handlers.respond),
            routing.Rule('/<path:path>', endpoint=handlers.respond),
        ])

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return endpoint(self.pod, request)
        except exceptions.HTTPException, e:
            return e

    def wsgi_app(self, environ, start_response):
        request = wrappers.Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

#        ('/_grow/translations/(.*)', handlers.CatalogHandler),
#        ('/_grow/translations', handlers.CatalogsHandler),
#        ('/_grow/content', handlers.CollectionsHandler),
#        ('/_grow', handlers.ConsoleHandler),
#        ('/.*', handlers.PodHandler),


def CreateWSGIApplication(pod, debug=False):
    podserver_app = PodServer(pod)
    static_path = os.path.join(utils.get_grow_dir(), 'server', 'frontend')
    return wsgi.SharedDataMiddleware(podserver_app, {
        '/_grow/static': static_path,
    })
