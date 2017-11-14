"""Tests for the renderer."""

import unittest
from grow.pods import pods
from grow.pods import storage
from grow.rendering import renderer
from grow.testing import testing


class RendererTestCase(unittest.TestCase):
    """Test the renderer."""

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage, use_reroute=True)
        self.render = renderer.Renderer()

    def test_renderer(self):
        """Renders the docs without errors."""
        self.pod.router.add_all()
        routes = self.pod.router.routes
        self.render.rendered_docs(self.pod, routes)


if __name__ == '__main__':
    unittest.main()
