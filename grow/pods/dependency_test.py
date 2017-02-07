from . import dependency
from grow.testing import testing
import unittest


class DependencyGraphTestCase(unittest.TestCase):

    def test_get_all_dependencies(self):
        graph = dependency.DependencyGraph()
        graph.add_references(
            '/content/test.html',
            set(['/content/test1.html']))
        self.assertEqual(
            set(['/content/test.html', '/content/test1.html']),
            graph.get_dependents('/content/test1.html'))

    def test_get_dependents(self):
        graph = dependency.DependencyGraph()
        graph.add_references(
            '/content/test.html',
            set(['/content/test1.html']))
        self.assertEqual(
            set(['/content/test.html', '/content/test1.html']),
            graph.get_dependents('/content/test1.html'))

    def test_get_dependents_collection(self):
        graph = dependency.DependencyGraph()
        graph.add_references(
            '/content/test.html',
            set(['/content/collection']))
        graph.add_references(
            '/content/test1.html',
            set(['/content/collection/coll1.html']))
        self.assertEqual(
            set([
                '/content/test.html',
                '/content/test1.html',
                '/content/collection/coll1.html',
            ]),
            graph.get_dependents('/content/collection/coll1.html'))

    def test_get_dependents_self(self):
        graph = dependency.DependencyGraph()
        self.assertEqual(
            set(['/content/test.html']),
            graph.get_dependents('/content/test.html'))

    def test_get_dependencies(self):
        graph = dependency.DependencyGraph()
        graph.add_references(
            '/content/test.html',
            set(['/content/test1.html', '/content/test2.html']))
        self.assertEqual(
            set(['/content/test1.html', '/content/test2.html']),
            graph.get_dependencies('/content/test.html'))

    def test_empty_dependents(self):
        graph = dependency.DependencyGraph()
        self.assertEqual(set(['/content/test1.html']), graph.get_dependents('/content/test1.html'))

    def test_empty_dependencies(self):
        graph = dependency.DependencyGraph()
        self.assertEqual(set(), graph.get_dependencies('/content/test.html'))


class DependencyLogTestCase(unittest.TestCase):

    def test_add(self):
        stream = dependency.DependencyLog()
        stream.add('/content/test.html')
        self.assertEqual(set(['/content/test.html']), stream.read_all())

    def test_add_duplicate(self):
        stream = dependency.DependencyLog()
        stream.add('/content/test.html')
        stream.add('/content/test1.html')
        stream.add('/content/test.html')
        self.assertEqual(set(['/content/test.html', '/content/test1.html']), stream.read_all())

    def test_empty(self):
        stream = dependency.DependencyLog()
        self.assertEqual(set(), stream.read_all())


if __name__ == '__main__':
    unittest.main()
