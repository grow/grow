from protorpc import messages


class Format(messages.Enum):
  YAML = 1
  MARKDOWN = 2
  HTML = 3

extensions_to_formats = {
    '.html': Format.HTML,
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


class CollectionMessage(messages.Message):
  collection_path = messages.StringField(1)  # posts
  num_documents = messages.IntegerField(2)
  title = messages.StringField(3)
  fields = messages.StringField(4)  # JSON fields
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
  basename = messages.StringField(2)
  collection_path = messages.StringField(3)
  fields = messages.StringField(5)  # JSON fields
  body = messages.StringField(6)
  content = messages.StringField(7)
  html = messages.StringField(8)
  serving_path = messages.StringField(9)
  pod_path = messages.StringField(10)
