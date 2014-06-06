from . import base
from protorpc import messages
import errno
import os
import paramiko


class Config(messages.Message):
  host = messages.StringField(1)
  port = messages.StringField(2)
  root_dir = messages.StringField(3)


class ScpDeployment(base.BaseDeployment):
  NAME = 'scp'
  Config = Config
  threaded = False

  def __init__(self, *args, **kwargs):
    super(ScpDeployment, self).__init__(*args, **kwargs)
    self.ssh = paramiko.SSHClient()
    self.host = self.config.host
    self.port = self.config.port
    self.root_dir = self.config.root_dir

  def __str__(self):
    return 'scp://{}:{}'.format(self.config.host, self.config.root_dir)

  def prelaunch(self, dry_run=False):
    self.ssh.load_system_host_keys()
    self.ssh.connect(self.host, port=self.port)
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
