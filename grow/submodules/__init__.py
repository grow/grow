import os
import sys


def fix_imports():
  here = os.path.dirname(__file__)
  dirs = [
      os.path.normpath(os.path.join(here, '..', '..')),
      os.path.normpath(os.path.join(here, 'babel')),
      os.path.normpath(os.path.join(here, 'dulwich')),
      os.path.normpath(os.path.join(here, 'google-apputils-python')),
      os.path.normpath(os.path.join(here, 'httplib2', 'python2')),
      os.path.normpath(os.path.join(here, 'pytz')),
      os.path.normpath(os.path.join(here, 'requests')),
  ]
  sys.path.extend(dirs)
