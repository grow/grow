"""Path formatter for formatting grow paths."""

import datetime
import re
import string
from grow.common import structures
from grow.common import utils


HTML_EXTENSIONS = ('.html', '.htm')
VALID_DOC_EXTENSIONS = ('.html', '.htm', '.xml', '.svg')
INDEX_BASE_ENDINGS = ('/{base}', '/{base}/')


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
        if not doc.view.endswith(HTML_EXTENSIONS):
            return path
        if path.endswith(VALID_DOC_EXTENSIONS):
            return path
        if path and not path.endswith('/'):
            return '{}/'.format(path)
        return path

    @staticmethod
    def _locale_or_alias(locale):
        if not locale:
            return ''
        if not isinstance(locale, str) and locale.alias is not None:
            return locale.alias
        return str(locale)

    def format_doc(self, doc, path, locale=None, parameterize=False):
        """Format a URL path using the doc information."""
        path = '' if path is None else path

        # Most params should always be replaced.
        params = self.params_pod()
        params.update(self.params_doc(path, doc))
        params = self.params_lower(path, params)

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

    def format_static(self, path, locale=None, parameterize=False,
                      fingerprint=None):
        """Format a static document url."""

        params = self.params_pod()
        path = utils.safe_format(path, **params)

        if parameterize:
            path = self.parameterize(path)

        params = {}

        if fingerprint:
            params['fingerprint'] = fingerprint

        params['locale'] = self._locale_or_alias(locale)

        if params:
            path = utils.safe_format(path, **params)

        return self.strip_double_slash(path)

    def format_view(self, doc, path, parameterize=False):
        """Format a URL path using the doc information for views."""
        path = '' if path is None else path

        # Most params should always be replaced.
        params = self.params_pod()
        params.update(self.params_doc(path, doc))
        params = self.params_lower(path, params)

        path = utils.safe_format(path, **params)

        if parameterize:
            path = self.parameterize(path)

        return self.strip_double_slash(path)

    def params_doc(self, path, doc):
        """Selective access to the document properties depending on path."""
        params = {}
        # Remove the base when the path ends with the base and is index.
        if doc.base == 'index' and path.endswith(INDEX_BASE_ENDINGS):
            params['base'] = ''
        else:
            params['base'] = doc.base
        params['collection'] = structures.AttributeDict(
            base_path=doc.collection_base_path,
            sub_path=doc.collection_base_path,
            basename=doc.collection.basename,
            root=doc.collection.root)
        if '{category}' in path:
            params['category'] = doc.category
        if '{parent}' in path:
            params['parent'] = doc.parent if doc.parent else utils.DummyDict()
        if '{slug}' in path:
            params['slug'] = doc.slug
        if '{date}' in path:
            if isinstance(doc.date, datetime.datetime):
                params['date'] = doc.date.date()
            else:
                params['date'] = doc.date
        return params

    def params_lower(self, path, params):
        """Update to support lowercase when in the path."""
        if '|lower' in path:
            for key, value in params.items():
                if isinstance(value, str):
                    params['{}|lower'.format(key)] = value.lower()
        return params

    def params_pod(self):
        params = {}
        podspec = self.pod.podspec.get_config()
        if 'root' in podspec:
            params['root'] = podspec['root']
        else:
            params['root'] = ''
        params['env'] = self.pod.env
        return params
