import collections
import os
from protorpc import messages


class FileCountMessage(messages.Message):
  ext = messages.StringField(1)
  count = messages.IntegerField(2)


class StatsMessage(messages.Message):
  num_collections = messages.IntegerField(101)
  num_documents = messages.IntegerField(102)
  num_static_files = messages.IntegerField(103)
  num_files_per_type = messages.MessageField(FileCountMessage, 104, repeated=True)

  locales = messages.StringField(123, repeated=True)
  langs = messages.StringField(124, repeated=True)
  num_messages = messages.IntegerField(125)
  num_untranslated_messages = messages.IntegerField(126)


class Stats(object):

  def __init__(self, pod, paths_to_contents=None):
    self.pod = pod
    if paths_to_contents is None:
      paths_to_contents = pod.export()
    self.paths_to_contents = paths_to_contents

  def get_num_files_per_type(self):
    file_counts = collections.defaultdict(int)
    for path in self.paths_to_contents.keys():
      ext = os.path.splitext(path)[-1]
      file_counts[ext] += 1
    messages = []
    for ext, count in file_counts.iteritems():
      messages.append(FileCountMessage(ext=ext, count=count))
    return messages

  def to_message(self):
    message = StatsMessage()
    message.num_collections = len(self.pod.list_collections())
    message.locales = [str(locale) for locale in self.pod.list_locales()]
    message.langs = self.pod.get_translations().list_locales()
    message.num_files_per_type = self.get_num_files_per_type()
    return message
