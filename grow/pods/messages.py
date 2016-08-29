from protorpc import messages


class Kind(messages.Enum):
    RENDERED = 1
    STATIC = 2
    SITEMAP = 3


class Formatters(messages.Message):
    locale = messages.StringField(1, repeated=True)
    filename = messages.StringField(2, repeated=True)


class Route(messages.Message):
    path_format = messages.StringField(1)
    pod_path = messages.StringField(2)
    formatters = messages.MessageField(Formatters, 3)


class StaticLocalization(messages.Message):
    static_dir = messages.StringField(1)
    serve_at = messages.StringField(2)
    formatters = messages.MessageField(Formatters, 4)


class StaticRoute(messages.Message):
    path_format = messages.StringField(1)
    pod_path_format = messages.StringField(2)
    localized = messages.BooleanField(3)
    localization = messages.MessageField(StaticLocalization, 4)
    fingerprinted = messages.BooleanField(5)
    formatters = messages.MessageField(Formatters, 6)


class SitemapRoute(messages.Message):
    path_format = messages.StringField(1)
    formatters = messages.MessageField(Formatters, 2)


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


class FileMessage(messages.Message):
    pod_path = messages.StringField(1)
    content = messages.StringField(2)
    content_b64 = messages.BytesField(3)
    content_url = messages.StringField(4)
    mimetype = messages.StringField(5)


class PodMessage(messages.Message):
    collections = messages.MessageField(CollectionMessage, 2, repeated=True)
    files = messages.MessageField(FileMessage, 3, repeated=True)


class FileSearchMessage(messages.Message):
    prefix = messages.StringField(1)
    depth = messages.StringField(2)
