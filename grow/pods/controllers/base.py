class BaseController(object):

  def __init__(self, pod):
    self.pod = pod
    self.route_params = {}

  def set_route_params(self, route_params):
    self.route_params = route_params

  def get_mimetype(self):
    raise NotImplementedError

  def get_http_headers(self):
    return {
        'Content-Type': self.mimetype,
    }
