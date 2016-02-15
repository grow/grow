from grow.pods.preprocessors import base
from protorpc import messages


class CustomPreprocessor(base.BasePreprocessor):
    KIND = 'custom_preprocessor'

    class Config(messages.Message):
        value = messages.StringField(1)

    def run(self):
        # To allow the test to check the result
        self.pod._custom_preprocessor_value = self.config.value
