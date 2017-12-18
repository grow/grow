from . import translations_filter
from click import testing as click_testing
from grow.testing import testing
import unittest


class FilterTestCase(unittest.TestCase):

    def setUp(self):
        self.test_pod_dir = testing.create_test_pod_dir()
        self.runner = click_testing.CliRunner()

    def test_filter(self):
        args = [self.test_pod_dir, '-o', 'missing.po']
        result = self.runner.invoke(
            translations_filter.translations_filter, args, catch_exceptions=False)
        self.assertEqual(0, result.exit_code)
        args = [self.test_pod_dir, '--locale=de', '-o', 'missing.po']
        result = self.runner.invoke(
            translations_filter.translations_filter, args, catch_exceptions=False)
        self.assertEqual(0, result.exit_code)
        args = [self.test_pod_dir, '--out_dir=missing-dir', '--localized']
        result = self.runner.invoke(
            translations_filter.translations_filter, args, catch_exceptions=False)
        self.assertEqual(0, result.exit_code)


if __name__ == '__main__':
    unittest.main()
