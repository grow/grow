"""Tests for the render controllers."""

import unittest

from grow import storage
from grow.pods import pods
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
        controller = render_controller.RenderController.from_route_info(self.pod, '/', route_info)
        self.assertIsInstance(controller, render_controller.RenderDocumentController)

        # Static Document
        route_info = router.RouteInfo('static')
        controller = render_controller.RenderController.from_route_info(self.pod, '/', route_info)
        self.assertIsInstance(controller, render_controller.RenderStaticDocumentController)

        # Sitemap
        route_info = router.RouteInfo('sitemap')
        controller = render_controller.RenderController.from_route_info(self.pod, '/', route_info)
        self.assertIsInstance(controller, render_controller.RenderSitemapController)

        # Random Unknown Kind
        route_info = router.RouteInfo('random')
        with self.assertRaises(render_controller.UnknownKindError):
            controller = render_controller.RenderController.from_route_info(
                self.pod, '/', route_info
            )

    def test_render_sitemap_single_vs_multi_locale(self):
        """Test that xhtml:link and xmlns:xhtml are omitted when no doc has multiple locales."""
        route_info = router.RouteInfo('sitemap')
        controller = render_controller.RenderController.from_route_info(
            self.pod, '/root/sitemap.xml', route_info
        )
        # Multi-locale test pod should include xmlns:xhtml and xhtml:link.
        rendered_multi = controller.render().read()
        self.assertIn('xmlns:xhtml="http://www.w3.org/1999/xhtml"', rendered_multi)
        self.assertIn('<xhtml:link rel="alternate"', rendered_multi)

        # Single-locale pod should omit xmlns:xhtml and xhtml:link.
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, 'podspec.yaml'), 'w', encoding='utf-8') as f:
                f.write('localization:\n  default_locale: en\n  locales:\n  - en\nsitemap:\n  enabled: true\n')
            os.makedirs(os.path.join(tmpdir, 'content', 'pages'))
            with open(os.path.join(tmpdir, 'content', 'pages', '_blueprint.yaml'), 'w', encoding='utf-8') as f:
                f.write('path: /{base}/\nview: /views/base.html\n')
            with open(os.path.join(tmpdir, 'content', 'pages', 'home.md'), 'w', encoding='utf-8') as f:
                f.write('---\n$title: Home\n---\nHello\n')
            os.makedirs(os.path.join(tmpdir, 'views'))
            with open(os.path.join(tmpdir, 'views', 'base.html'), 'w', encoding='utf-8') as f:
                f.write('{{doc.html|safe}}')
            single_pod = pods.Pod(tmpdir, storage=storage.FileStorage)
            single_controller = render_controller.RenderController.from_route_info(
                single_pod, '/sitemap.xml', route_info
            )
            rendered_single = single_controller.render().read()
            self.assertNotIn('xmlns:xhtml', rendered_single)
            self.assertNotIn('xhtml:link', rendered_single)
            self.assertIn('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', rendered_single)


if __name__ == '__main__':
    unittest.main()
