from grow.deployments import base


class FileSystemDeployment(base.BaseDeployment):

  def __init__(self, out_dir):
    self.out_dir = out_dir

  def dump(self, pod):
    pod.dump(out_dir=self.out_dir)
