from grow.deployments import base
import errno
import os
import paramiko


class ScpDeployment(base.BaseDeployment):

  def __init__(self, **kwargs):
    self.ssh = paramiko.SSHClient()
    self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    self.host = kwargs.pop('host') # (Raises an error if "host" is not provided.)
    self.username = kwargs.pop('username', None)
    self.port = kwargs.pop('port', 22)
    self.root_dir = kwargs.pop('root_dir', '')

    # One SSH client cannot accept multiple connections, so
    # this deployment is not parallelized (for now).
    self.threaded = False

  def get_destination_address(self):
    return '{}:{}'.format(self.host, self.root_dir)

  def prelaunch(self, dry_run=False):
    self.ssh.load_system_host_keys()
    self.ssh.connect(self.host, username=self.username, port=self.port)
    self.sftp = self.ssh.open_sftp()

  def postlaunch(self, dry_run=False):
    self.sftp.close()
    self.ssh.close()

  def read_file(self, path):
    path = os.path.join(self.root_dir, path.lstrip('/'))
    fp = self.sftp.open(path)
    content = fp.read()
    fp.close()
    return content

  def delete_file(self, path):
    path = os.path.join(self.root_dir, path.lstrip('/'))
    self.sftp.remove(path)

  def write_file(self, path, content):
    if isinstance(content, unicode):
      content = content.encode('utf-8')
    path = os.path.join(self.root_dir, path.lstrip('/'))
    self._mkdirs(os.path.dirname(path))
    fp = self.sftp.open(path, 'w')
    fp.write(content)
    fp.close()
    return content

  def _mkdirs(self, path):
    """Recursively creates directories."""
    base = ''
    for part in path.split('/'):
      base += part + '/'
      try:
        self.sftp.lstat(base)
      except IOError, e:
        if e.errno == errno.ENOENT:
          self.sftp.mkdir(base)
