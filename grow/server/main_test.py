from grow.pods import pods
from grow.server import main
from grow.testing import testing
import unittest
import webapp2


class PodHandlerTestCase(unittest.TestCase):

  def test_request(self):
    self.dir_path = testing.create_test_pod_dir()
    pod = pods.Pod(self.dir_path)

    # Verify application errors when no pod root is set.
    app = main.CreateWSGIApplication()
    request = webapp2.Request.blank('/')
    response = request.get_response(app)
    self.assertEqual(response.status_int, 500)

    # When serving a pod, should 200.
    app = main.CreateWSGIApplication(pod)
    request = webapp2.Request.blank('/')
    response = request.get_response(app)
    self.assertEqual(response.status_int, 200)

    # Verify 404 is sent for blank page.
    request = webapp2.Request.blank('/dummy/page/')
    response = request.get_response(app)
    self.assertEqual(response.status_int, 404)


if __name__ == '__main__':
  unittest.main()
