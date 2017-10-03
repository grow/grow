from . import base
from grow.common import utils
from grow.pods import env
from protorpc import messages
import errno
import os
try:
    import paramiko
except ImportError:
    # Unavailable on Google App Engine.
    # https://github.com/paramiko/paramiko/pull/334
    paramiko = None


class Config(messages.Message):
    host = messages.StringField(1)
    port = messages.IntegerField(2, default=22)
    root_dir = messages.StringField(3, default='')
    username = messages.StringField(4)
    env = messages.MessageField(env.EnvConfig, 5)
    keep_control_dir = messages.BooleanField(6, default=False)


class ScpDestination(base.BaseDestination):
    KIND = 'scp'
    Config = Config
    threaded = False

    def __init__(self, *args, **kwargs):
        super(ScpDestination, self).__init__(*args, **kwargs)
        if paramiko is None:
            raise utils.UnavailableError('SCP deployments are not available in this environment.')
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.host = self.config.host
        self.port = self.config.port
        self.root_dir = self.config.root_dir
        self.username = self.config.username

    def __str__(self):
        return 'scp://{}:{}'.format(self.config.host, self.config.root_dir)

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

    def write_file(self, rendered_doc):
        path = rendered_doc.path
        content = rendered_doc.read()
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
