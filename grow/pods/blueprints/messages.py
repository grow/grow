from protorpc import messages
from protorpc import message_types


class Format(messages.Enum):
  YAML = 1
  MARKDOWN = 2

extensions_to_formats = {
    '.md': Format.MARKDOWN,
    '.yaml': Format.YAML,
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
  doc_path = messages.StringField(1)  # posts
  num_documents = messages.IntegerField(2)
#  fields = messages.MessageField(FieldMessage, 2, repeated=True)


class UserMessage(messages.Message):
  name = messages.StringField(1)
  email = messages.StringField(2)


class BuiltInFieldsMessage(messages.Message):
  path = messages.StringField(1)
  view = messages.StringField(2)
  order = messages.IntegerField(3)
  title = messages.StringField(4)


class DocumentMessage(messages.Message):
  doc_path = messages.StringField(1)  # posts/slug.md
  builtins = messages.MessageField(BuiltInFieldsMessage, 2)
  fields = messages.StringField(3)
  body = messages.StringField(4)
  content = messages.StringField(5)
  html = messages.StringField(6)
