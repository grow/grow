"""Tests for the main grow development server."""

import unittest
import webob
from grow.pods import pods
from grow.server import main
from grow.testing import testing


class PodHandlerTestCase(unittest.TestCase):

    def test_request(self):
        dir_path = testing.create_test_pod_dir()
        pod = pods.Pod(dir_path)
        pod.router.add_all(use_cache=False)

        # When serving a pod, should 200.
        app = main.create_wsgi_app(pod, 'localhost', 8080)
        request = webob.Request.blank('/')
        response = request.get_response(app)
        self.assertEqual(200, response.status_int)

        # Verify 404 is sent for page not found.
        request = webob.Request.blank('/dummy/page/')
        response = request.get_response(app)
        self.assertEqual(404, response.status_int)

        # Verify 206 for partial content.
        headers = {'Range': 'bytes=0-4'}
        request = webob.Request.blank('/public/file.txt', headers=headers)
        response = request.get_response(app)
        self.assertEqual(206, response.status_int)
        self.assertEqual('bytes 0-4/13', response.headers['Content-Range'])
        self.assertEqual(b'Hello', response.body)

        headers = {'Range': 'bytes=5-13'}
        request = webob.Request.blank('/public/file.txt', headers=headers)
        response = request.get_response(app)
        self.assertEqual('bytes 5-12/13', response.headers['Content-Range'])
        self.assertEqual(b' World!\n', response.body)

        # Verify full response when headers omitted.
        request = webob.Request.blank('/public/file.txt')
        response = request.get_response(app)
        self.assertEqual(b'Hello World!\n', response.body)

        # Verify 304.
        url_path = '/public/file.txt'
        matched = pod.router.routes.match(url_path)
        controller = pod.router.get_render_controller(
            url_path, matched.value, params=matched.params)
        response_headers = controller.get_http_headers()
        headers = {'If-None-Match': response_headers['Last-Modified']}
        request = webob.Request.blank(url_path, headers=headers)
        response = request.get_response(app)
        self.assertEqual(304, response.status_int)
        self.assertEqual(b'', response.body)

        response = request.get_response(app)
        self.assertEqual(304, response.status_int)
        self.assertEqual(b'', response.body)

        # Verify sitemap on server.
        path = '/root/sitemap.xml'
        request = webob.Request.blank(path)
        response = request.get_response(app)
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/xml', response.headers['Content-Type'])

    def test_admin(self):
        dir_path = testing.create_test_pod_dir()
        pod = pods.Pod(dir_path)
        pod.router.add_all(use_cache=False)
        app = main.create_wsgi_app(pod, 'localhost', 8080)

        # Verify routes are served.
        request = webob.Request.blank('/_grow/routes')
        response = request.get_response(app)
        self.assertEqual(200, response.status_int)
        js_sentinel = b'<h2>Routes</h2>'
        self.assertIn(js_sentinel, response.body)

        request = webob.Request.blank('/_grow/ui/css/admin.min.css')
        response = request.get_response(app)
        self.assertEqual(200, response.status_int)

    def test_ui(self):
        dir_path = testing.create_test_pod_dir()
        pod = pods.Pod(dir_path)
        pod.router.add_all(use_cache=False)
        app = main.create_wsgi_app(pod, 'localhost', 8080)

        # Verify JS and CSS are served.
        request = webob.Request.blank('/_grow/ui/js/ui.min.js')
        response = request.get_response(app)
        self.assertEqual(200, response.status_int)
        js_sentinel = b'setAttribute("target","_blank")'
        self.assertIn(js_sentinel, response.body)

        request = webob.Request.blank('/_grow/ui/css/ui.min.css')
        response = request.get_response(app)
        self.assertEqual(200, response.status_int)
        css_sentinel = b'#grow'
        self.assertIn(css_sentinel, response.body)


if __name__ == '__main__':
    unittest.main()
