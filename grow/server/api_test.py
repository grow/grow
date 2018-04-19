"""Api Handler tests."""

import unittest
import webapp2
from grow.pods import pods
from grow.server import main
from grow.testing import testing


class ApiHandlerTestCase(unittest.TestCase):
    """Tests for the server API Handler."""

    def test_request(self):
        """Test that api requests can be completed correctly."""
        dir_path = testing.create_test_pod_dir()
        pod = pods.Pod(dir_path, use_reroute=True)
        pod.router.add_all()

        # When serving a pod, should 200.
        app = main.create_wsgi_app(pod, 'localhost', 8080)
        request = webapp2.Request.blank(
            '/_grow/api/editor/content?pod_path=/content/pages/home.yaml')
        response = request.get_response(app)
        self.assertEqual(200, response.status_int)


if __name__ == '__main__':
    unittest.main()
