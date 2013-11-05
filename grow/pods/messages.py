from protorpc import messages
from grow.pods.blueprints import messages as blueprint_messages


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


class TranslationCatalogMessage(messages.Message):
  locale = messages.StringField(1)
  messages = messages.MessageField(MessageMessage, 2, repeated=True)


class TranslationsMessage(messages.Message):
  catalogs = messages.MessageField(TranslationCatalogMessage, 1, repeated=True)


class RouteMessage(messages.Message):
  path = messages.StringField(1)
  kind = messages.StringField(2)


class RoutesMessage(messages.Message):
  domains = messages.StringField(1, repeated=True)
  routes = messages.MessageField(RouteMessage, 2, repeated=True)


class FileMessage(messages.Message):
  pod_path = messages.StringField(1)
  content = messages.StringField(2)
  content_b64 = messages.BytesField(3)
  content_url = messages.StringField(4)
  mimetype = messages.StringField(5)


class PodMessage(messages.Message):
  changeset = messages.StringField(1)
  blueprints = messages.MessageField(blueprint_messages.BlueprintMessage, 2, repeated=True)
  files = messages.MessageField(FileMessage, 3, repeated=True)
  routes = messages.MessageField(RoutesMessage, 4)


class FileTransferMessage(messages.Message):
  pod_path = messages.StringField(1)
  content_b64 = messages.StringField(2)


class FileSearchMessage(messages.Message):
  prefix = messages.StringField(1)
  depth = messages.StringField(2)
