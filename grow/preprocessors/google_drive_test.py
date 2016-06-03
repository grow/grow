from . import google_drive
from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import unittest


class GoogleSheetsPreprocessorTest(unittest.TestCase):

    def test_convert_rows_to_mapping(self):
        rows = [
            ['# Comment', True],
            ['foo.bar.baz', True],
            ['foo.bar.bam', True],
            ['foo.baz', True],
            ['qaz', True],
        ]
        expected = {
            'foo': {
                'bar': {
                    'baz': True,
                    'bam': True,
                },
                'baz': True,
            },
            'qaz': True,
        }
        preprocessor = google_drive.GoogleSheetsPreprocessor
        result = preprocessor._convert_rows_to_mapping(rows)
        self.assertDictEqual(expected, result)


if __name__ == '__main__':
    unittest.main()
