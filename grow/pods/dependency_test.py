from . import dependency
import unittest


class DependencyGraphTestCase(unittest.TestCase):

    def test_add_all(self):
        graph = dependency.DependencyGraph()
        graph.add_all({
            '/content/test.yaml': ['/content/test1.yaml'],
            '/content/test2.yaml': ['/content/test1.yaml'],
        })
        self.assertEqual(
            {
                '/content/test.yaml': ['/content/test1.yaml'],
                '/content/test2.yaml': ['/content/test1.yaml'],
            },
            graph.export())

    def test_add(self):
        graph = dependency.DependencyGraph()
        graph.add('/content/test.yaml', '/content/test1.yaml')
        graph.add('/content/test.yaml', '/content/test2.yaml')
        self.assertEqual(
            {
                '/content/test.yaml': [
                    '/content/test1.yaml',
                    '/content/test2.yaml',
                ],
            },
            graph.export())

    def test_add_none(self):
        graph = dependency.DependencyGraph()
        graph.add('/content/test.yaml', '/content/test1.yaml')
        graph.add('/content/test.yaml', None)
        graph.add(None, '/content/test1.yaml')
        self.assertEqual(
            {
                '/content/test.yaml': [
                    '/content/test1.yaml',
                ],
            },
            graph.export())

    def test_add_normalize(self):
        graph = dependency.DependencyGraph()
        graph.add('/content/test.yaml', 'content/test1.yaml')
        graph.add('content/test.yaml', '/content/test2.yaml')
        self.assertEqual(
            {
                '/content/test.yaml': [
                    '/content/test1.yaml',
                    '/content/test2.yaml',
                ],
            },
            graph.export())

    def test_export(self):
        graph = dependency.DependencyGraph()
        graph.add_references(
            '/content/test.yaml',
            set(['/content/test1.yaml']))
        self.assertEqual(
            {
                '/content/test.yaml': ['/content/test1.yaml'],
            },
            graph.export())

    def test_get_dependents(self):
        graph = dependency.DependencyGraph()
        graph.add_references(
            '/content/test.yaml',
            ['/content/test1.yaml'])
        self.assertEqual(
            set(['/content/test.yaml', '/content/test1.yaml']),
            graph.get_dependents('/content/test1.yaml'))

    def test_get_dependents_collection(self):
        graph = dependency.DependencyGraph()
        graph.add_references(
            '/content/test.yaml',
            ['/content/collection'])
        graph.add_references(
            '/content/test1.yaml',
            ['/content/collection/coll1.yaml'])
        self.assertEqual(
            set([
                '/content/test.yaml',
                '/content/test1.yaml',
                '/content/collection/coll1.yaml',
            ]),
            graph.get_dependents('/content/collection/coll1.yaml'))

    def test_get_dependents_self(self):
        graph = dependency.DependencyGraph()
        self.assertEqual(
            set(['/content/test.yaml']),
            graph.get_dependents('/content/test.yaml'))

    def test_get_dependencies(self):
        graph = dependency.DependencyGraph()
        graph.add_references(
            '/content/test.yaml',
            ['/content/test1.yaml', '/content/test2.yaml'])
        self.assertEqual(
            set(['/content/test1.yaml', '/content/test2.yaml']),
            graph.get_dependencies('/content/test.yaml'))

    def test_empty_dependents(self):
        graph = dependency.DependencyGraph()
        self.assertEqual(set(['/content/test1.yaml']),
                         graph.get_dependents('/content/test1.yaml'))

    def test_empty_dependencies(self):
        graph = dependency.DependencyGraph()
        self.assertEqual(set(), graph.get_dependencies('/content/test.yaml'))

    def test_match_dependents(self):
        graph = dependency.DependencyGraph()
        graph.add_references(
            '/content/ref.yaml',
            ['/content/test1.yaml'])
        graph.add_references(
            '/content/ref1.yaml',
            ['/content/test1.yaml'])
        graph.add_references(
            '/content/ref2.yaml',
            ['/content/test2.yaml'])
        self.assertEqual(
            set(['/content/ref.yaml']),
            graph.match_dependents('/content/ref.yaml'))
        self.assertEqual(
            set(['/content/ref1.yaml']),
            graph.match_dependents('/content/ref1.yaml'))
        self.assertEqual(
            set(['/content/ref2.yaml']),
            graph.match_dependents('/content/ref2.yaml'))
        self.assertEqual(
            set(['/content/test1.yaml', '/content/ref.yaml', '/content/ref1.yaml']),
            graph.match_dependents('/content/test1.yaml'))
        self.assertEqual(
            set(['/content/test1.yaml', '/content/test2.yaml',
                 '/content/ref.yaml', '/content/ref1.yaml', '/content/ref2.yaml']),
            graph.match_dependents('/content/test*.yaml'))

    def test_reset(self):
        graph = dependency.DependencyGraph()
        graph.add_references(
            '/content/test.yaml',
            ['/content/test1.yaml', '/content/test2.yaml'])
        self.assertEqual(
            set(['/content/test1.yaml', '/content/test2.yaml']),
            graph.get_dependencies('/content/test.yaml'))
        graph.reset()
        self.assertEqual(set(), graph.get_dependencies('/content/test.yaml'))


if __name__ == '__main__':
    unittest.main()
