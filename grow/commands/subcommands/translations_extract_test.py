import unittest

from click import testing as click_testing

from grow.testing import testing

from . import translations_extract


class ExtractTestCase(unittest.TestCase):

    def setUp(self):
        self.test_pod_dir = testing.create_test_pod_dir()
        self.runner = click_testing.CliRunner()

    def test_extract(self):
        args = [self.test_pod_dir]
        result = self.runner.invoke(
            translations_extract.translations_extract, args, catch_exceptions=False)
        self.assertEqual(0, result.exit_code)


if __name__ == '__main__':
    unittest.main()
