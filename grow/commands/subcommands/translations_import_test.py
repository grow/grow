from . import translations_import
from click import testing as click_testing
from grow.testing import testing
import os
import unittest


class ImportTranslationsTestCase(unittest.TestCase):

    def setUp(self):
        self.test_pod_dir = testing.create_test_pod_dir()
        self.runner = click_testing.CliRunner()

    def test_translations_import(self):
        func = translations_import.translations_import

        path = testing.get_testdata_dir()
        po_path_to_import = os.path.join(path, 'external', 'messages.de.po')
        args = [self.test_pod_dir, '--locale=de', '--source={}'.format(po_path_to_import)]
        result = self.runner.invoke(func, args, catch_exceptions=False)
        self.assertEqual(0, result.exit_code)

        po_path_to_import = os.path.join(path, 'external', 'messages.de.zip')
        args = [self.test_pod_dir, '--source={}'.format(po_path_to_import)]
        result = self.runner.invoke(func, args, catch_exceptions=False)
        self.assertEqual(0, result.exit_code)


if __name__ == '__main__':
    unittest.main()
