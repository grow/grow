"""Path formatter for formatting grow paths."""

import datetime
import re
import string
from grow.common import structures
from grow.common import utils


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

    @staticmethod
    def trailing_slash(doc, path):
        """Adds trailing slash when appropriate."""
        if not doc.view.endswith(('.html', '.htm')):
            return path
        if path and not path.endswith('/'):
            return '{}/'.format(path)
        return path

    @staticmethod
    def _locale_or_alias(locale):
        if not locale:
            return ''
        if not isinstance(locale, basestring) and locale.alias is not None:
            return locale.alias.lower()
        return str(locale).lower()

    def format_doc(self, doc, path, locale=None, parameterize=False):
        """Format a URL path using the doc information."""
        path = '' if path is None else path

        # Most params should always be replaced.
        params = self.params_pod()
        params['base'] = doc.base
        params['category'] = doc.category
        params['collection'] = structures.AttributeDict(
            base_path=doc.collection_base_path,
            basename=doc.collection.basename,
            root=doc.collection.root)
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

        path = utils.safe_format(path, **params)

        if parameterize:
            path = self.parameterize(path)

        params = {}

        if locale is None:
            locale = doc.locale
        params['locale'] = self._locale_or_alias(locale)

        path = utils.safe_format(path, **params)
        path = self.strip_double_slash(path)
        return self.trailing_slash(doc, path)

    def format_pod(self, path, parameterize=False):
        """Format a URL path using the pod information."""
        path = '' if path is None else path

        params = self.params_pod()
        path = utils.safe_format(path, **params)

        if parameterize:
            path = self.parameterize(path)

        return self.strip_double_slash(path)

    def format_static(self, path, locale=None, parameterize=False):
        """Format a static document url."""

        params = self.params_pod()
        path = utils.safe_format(path, **params)

        if parameterize:
            path = self.parameterize(path)

        params['locale'] = self._locale_or_alias(locale)
        if params['locale']:
            path = utils.safe_format(path, **params)

        return self.strip_double_slash(path)

    def params_pod(self):
        params = {}
        podspec = self.pod.podspec.get_config()
        if 'root' in podspec:
            params['root'] = podspec['root']
        else:
            params['root'] = ''
        params['env'] = self.pod.env
        return params
