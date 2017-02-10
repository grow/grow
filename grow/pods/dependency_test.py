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
        self.assertEqual(set(['/content/test1.yaml']), graph.get_dependents('/content/test1.yaml'))

    def test_empty_dependencies(self):
        graph = dependency.DependencyGraph()
        self.assertEqual(set(), graph.get_dependencies('/content/test.yaml'))

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


class DependencyLogTestCase(unittest.TestCase):

    def test_add(self):
        log = dependency.DependencyLog()
        log.add('/content/test.yaml')
        self.assertEqual(set(['/content/test.yaml']), log.read_all())

    def test_add_duplicate(self):
        log = dependency.DependencyLog()
        log.add('/content/test.yaml')
        log.add('/content/test1.yaml')
        log.add('/content/test.yaml')
        self.assertEqual(set(['/content/test.yaml', '/content/test1.yaml']), log.read_all())

    def test_empty(self):
        log = dependency.DependencyLog()
        self.assertEqual(set(), log.read_all())


if __name__ == '__main__':
    unittest.main()
