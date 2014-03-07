# TODO(jeremydw): Implement.


class Podspec(object):

  def __init__(self, pod):
    self.pod = pod
    self.root_path = self.pod.yaml.get('flags', {}).get('root_path', '').lstrip('/').rstrip('/')
    self.default_locale = self.pod.yaml.get('localization', {}).get('default_locale', None)

  def get_config(self):
    return self.pod.yaml
