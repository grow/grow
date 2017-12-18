"""Tests for the render controllers."""

import unittest
from grow.pods import pods
from grow import storage
from grow.rendering import render_controller
from grow.routing import router
from grow.testing import testing


class RenderControllerTestCase(unittest.TestCase):
    """Test the render controller."""

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

    def test_render_factory(self):
        """Test that the kinds correspond to the correct classes."""

        # Document
        route_info = router.RouteInfo('doc')
        controller = render_controller.RenderController.from_route_info(
            self.pod, '/', route_info)
        self.assertIsInstance(
            controller, render_controller.RenderDocumentController)

        # Static Document
        route_info = router.RouteInfo('static')
        controller = render_controller.RenderController.from_route_info(
            self.pod, '/', route_info)
        self.assertIsInstance(
            controller, render_controller.RenderStaticDocumentController)

        # Sitemap
        route_info = router.RouteInfo('sitemap')
        controller = render_controller.RenderController.from_route_info(
            self.pod, '/', route_info)
        self.assertIsInstance(
            controller, render_controller.RenderSitemapController)

        # Random Unknown Kind
        route_info = router.RouteInfo('random')
        with self.assertRaises(render_controller.UnknownKindError):
            controller = render_controller.RenderController.from_route_info(
                self.pod, '/', route_info)


if __name__ == '__main__':
    unittest.main()
