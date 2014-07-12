from protorpc import messages


class Kind(messages.Enum):
  RENDERED = 1
  STATIC = 2


class RouteMessage(messages.Message):
  path = messages.StringField(1)
  kind = messages.EnumField(Kind, 2)
  locale = messages.StringField(3)
