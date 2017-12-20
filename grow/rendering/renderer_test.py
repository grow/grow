"""Tests for the renderer."""

import unittest
import mock
from grow.pods import pods
from grow import storage
from grow.rendering import render_controller
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

    def test_renderer_sans_threading(self):
        """Renders the docs without threading."""
        self.pod.router.add_all()
        routes = self.pod.router.routes
        self.render.rendered_docs(self.pod, routes, use_threading=False)

    @mock.patch.object(render_controller.RenderDocumentController, 'render')
    def test_render(self, mock_render):
        """Renders the docs with errors."""
        mock_render.side_effect = ValueError()

        self.pod.router.add_all()
        routes = self.pod.router.routes

        with self.assertRaises(renderer.RenderErrors):
            self.render.rendered_docs(self.pod, routes)


if __name__ == '__main__':
    unittest.main()
