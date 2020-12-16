# -*- coding: utf-8 -*-
"""
Utility for converting Grow sites to enable collection level routing. Instead
of storing things that affect routing directly in the document it is stored
at the level of the collection to prevent the need to read every document to
generate the routing information.

WARNING: This feature is used in the `separate_routing` experiment.

Usage:

    grow convert --type=collection_routing
"""

import collections
import logging
import os
import yaml
from grow.common import yaml_utils


ROUTES_FILENAME = '_blueprint.yaml'
COLLECTION_META_KEYS = ('$path', '$localization', '$view')
COLLECTION_BLUEPRINT_KEYS = (
    '$path', '$localization', '$view', 'path', 'localization', 'view',
    'composite_files')


class Error(Exception):

    def __init__(self, message):
        super(Error, self).__init__(message)
        self.message = message


class RoutesData(object):
    """Store and format the routes information pulled from the documents."""

    def __init__(self, collection_path, blueprint):
        self.paths = collections.OrderedDict()
        self.collection_path = collection_path
        self.blueprint = blueprint

    @property
    def data(self):
        """The yaml contents to write to the file."""
        data = collections.OrderedDict()

        # Pull over the existing blueprint data.
        if '$path' in self.blueprint or 'path' in self.blueprint:
            data['path'] = self.blueprint.get(
                '$path', self.blueprint.get('path'))

        tagged_keys = tuple(['{}@'.format(key)
                             for key in COLLECTION_BLUEPRINT_KEYS])

        for key in sorted(self.blueprint.keys()):
            if key in COLLECTION_BLUEPRINT_KEYS or key.startswith(tagged_keys):
                data[key.lstrip('$')] = self.blueprint[key]

        data['routes'] = self.paths
        return data

    def extract_doc(self, doc):
        """Extract the meta information from the doc to use for the routes."""
        if doc.pod_path.endswith('.yaml'):
            raw_data = yaml.load(
                doc.pod.read_file(doc.pod_path), Loader=yaml_utils.PlainTextYamlLoader)
        else:
            raw_data = doc.format.front_matter.raw_data

        if not raw_data:
            print('No raw data found for document: {}'.format(doc.pod_path))
            return

        data = collections.OrderedDict()

        tagged_keys = tuple(['{}@'.format(key)
                             for key in COLLECTION_META_KEYS])

        for key, value in raw_data.items():
            if key in COLLECTION_META_KEYS or key.startswith(tagged_keys):
                normal_key = key.lstrip('$')
                if 'path' in key:
                    # Use `__NONE` as sentinel to support equating a `value` of None.
                    collection_path = self.blueprint.get(
                            key, self.blueprint.get(normal_key, '__NONE'))
                    # Skip the paths that are the same as the collection.
                    if collection_path == value:
                        continue
                data[normal_key] = value

        if data:
            self.paths[doc.collection_sub_path[1:]] = data

    def write_routes(self, pod, collection):
        """Write the converted routes to the configuration file."""
        routes_file = os.path.join(collection.pod_path, ROUTES_FILENAME)

        if self.data['routes']:
            print(' └─ Writing: {}'.format(routes_file))
            print('')
            output = yaml.dump(
                self.data, Dumper=yaml_utils.PlainTextYamlDumper,
                default_flow_style=False, allow_unicode=True, width=800)
            pod.write_file(routes_file, output)
        else:
            print(' └─ Skipping: {}'.format(routes_file))
            print('')


class ConversionCollection(object):
    """Temporary collection class for doing a conversion for a collection."""

    def __init__(self, pod, collection):
        self.pod = pod
        self.collection = collection
        self.routes_data = RoutesData(collection.pod_path, collection.yaml)

    def convert(self):
        """Perform the conversion to use collection based routing."""
        print('Converting: {}'.format(self.collection.pod_path))

        # Pull out the meta information from all the docs.
        sorted_docs = sorted(self.collection.list_docs_unread(), key=lambda doc: doc.pod_path)
        for doc in sorted_docs:
            self.routes_data.extract_doc(doc)

        self.routes_data.write_routes(self.pod, self.collection)


class Converter(object):

    @staticmethod
    def convert(pod):
        logging.info('Converting pod for collection level routing: {}'.format(
            pod.root))

        for collection in pod.list_collections():
            conv_collection = ConversionCollection(pod, collection)
            conv_collection.convert()
