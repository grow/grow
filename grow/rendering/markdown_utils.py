"""Markdown utility methods for pods."""

import copy
import markdown
from markdown.extensions import tables
from grow.common import markdown_extensions
from grow.common import structures
from grow.common import utils


class MarkdownUtil(object):
    """Utility class for working with pod flavored markdown."""

    def __init__(self, pod):
        self.pod = pod

    @property
    def extensions(self):
        """List of enabled extensions for the pod."""
        # Do not cache property so that the extensions are created fresh.
        extensions = [
            tables.TableExtension(),
            markdown_extensions.TocExtension(pod=self.pod),
            markdown_extensions.CodeBlockExtension(self.pod),
            markdown_extensions.IncludeExtension(self.pod),
            markdown_extensions.UrlExtension(self.pod),
            'markdown.extensions.fenced_code',
            'markdown.extensions.codehilite',
        ]

        for config in self.markdown_config:
            if config['kind'] in extensions:
                continue

            if config['kind'].startswith('markdown.extensions'):
                extensions.append(config['kind'])

        return extensions

    @utils.cached_property
    def extension_configs(self):
        """Extension configurations from the podspec."""
        extension_configs = {}

        for config in self.markdown_config:
            if config['kind'].startswith('markdown.extensions'):
                ext_config = copy.deepcopy(config)
                ext_config.pop('kind', None)
                if ext_config:
                    extension_configs[config['kind']] = ext_config

        # Special handling for code highlighting backwards compatability.
        config = self.extension_config('markdown.extensions.codehilite')
        codehilite_config = {
            'pygments_style': 'default',
            'noclasses': True,
            'css_class': 'code',
        }
        if 'theme' in config:
            codehilite_config['pygments_style'] = config.theme
        if 'classes' in config:
            codehilite_config['noclasses'] = not config.classes
        if 'class_name' in config:
            codehilite_config['css_class'] = config.class_name
        extension_configs['markdown.extensions.codehilite'] = codehilite_config

        return extension_configs

    @property
    def markdown(self):
        """Markdown object using the pod configuration."""
        return markdown.Markdown(
            extensions=self.extensions,
            extension_configs=self.extension_configs)

    @utils.cached_property
    def markdown_config(self):
        """Markdown config from podspec."""
        if 'markdown' in self.pod.podspec:
            markdown_config = self.pod.podspec.markdown
            if 'extensions' in markdown_config:
                return markdown_config['extensions']
        return []

    def extension_config(self, kind):
        """Get the markdown config for a specific extension."""
        for extension in self.markdown_config:
            if extension.get('kind', '') == kind:
                return structures.AttributeDict(extension)
        return structures.AttributeDict({})
