"""Base installer class."""

import os
from grow.sdk import sdk_utils


class Error(Exception):
    """Base error for installers."""
    pass


class MissingPrerequisiteError(Error):
    """Installer is missing a prerequisite."""

    def __init__(self, message, install_commands=None):
        super(MissingPrerequisiteError, self).__init__(message)
        self.install_commands = install_commands


class InstallError(Error):
    """Installer had a error during install."""
    pass


class BaseInstaller(object):
    """Base class for grow installers."""

    KIND = None

    def __init__(self, pod, config):
        self.pod = pod
        self.config = config

    @property
    def post_install_messages(self):
        """List of messages to display after installing."""
        return ['Finished: {}'.format(self.KIND)]

    @property
    def should_run(self):
        """Should the installer run?"""
        return True

    def check_prerequisites(self):
        """Check if required prerequisites are installed or available."""
        pass

    def install(self):
        """Run the installer."""
        raise NotImplementedError()

    def subprocess_args(self, shell=False):
        """Arguments for running subprocess commands."""
        env = os.environ.copy()
        node_modules_path = os.path.join(self.pod.root, 'node_modules', '.bin')
        env['PATH'] = str(env['PATH'] + os.path.pathsep + node_modules_path)
        if self.pod.env and self.pod.env.name:
            env['GROW_ENVIRONMENT_NAME'] = self.pod.env.name
        args = {
            'cwd': self.pod.root,
            'env': env,
        }
        if shell or sdk_utils.PLATFORM == 'win':
            args['shell'] = True
        return args
