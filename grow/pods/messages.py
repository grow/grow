from protorpc import messages


class Kind(messages.Enum):
    RENDERED = 1
    STATIC = 2
    SITEMAP = 3


class RouteMessage(messages.Message):
    path = messages.StringField(1)
    kind = messages.EnumField(Kind, 2)
    locale = messages.StringField(3)


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
    routes = messages.MessageField(RouteMessage, 1, repeated=True)


class FileMessage(messages.Message):
    pod_path = messages.StringField(1)
    content = messages.StringField(2)
    content_b64 = messages.BytesField(3)
    content_url = messages.StringField(4)
    mimetype = messages.StringField(5)


class PodMessage(messages.Message):
    collections = messages.MessageField(CollectionMessage, 2, repeated=True)
    files = messages.MessageField(FileMessage, 3, repeated=True)
    routes = messages.MessageField(RoutesMessage, 4)


class FileSearchMessage(messages.Message):
    prefix = messages.StringField(1)
    depth = messages.StringField(2)
