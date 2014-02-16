from grow.server import main
from grow.server import handlers
import os
import unittest
import webapp2


class PodHandlerTestCase(unittest.TestCase):

  def test_request(self):
    # Verify application errors when no pod root is set.
    handlers.set_pod_root(None)
    request = webapp2.Request.blank('/')
    response = request.get_response(main.application)
    self.assertEqual(response.status_int, 500)

    # When serving a pod, should 200.
    root = os.path.join(os.path.dirname(__file__), '..', 'pods', 'testdata', 'pod')
    handlers.set_pod_root(root)
    request = webapp2.Request.blank('/')
    response = request.get_response(main.application)
    self.assertEqual(response.status_int, 200)

    # Verify 404 is sent for blank page.
    request = webapp2.Request.blank('/dummy/page/')
    response = request.get_response(main.application)
    self.assertEqual(response.status_int, 404)


if __name__ == '__main__':
  unittest.main()
