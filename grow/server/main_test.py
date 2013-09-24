from grow.server import main
from grow.server import handlers
import os
import unittest
import webapp2


class PodHandlerTestCase(unittest.TestCase):

  def test_request(self):
    # By default, application should match no routes without any pods.
    handlers.set_single_pod_root(None)
    request = webapp2.Request.blank('/')
    response = request.get_response(main.application)
    self.assertEqual(response.status_int, 404)

    # When serving a pod, should 200.
    root = os.path.join(os.path.dirname(__file__), '..', 'pods', 'testdata', 'pod')
    handlers.set_single_pod_root(root)
    request = webapp2.Request.blank('/')
    response = request.get_response(main.application)
    self.assertEqual(response.status_int, 200)


if __name__ == '__main__':
  unittest.main()
