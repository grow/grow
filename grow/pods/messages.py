from protorpc import messages
from .controllers import messages as controller_messages
from .collectionz import messages as collection_messages


class LocaleGroupMessage(messages.Message):
  group_name = messages.StringField(1)
  regions = messages.StringField(2, repeated=True)
  languages = messages.StringField(3, repeated=True)


class LocalesMessage(messages.Message):
  groups = messages.MessageField(LocaleGroupMessage, 1, repeated=True)


class MessageMessage(messages.Message):
  msgid = messages.StringField(1)
  msgstr = messages.StringField(2)
  description = messages.StringField(3)
  flags = messages.StringField(4, repeated=True)


class CatalogMessage(messages.Message):
  locale = messages.StringField(1)
  messages = messages.MessageField(MessageMessage, 2, repeated=True)


class CatalogsMessage(messages.Message):
  catalogs = messages.MessageField(CatalogMessage, 1, repeated=True)


class RoutesMessage(messages.Message):
  routes = messages.MessageField(controller_messages.RouteMessage, 1, repeated=True)


class FileMessage(messages.Message):
  pod_path = messages.StringField(1)
  content = messages.StringField(2)
  content_b64 = messages.BytesField(3)
  content_url = messages.StringField(4)
  mimetype = messages.StringField(5)


class PodMessage(messages.Message):
  collections = messages.MessageField(collection_messages.CollectionMessage, 2, repeated=True)
  files = messages.MessageField(FileMessage, 3, repeated=True)
  routes = messages.MessageField(RoutesMessage, 4)


class FileSearchMessage(messages.Message):
  prefix = messages.StringField(1)
  depth = messages.StringField(2)
