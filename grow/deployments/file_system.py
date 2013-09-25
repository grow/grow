from grow.deployments import base


class FileSystemDeployment(base.BaseDeployment):

  def __init__(self, out_dir):
    self.out_dir = out_dir

  def deploy(self, pod):
    # TODO(jeremydw): Read manifest and takedown old content here.
    pod.dump(out_dir=self.out_dir)
