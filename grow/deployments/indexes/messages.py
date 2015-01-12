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
  has_unstaged_changes = messages.BooleanField(5)


class FileMessage(messages.Message):
  path = messages.StringField(1)
  sha = messages.StringField(2)
  deployed = message_types.DateTimeField(3)
  deployed_by = messages.MessageField(AuthorMessage, 4)
  action = messages.StringField(5)


class IndexMessage(messages.Message):
  files = messages.MessageField(FileMessage, 1, repeated=True)
  deployed = message_types.DateTimeField(4)
  deployed_by = messages.MessageField(AuthorMessage, 5)
  commit = messages.MessageField(CommitMessage, 6)


class WhatChangedMessage(messages.Message):
  commit = messages.MessageField(CommitMessage, 1)
  files = messages.MessageField(FileMessage, 2, repeated=True)


class DiffMessage(messages.Message):
  adds = messages.MessageField(FileMessage, 1, repeated=True)
  edits = messages.MessageField(FileMessage, 2, repeated=True)
  deletes = messages.MessageField(FileMessage, 3, repeated=True)
  nochanges = messages.MessageField(FileMessage, 4, repeated=True)
  indexes = messages.MessageField(IndexMessage, 5, repeated=True)
  what_changed = messages.StringField(6)
