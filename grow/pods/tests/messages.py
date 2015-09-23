from protorpc import messages


class Status(messages.Enum):
  PASS = 1
  FAIL = 2
  WARN = 3


class RegExTestMessage(messages.Message):
  text = messages.StringField(1)
  status = messages.EnumField(Status, 2, default=Status.PASS)
  regex = messages.StringField(3)


class SnippetMessage(messages.Message):
  line_num = messages.IntegerField(1)
  lines = messages.StringField(2, repeated=True)


class TestResultMessage(messages.Message):
  status = messages.EnumField(Status, 1, default=Status.PASS)
  text = messages.StringField(2)
  snippet = messages.MessageField(SnippetMessage, 4)
  path = messages.StringField(5)


class TestResultsMessage(messages.Message):
  title = messages.StringField(1)
  passes = messages.MessageField(TestResultMessage, 2, repeated=True)
  fails = messages.MessageField(TestResultMessage, 3, repeated=True)
  warnings = messages.MessageField(TestResultMessage, 4, repeated=True)
