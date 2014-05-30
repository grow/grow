from protorpc import messages


class DeploymentKind(messages.Enum):
  GOOGLE_STORAGE = 1
  GOOGLE_STORAGE_FROM_APP_ENGINE = 2
  AMAZON_S3 = 3
  GROW_CHANNEL = 4
  FILE_SYSTEM = 5


class TestResultMessage(messages.Message):
  passed = messages.BooleanField(1, default=True)
  name = messages.StringField(2)
  result = messages.StringField(3)


class TestResultsMessage(messages.Message):
  test_results = messages.MessageField(TestResultMessage, 1, repeated=True)
