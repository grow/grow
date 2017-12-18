"""Local deployment destination."""

import errno
import os
import shutil
from grow.deployments.destinations import base
from grow.pods import env
from grow.storage import file_storage
from protorpc import messages


class Config(messages.Message):
    out_dir = messages.StringField(1, default='')
    env = messages.MessageField(env.EnvConfig, 2)
    keep_control_dir = messages.BooleanField(3, default=False)
    before_deploy = messages.StringField(4, repeated=True)
    after_deploy = messages.StringField(5, repeated=True)
    control_dir = messages.StringField(6)


class LocalDestination(base.BaseDestination):
    KIND = 'local'
    Config = Config
    storage = file_storage.FileStorage

    def __str__(self):
        return os.path.abspath(os.path.join(self.out_dir))

    @property
    def out_dir(self):
        return os.path.expanduser(self.config.out_dir)

    def read_file(self, path):
        path = os.path.join(self.out_dir, path.lstrip('/'))
        return self.storage.read(path)

    def delete_file(self, path):
        out_path = os.path.join(self.out_dir, path.lstrip('/'))
        self.storage.delete(out_path)

    def write_file(self, rendered_doc):
        path = rendered_doc.path
        out_path = os.path.join(self.out_dir, path.lstrip('/'))
        if rendered_doc.file_path:
            dir_name = os.path.dirname(out_path)
            try:
                os.makedirs(dir_name)
            except OSError as exc:
                if exc.errno == errno.EEXIST:
                    pass
                else:
                    raise
            shutil.copyfile(rendered_doc.file_path, out_path)
        else:
            self.storage.write(out_path, rendered_doc.read())

    def prelaunch(self, dry_run=False):
        for command in self.config.before_deploy:
            self.command(command)
        super(LocalDestination, self).prelaunch(dry_run)

    def postlaunch(self, dry_run=False):
        if self.success:
            for command in self.config.after_deploy:
                self.command(command)
        super(LocalDestination, self).postlaunch(dry_run)
