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

