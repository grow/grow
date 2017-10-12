"""Path formatter for formatting grow paths."""

import datetime
import re
import string
from grow.common import utils


class SafeDict(dict):

    def __missing__(self, key):
        return '{' + key + '}'


class PathFormat(object):
    """Format url paths using the information from the pod."""

    PARAM_CURLY_REGEX_SECTION = re.compile(r'/{([^}]*)}/')
    PARAM_CURLY_REGEX_END = re.compile(r'/{([^}]*)}$')

    def __init__(self, pod):
        self.pod = pod
        self.formatter = string.Formatter()

    @staticmethod
    def parameterize(path):
        """Replace stubs with routes params."""
        path = re.sub(PathFormat.PARAM_CURLY_REGEX_SECTION, r'/:\1/', path)
        return re.sub(PathFormat.PARAM_CURLY_REGEX_END, r'/:\1', path)

    @staticmethod
    def strip_double_slash(path):
        """Remove double slashes from the path."""
        while '//' in path:
            path = path.replace('//', '/')
        return path

    def format_doc(self, doc, path, locale=None, parameterize=False):
        """Format a URL path using the doc information."""
        path = '' if path is None else path
        path = self.format_pod(path)

        # Most params should always be replaced.
        params = SafeDict()
        params['base'] = doc.base
        params['category'] = doc.category
        params['collection'] = doc.collection
        params['parent'] = doc.parent if doc.parent else utils.DummyDict()
        params['slug'] = doc.slug

        if isinstance(doc.date, datetime.datetime):
            params['date'] = doc.date.date()
        else:
            params['date'] = doc.date

        if '|lower' in path:
            for key, value in params.items():
                if isinstance(value, basestring):
                    params['{}|lower'.format(key)] = value.lower()

        path = self.formatter.vformat(path, (), params)

        if parameterize:
            path = self.parameterize(path)

        params = SafeDict()

        if locale is not None:
            if not isinstance(locale, basestring) and locale.alias is not None:
                params['locale'] = locale.alias
            else:
                params['locale'] = locale
        elif doc.locale is not None:
            params['locale'] = doc.locale.alias
        else:
            params['locale'] = ''
        params['locale'] = str(params['locale']).lower()

        path = self.formatter.vformat(path, (), params)
        return PathFormat.strip_double_slash(path)

    def format_pod(self, path):
        """Format a URL path using the pod information."""
        path = '' if path is None else path
        params = SafeDict()
        if 'root' in self.pod.podspec:
            params['root'] = self.pod.podspec['root']
        else:
            params['root'] = ''
        params['env'] = self.pod.env
        path = self.formatter.vformat(path, (), params)
        return PathFormat.strip_double_slash(path)
