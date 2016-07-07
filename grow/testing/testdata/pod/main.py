from google.appengine.ext import vendor
vendor.add('lib')

from grow.server import main as grow_main
import grow

pod = grow.Pod('.')
app = grow_main.create_wsgi_app(pod)
