class BaseDeployment(object):

  def upload_pod(self, pod):
    """Uploads a pod but does not deploy it."""
    raise NotImplementedError

  def dump(self, pod):
    """Deploys a static version of the pod."""
    raise NotImplementedError

  def deploy_pod(self, pod):
    """Deploys a pod, making it serve live traffic."""
    raise NotImplementedError

  def takedown_pod(self, pod):
    raise NotImplementedError

  def get_manifest(self):
    raise NotImplementedError
