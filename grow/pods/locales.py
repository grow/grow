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
