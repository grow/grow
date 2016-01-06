from . import local
import unittest


class LocalDestinationTestCase(unittest.TestCase):

    def test_out_dir(self):
        config = local.Config(out_dir='~/test/')
        destination = local.LocalDestination(config)
        # Weakly verify out_dir is expanded.
        self.assertNotIn('~', destination.out_dir)


if __name__ == '__main__':
    unittest.main()
