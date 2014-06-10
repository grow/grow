from grow.deployments import base
import errno
import os
import paramiko


class ScpDeployment(base.BaseDeployment):

  def __init__(self, **kwargs):
    self.ssh = paramiko.SSHClient()
    self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if 'username' in kwargs:
        self.username = kwargs['username']
    self.host = kwargs['host']
    if 'port' in kwargs:
        self.port = kwargs['port']
    else:
        self.port = 22
    if 'root_dir' in kwargs:
        self.root_dir = kwargs['root_dir']
    else:
        self.root_dir = ''



    # One SSH client cannot accept multiple connections, so
    # this deployment is not parallelized (for now).
    self.threaded = False

  def get_destination_address(self):
    return '{}:{}'.format(self.host, self.root_dir)

  def prelaunch(self, dry_run=False):
    self.ssh.load_system_host_keys()
#    if hasattr(self, 'username'):
    try:
        login = self.username
        self.ssh.connect(self.host, username=login, port=self.port)
    except AttributeError:
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
