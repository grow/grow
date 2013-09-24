from protorpc import messages


class PageMessage(messages.Message):
  name = messages.StringField(1)
  view = messages.StringField(4)
  staging_url = messages.StringField(5)
  path = messages.StringField(6)


class ControllerMessage(messages.Message):
  name = messages.StringField(1)
  page = messages.MessageField(PageMessage, 2)
