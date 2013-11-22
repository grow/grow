class BaseDeployment(object):

  def deploy(self, pod, dry_run=False):
    raise NotImplementedError

  def is_capable(self):
    raise NotImplementedError

  def get_deployed_index(self):
    raise NotImplementedError
