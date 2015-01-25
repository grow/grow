import babel
import re
from grow.pods import errors
from grow.pods import messages



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

  def __hash__(self):
    return hash(str(self))

  def __eq__(self, other):
    if isinstance(other, basestring):
      return str(self).lower() == other.lower()
    return super(Locale, self).__eq__(other)

  @classmethod
  def parse_codes(cls, codes):
    return [cls.parse(code) for code in codes]

  @property
  def is_rtl(self):
    return Locale.RTL_REGEX.match(self.language)

  @property
  def direction(self):
    return 'rtl' if self.is_rtl else 'ltr'

  def set_alias(self, pod):
    locale = str(self).lower()
    podspec = pod.get_podspec()
    config = podspec.get_config()
    if 'localization' in config and 'aliases' in config['localization']:
      aliases = config['localization']['aliases']
      for custom_locale, babel_locale in aliases.iteritems():
        locale = locale.replace(babel_locale, custom_locale)
    self._alias = locale

  @property
  def alias(self):
    return self._alias

  @alias.setter
  def alias(self, alias):
    self._alias = alias
