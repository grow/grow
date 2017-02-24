import unittest

from . import document_fields
from . import pods
from . import storage
from grow.testing import testing


class DocumentFieldsTestCase(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)


if __name__ == '__main__':
    unittest.main()
