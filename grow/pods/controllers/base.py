class BaseController(object):

  def __init__(self, _pod):
    self.pod = _pod
    self.route_params = {}

  def set_route_params(self, route_params):
    self.route_params = route_params

  def validate_route_params(self, route_params):
    pass

  def get_route_params(self):
    return self.route_params

  def get_mimetype(self):
    raise NotImplementedError

  def get_http_headers(self):
    return {
        'Content-Type': self.mimetype,
    }
