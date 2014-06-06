from protorpc import messages
from protorpc import message_types


class AuthorMessage(messages.Message):
  name = messages.StringField(1)
  email = messages.StringField(2)


class CommitMessage(messages.Message):
  sha = messages.StringField(1)
  author = messages.MessageField(AuthorMessage, 2)
  date = message_types.DateTimeField(3)
  message = messages.StringField(4)


class FileMessage(messages.Message):
  path = messages.StringField(1)
  sha = messages.StringField(2)
  modified = message_types.DateTimeField(3)
  modified_by = messages.MessageField(AuthorMessage, 4)


class IndexMessage(messages.Message):
  files = messages.MessageField(FileMessage, 1, repeated=True)
  created = message_types.DateTimeField(2)
  created_by = messages.MessageField(AuthorMessage, 3)
  modified = message_types.DateTimeField(4)
  modified_by = messages.MessageField(AuthorMessage, 5)
  commit = messages.MessageField(CommitMessage, 6)


class DiffMessage(messages.Message):
  adds = messages.MessageField(FileMessage, 1, repeated=True)
  edits = messages.MessageField(FileMessage, 2, repeated=True)
  deletes = messages.MessageField(FileMessage, 3, repeated=True)
  nochanges = messages.MessageField(FileMessage, 4, repeated=True)
  indexes = messages.MessageField(IndexMessage, 5, repeated=True)
