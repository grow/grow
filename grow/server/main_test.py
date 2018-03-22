from grow.pods import pods
from grow.server import main
from grow.testing import testing
import unittest
import webapp2


class PodHandlerTestCase(unittest.TestCase):

    def test_request(self):
        dir_path = testing.create_test_pod_dir()
        pod = pods.Pod(dir_path, use_reroute=True)
        pod.router.add_all()

        # When serving a pod, should 200.
        app = main.create_wsgi_app(pod, 'localhost', 8080)
        request = webapp2.Request.blank('/')
        response = request.get_response(app)
        self.assertEqual(200, response.status_int)

        # Verify 404 is sent for page not found.
        request = webapp2.Request.blank('/dummy/page/')
        response = request.get_response(app)
        self.assertEqual(404, response.status_int)

        # Verify 206 for partial content.
        headers = {'Range': 'bytes=0-4'}
        request = webapp2.Request.blank('/public/file.txt', headers=headers)
        response = request.get_response(app)
        self.assertEqual(206, response.status_int)
        self.assertEqual('bytes 0-4/13', response.headers['Content-Range'])
        self.assertEqual('Hello', response.body)

        headers = {'Range': 'bytes=5-13'}
        request = webapp2.Request.blank('/public/file.txt', headers=headers)
        response = request.get_response(app)
        self.assertEqual('bytes 5-12/13', response.headers['Content-Range'])
        self.assertEqual(' World!\n', response.body)

        # Verify full response when headers omitted.
        request = webapp2.Request.blank('/public/file.txt')
        response = request.get_response(app)
        self.assertEqual('Hello World!\n', response.body)

        # Verify 304.
        url_path = '/public/file.txt'
        matched = pod.router.routes.match(url_path)
        controller = pod.router.get_render_controller(
            url_path, matched.value, params=matched.params)
        response_headers = controller.get_http_headers()
        headers = {'If-None-Match': response_headers['Last-Modified']}
        request = webapp2.Request.blank(url_path, headers=headers)
        response = request.get_response(app)
        self.assertEqual(304, response.status_int)
        self.assertEqual('', response.body)

        response = request.get_response(app)
        self.assertEqual(304, response.status_int)
        self.assertEqual('', response.body)

        # Verify sitemap on server.
        path = '/sitemap.xml'
        request = webapp2.Request.blank(path)
        response = request.get_response(app)
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/xml', response.headers['Content-Type'])

    def test_admin(self):
        dir_path = testing.create_test_pod_dir()
        pod = pods.Pod(dir_path, use_reroute=True)
        pod.router.add_all()
        app = main.create_wsgi_app(pod, 'localhost', 8080)

        # Verify routes are served.
        request = webapp2.Request.blank('/_grow/routes')
        response = request.get_response(app)
        self.assertEqual(200, response.status_int)
        js_sentinel = '<h2>Routes</h2>'
        self.assertIn(js_sentinel, response.body)

        request = webapp2.Request.blank('/_grow/ui/css/admin.min.css')
        response = request.get_response(app)
        self.assertEqual(200, response.status_int)

    def test_editor(self):
        dir_path = testing.create_test_pod_dir()
        pod = pods.Pod(dir_path, use_reroute=True)
        pod.router.add_all()
        app = main.create_wsgi_app(pod, 'localhost', 8080)

        # Verify routes are served.
        request = webapp2.Request.blank('/_grow/editor')
        response = request.get_response(app)
        self.assertEqual(200, response.status_int)
        js_sentinel = 'front_matter'
        self.assertIn(js_sentinel, response.body)

        request = webapp2.Request.blank('/_grow/ui/css/editor.min.css')
        response = request.get_response(app)
        self.assertEqual(200, response.status_int)

    def test_ui(self):
        dir_path = testing.create_test_pod_dir()
        pod = pods.Pod(dir_path, use_reroute=True)
        pod.router.add_all()
        app = main.create_wsgi_app(pod, 'localhost', 8080)

        # Verify JS and CSS are served.
        request = webapp2.Request.blank('/_grow/ui/js/ui.min.js')
        response = request.get_response(app)
        self.assertEqual(200, response.status_int)
        js_sentinel = 'function(modules)'
        self.assertIn(js_sentinel, response.body)

        request = webapp2.Request.blank('/_grow/ui/css/ui.min.css')
        response = request.get_response(app)
        self.assertEqual(200, response.status_int)
        css_sentinel = '#grow'
        self.assertIn(css_sentinel, response.body)


if __name__ == '__main__':
    unittest.main()
