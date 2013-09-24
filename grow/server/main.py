#!/usr/bin/python

import appengine_config
import webapp2
from grow.server import handlers


routes = (
    ('/_grow/.*', handlers.ConsoleHandler),
    ('/.*', handlers.PodHandler),
)
application = webapp2.WSGIApplication(routes)
