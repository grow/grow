from protorpc import messages


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
