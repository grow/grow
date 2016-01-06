"""Instructs httplib2 where to find cacerts.

See:
https://github.com/jcgregorio/httplib2/blob/master/python2/httplib2/__init__.py
"""

from . import utils


def get():
    return utils.get_cacerts_path()
