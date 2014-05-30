from protorpc import messages
from protorpc import message_types


class FileMessage(messages.Message):
  path = messages.StringField(1)
  sha = messages.StringField(2)
  modified = message_types.DateTimeField(3)
  modified_by = messages.StringField(4)


class DiffMessage(messages.Message):
  adds = messages.MessageField(FileMessage, 1, repeated=True)
  edits = messages.MessageField(FileMessage, 2, repeated=True)
  deletes = messages.MessageField(FileMessage, 3, repeated=True)
  nochanges = messages.MessageField(FileMessage, 4, repeated=True)


class IndexMessage(messages.Message):
  files = messages.MessageField(FileMessage, 1, repeated=True)
  created = message_types.DateTimeField(2)
  created_by = messages.StringField(3)
  modified = message_types.DateTimeField(4)
  modified_by = messages.StringField(5)
