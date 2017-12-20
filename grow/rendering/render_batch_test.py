"""Tests for the render batch."""

import unittest
from grow.pods import pods
from grow import storage
from grow.rendering import render_batch
from grow.rendering import renderer
from grow.testing import testing


class RendererTestCase(unittest.TestCase):
    """Test the renderer."""

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(
            self.dir_path, storage=storage.FileStorage, use_reroute=True)
        self.batches = render_batch.RenderBatches(
            self.pod.render_pool, self.pod.profile)

    def test_render_batches(self):
        """Renders the docs without errors."""
        self.pod.router.add_all()

        routes = self.pod.router.routes
        for controller in renderer.Renderer.controller_generator(self.pod, routes):
            self.batches.add(controller)

        self.assertEqual(len(routes), len(self.batches))

    def test_render_batches_batch_size(self):
        """Breaks up the rendering into specific sized batches."""
        self.pod.router.add_all()

        # Set a lower max batch size for tests.
        self.batches.batch_size = 3

        routes = self.pod.router.routes
        for controller in renderer.Renderer.controller_generator(self.pod, routes):
            self.batches.add(controller)

        self.assertEqual(len(routes), len(self.batches))

    def test_render_batch_not_started(self):
        """Breaks up the rendering into max sized batches."""
        batch = render_batch.RenderLocaleBatch(None, None)
        with self.assertRaises(render_batch.RenderNotStartedError):
            batch.render_finish()


if __name__ == '__main__':
    unittest.main()
