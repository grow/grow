from grow.pods import pods
from grow.server import main
from grow.testing import testing
import unittest
import webapp2


class PodHandlerTestCase(unittest.TestCase):

    def test_request(self):
        self.dir_path = testing.create_test_pod_dir()
        pod = pods.Pod(self.dir_path)

        # When serving a pod, should 200.
        app = main.create_wsgi_app(pod)
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
        modified = 'Tue, 17 Nov 2015 15:17:06 GMT'
        headers = {'If-None-Match': modified}
        request = webapp2.Request.blank('/public/file.txt', headers=headers)
        response = request.get_response(app)
        self.assertEqual(304, response.status_int)
        self.assertEqual('', response.body)

        headers = {'If-Modified-Since': modified}
        response = request.get_response(app)
        self.assertEqual(304, response.status_int)
        self.assertEqual('', response.body)


if __name__ == '__main__':
    unittest.main()
