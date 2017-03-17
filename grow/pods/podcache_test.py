from . import podcache
import unittest


class DependencyGraphTestCase(unittest.TestCase):

    def test_init(self):
        yaml = {
            'dependencies': {
                '/content/test': [
                    '/content/test1',
                    '/content/test2',
                ]
            }
        }
        cache = podcache.PodCache(yaml, None)

        self.assertEqual(
            {
                '/content/test': ['/content/test1', '/content/test2'],
            },
            cache.dependency_graph.export())

if __name__ == '__main__':
    unittest.main()
