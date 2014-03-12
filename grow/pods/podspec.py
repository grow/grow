# TODO(jeremydw): Implement.
from grow.pods import locales


class Podspec(object):

  def __init__(self, pod):
    self.pod = pod
    self.root_path = self.pod.yaml.get('flags', {}).get('root_path', '').lstrip('/').rstrip('/')
    self.default_locale = locales.Locale.parse(self.pod.yaml.get('localization', {}).get('default_locale', None))
    self.fields = self.pod.yaml

  def get_config(self):
    return self.pod.yaml

  def __getattr__(self, name):
    if name in self.fields:
      return self.fields[name]
    if '{}@'.format(name) in self.fields:
      return self.fields['{}@'.format(name)]
    return object.__getattribute__(self, name)
