from protorpc import messages


class DeploymentKind(messages.Enum):
  GOOGLE_STORAGE = 1
  GOOGLE_STORAGE_FROM_APP_ENGINE = 2
  AMAZON_S3 = 3
  GROW_CHANNEL = 4
  FILE_SYSTEM = 5


class Result(messages.Enum):
  PASS = 1
  FAIL = 2
  WARNING = 3


class TestResultMessage(messages.Message):
  result = messages.EnumField(Result, 1, default=Result.PASS)
  title = messages.StringField(2)
  text = messages.StringField(3)


class TestResultsMessage(messages.Message):
  test_results = messages.MessageField(TestResultMessage, 1, repeated=True)


###


class ZipConfig(messages.Message):
  pass


#class DestinationConfig(messages.Message):
#  google_storage = messages.MessageField(GoogleStorageConfig, 1)
#  scp = messages.MessageField(ScpConfig, 2)
#  zip = messages.MessageField(ZipConfig, 3)
