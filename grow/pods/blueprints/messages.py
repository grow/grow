from protorpc import messages
from protorpc import message_types


class Format(messages.Enum):
  HTML = 1
  MARKDOWN = 2

extensions_to_formats = {
    '.md': Format.MARKDOWN,
    '.yaml': Format.HTML,
}


class Type(messages.Enum):
  STRING = 1
  TEXT = 2
  HTML = 3
  DATETIME = 4
  BOOLEAN = 5
  NUMBER = 6
  COLLECTION = 7


strings_to_types = {
    'String': Type.STRING,
    'Text': Type.TEXT,
    'Html': Type.HTML,
    'DateTime': Type.DATETIME,
    'Boolean': Type.BOOLEAN,
    'Number': Type.NUMBER,
    'Collection': Type.COLLECTION,
}


class FieldMessage(messages.Message):
  key = messages.StringField(1)
  name = messages.StringField(2)
  description = messages.StringField(3)
  type = messages.EnumField(Type, 4)
  repeated = messages.BooleanField(5)
  value = messages.StringField(6)


class BlueprintMessage(messages.Message):
  nickname = messages.StringField(1)
  num_documents = messages.IntegerField(2)
#  fields = messages.MessageField(FieldMessage, 2, repeated=True)


class UserMessage(messages.Message):
  name = messages.StringField(1)
  email = messages.StringField(2)


class DocumentMessage(messages.Message):
  slug = messages.StringField(1)
  pod_path = messages.StringField(11)
  body = messages.StringField(2)
  path = messages.StringField(3)
  order = messages.IntegerField(4)
  title = messages.StringField(5)
  title_nav = messages.StringField(6)
  subtitle = messages.StringField(7)
  published = message_types.DateTimeField(8)
  published_by = messages.MessageField(UserMessage, 9)
  categories = messages.StringField(10, repeated=True)
