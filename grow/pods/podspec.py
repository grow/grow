"""Podspec helper."""

from grow.translations import locales


class Error(Exception):
    pass


class PodSpecParseError(Error):
    pass


class PodSpec(object):

    def __init__(self, yaml, pod):
        yaml = yaml or {}
        self.yaml = yaml
        self.pod = pod
        self.grow_version = yaml.get('grow_version')
        _default_locale = yaml.get('localization', {}).get('default_locale', None)
        self.default_locale = locales.Locale.parse(_default_locale)
        self.fields = yaml

    def get_config(self):
        return self.yaml

    def __getattr__(self, name):
        if name in self.fields:
            return self.fields[name]
        tagged_name = '{}@'.format(name)
        if tagged_name in self.fields:
            return self.fields[tagged_name]
        return object.__getattribute__(self, name)

    def __iter__(self):
        return self.yaml.__iter__()

    @property
    def home(self):
        return self.pod.get_home_doc()

    @property
    def root(self):
        return self.fields.get('root', '')

    @property
    def localization(self):
        return self.fields.get('localization')

    def get_locale_alias(self, locale):
        """Get the locale alias for a given locale."""
        if 'localization' in self.yaml and 'aliases' in self.yaml['localization']:
            aliases = self.yaml['localization']['aliases']
            for custom_locale, babel_locale in aliases.iteritems():
                normalized_babel_locale = babel_locale.lower()
                if locale == normalized_babel_locale:
                    return custom_locale
        return locale
