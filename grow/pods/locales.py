from grow.pods import errors
from grow.pods import messages



class Locales(object):

  def __init__(self, pod):
    self.pod = pod

  def get_regions(self, group_name='default'):
    try:
      return self.pod.yaml[group_name]['regions']
    except errors.PodConfigurationError:
      return []

  def get_languages(self, group_name='default'):
    try:
      return self.pod.yaml[group_name]['languages']
    except errors.PodConfigurationError:
      return []

  def to_message(self):
    message = messages.LocalesMessage()
    message.regions = self.get_regions()
    message.languages = self.get_languages()
    return message