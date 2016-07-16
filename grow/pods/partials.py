"""Partials contain lightweight portable documents."""

from . import documents
from grow.common import structures
from grow.common import utils
from grow.pods import locales
import json
import logging
import operator
import os
import re


class Error(Exception):
    pass

class BadPartialNameError(Error, ValueError):
    pass

class PartialDoesNotExistError(Error, ValueError):
    pass

class PartialExistsError(Error):
    pass

class Partial(object):
    CONTENT_PATH = '/partial'
    _content_path_regex = re.compile('^' + CONTENT_PATH + '/?'
)

    def __init__(self, pod_path, _pod):
        utils.validate_name(pod_path)
        regex = Partial._content_path_regex
        self.pod = _pod
        self.partial_path = regex.sub('', pod_path).strip('/')
        
        self.pod_path = pod_path
        self.basename = os.path.basename(self.partial_path)

    def __repr__(self):
        return '<Partial "{}">'.format(self.partial_path)

    def __eq__(self, other):
        return (isinstance(other, Partial) 
                and self.partial_path == other.partial_path)

    def __getattr__(self, name):
        try:
            return self.fields[name]
        except KeyError:
            return object.__getattribute__(self, name)

    @utils.cached_property
    def fields(self):
        fields = utils.untag_fields(self.tagged_fields)
        return {} if not fields else fields

    @utils.cached_property
    def tagged_fields(self):
        return self.yaml

    @classmethod
    def list(cls, pod):
        items = []
        for root, dirs, _ in pod.walk(self.pod_path):
            if root == self.pod.abs_path(self.pod_path):
                for dir_name in dirs:
                    pod_path = os.path.join(self.pod_path, dir_name)
                    items.append(seld.pod.get_partial(pod_path))

        return items

    # TODO: (drGrove) Make this actually work
    @property
    def exists(self):
       """Returns whether the partial exists, as determined by whether
       the partial if found in the path."""
       return True

   @classmethod
   def create(cls, partial_path, fields, pod):
       """Creates a new partial by creating the partial file."""
       partial = cls.get(partial_path, pod)
       if partial.exists:
           raise PartialExistsError('{} already exists').format(partial)
       fields = utils.dump_yaml(fields)
       pod.write_file(partial.basename, fields)
       return partial

   @classmethod
   def get(cls, partial_path, _pod):
       """Returns a partial object."""
       return cls(partial_path, _pod)
