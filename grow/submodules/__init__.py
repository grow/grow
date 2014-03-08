# TODO(jeremydw): Reevaluate if we need this for non-standard distribution
# (such as GAE, or a Mac application).
import os
import sys


def fix_imports():
  here = os.path.dirname(__file__)
  dirs = [
      os.path.normpath(os.path.join(here, '..', '..')),
  ]
  sys.path[1:1] = dirs
  return dirs
