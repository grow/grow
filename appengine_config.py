from grow import submodules
submodules.fix_imports()


#def webapp_add_wsgi_middleware(app):
#  from google.appengine.ext.appstats import recording
#  app = recording.appstats_wsgi_middleware(app)
#  return app

appstats_MAX_STACK = 20
