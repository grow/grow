import grow
from protorpc import messages


class CustomPreprocessor(grow.Preprocessor):
    KIND = 'custom_preprocessor'

    class Config(messages.Message):
        value = messages.StringField(1)

    def run(self, **kwargs):
        # To allow the test to check the result
        self.pod._custom_preprocessor_value = self.config.value
