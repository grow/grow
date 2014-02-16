from grow.deployments import base
import os


class FileSystemDeployment(base.BaseDeployment):

  def get_destination_address(self):
    return self.out_dir

  def set_params(self, storage, out_dir):
    self.out_dir = out_dir
    self.storage = storage

  def read_file(self, path):
    path = os.path.join(self.out_dir, path.lstrip('/'))
    return self.storage.read(path)

  def delete_file(self, path):
    out_path = os.path.join(self.out_dir, path.lstrip('/'))
    self.storage.delete(out_path)

  def write_file(self, path, content):
    if isinstance(content, unicode):
      content = content.encode('utf-8')
    out_path = os.path.join(self.out_dir, path.lstrip('/'))
    self.storage.write(out_path, content)
