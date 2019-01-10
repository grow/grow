from babel import localedata
from grow.pods import errors
from grow.pods import messages
import pickle
import os
import babel
import re


class Locales(object):

    def __init__(self, pod):
        self.pod = pod

    def list_groups(self):
        if 'locales' not in self.pod.yaml:
            return []
        return self.pod.yaml['locales'].keys()

    def get_regions(self, group_name='default'):
        if 'regions' not in self.pod.yaml:
            return []
        try:
            return self.pod.yaml['locales'][group_name].get('regions', [])
        except errors.PodConfigurationError:
            return []

    def get_languages(self, group_name='default'):
        if 'locales' not in self.pod.yaml:
            return []
        try:
            return self.pod.yaml['locales'][group_name].get('languages', [])
        except errors.PodConfigurationError:
            return []

    def to_message(self):
        message = messages.LocalesMessage()
        message.groups = []
        for group_name in self.list_groups():
            group_message = messages.LocaleGroupMessage()
            group_message.group_name = group_name
            group_message.regions = self.get_regions(group_name)
            group_message.languages = self.get_languages(group_name)
            message.groups.append(group_message)
        return message


class Locale(babel.Locale):
    RTL_REGEX = re.compile('^(he|ar|fa|ur)(\W|$)')
    _alias = None

    def __init__(self, language, *args, **kwargs):
        # Normalize from "de_de" to "de_DE" for case-sensitive filesystems.
        parts = language.rsplit('_', 1)
        if len(parts) > 1:
            language = '{}_{}'.format(parts[0], parts[1].upper())
        super(Locale, self).__init__(language, *args, **kwargs)

    @classmethod
    def parse(cls, *args, **kwargs):
        locale = super(Locale, cls).parse(*args, **kwargs)
        # Weak attempt to permit fuzzy locales (locales for which we still have
        # language and country information, but not a full localedata file for),
        # but disallow completely invalid locales. See note at end of file.
        if locale and locale.get_display_name() is None:
            raise ValueError('{} is not a valid locale identifier'.format(args[0]))
        return locale

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if isinstance(other, basestring):
            return str(self).lower() == other.lower()
        return super(Locale, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '<Locale: "{}">'.format(str(self))

    @classmethod
    def parse_codes(cls, codes):
        return [cls.parse(code) for code in codes]

    @property
    def is_rtl(self):
        return Locale.RTL_REGEX.match(self.language)

    @property
    def direction(self):
        return 'rtl' if self.is_rtl else 'ltr'

    @classmethod
    def from_alias(cls, pod, alias):
        podspec = pod.get_podspec()
        config = podspec.get_config()
        if 'localization' in config and 'aliases' in config['localization']:
            aliases = config['localization']['aliases']
            for custom_locale, babel_locale in aliases.iteritems():
                if custom_locale == alias:
                    return cls.parse(babel_locale)
        return cls.parse(alias)

    def set_alias(self, pod):
        podspec = pod.get_podspec()
        self._alias = podspec.get_locale_alias(str(self).lower())

    @property
    def alias(self):
        return self._alias

    @alias.setter
    def alias(self, alias):
        self._alias = alias


# NOTE: Babel does not support "fuzzy" locales. A locale is considered "fuzzy"
# when a corresponding "localedata" file that matches a given locale's full
# identifier (e.g. "en_US") does not exist. Here's one example: "en_BD". CLDR
# does not have a localedata file matching "en_BD" (English in Bangladesh), but
# it does have individual files for "en" and also "bn_BD". As it turns
# out, localedata files that correspond to a locale's full identifier (e.g.
# "bn_BD.dat") are actually pretty light on the content (largely containing
# things like start-of-week information) and most of the "meat" of the data is
# contained in the main localedata file, e.g. "en.dat".
#
# Users may need to generate pages corresponding to locales that we don't
# have full localedata for, and until Babel supports fuzzy locales, we'll
# monkeypatch two Babel functions to provide partial support for fuzzy locales.
#
# With this monkeypatch, locales will be valid even if Babel doesn't have a
# localedata file matching a locale's full identifier, but locales will still
# fail with a ValueError if the user specifies a territory that does not exist.
# With this patch, a user can, however, specify an invalid language. Obviously,
# this patch should be removed when/if Babel adds support for fuzzy locales.
# Optionally, we may want to provide users with more control over whether a
# locale is valid or invalid, but we can revisit that later.

# See: https://github.com/grow/grow/issues/93


def fuzzy_load(name, merge_inherited=True):
    localedata._cache_lock.acquire()
    try:
        data = localedata._cache.get(name)
        if not data:
            # Load inherited data
            if name == 'root' or not merge_inherited:
                data = {}
            else:
                parts = name.split('_')
                if len(parts) == 1:
                    parent = 'root'
                else:
                    parent = '_'.join(parts[:-1])
                data = fuzzy_load(parent).copy()
            filename = os.path.join(localedata._dirname, '%s.dat' % name)
            try:
                fileobj = open(filename, 'rb')
                try:
                    if name != 'root' and merge_inherited:
                        localedata.merge(data, pickle.load(fileobj))
                    else:
                        data = pickle.load(fileobj)
                    localedata._cache[name] = data
                finally:
                    fileobj.close()
            except IOError:
                pass
        return data
    finally:
        localedata._cache_lock.release()


localedata.exists = lambda name: True
localedata.load = fuzzy_load
