"""Gerrit installer class."""

import subprocess
import urlparse
from grow.common import utils
from grow.sdk.installers import base_installer

KNOWN_GERRIT_HOSTS = (
    'googlesource.com',
)


class GerritInstaller(base_installer.BaseInstaller):
    """Gerrit installer."""

    KIND = 'gerrit'

    @property
    def should_run(self):
        """Should the installer run?"""
        gerrit_setting = self.config.get('gerrit', None)
        if gerrit_setting is not None:
            return gerrit_setting

        repo = utils.get_git_repo(self.pod.root)
        if repo is None:
            return False
        for remote in repo.remotes:
            url = remote.config_reader.get('url')
            result = urlparse.urlparse(url)
            if result.netloc.endswith(KNOWN_GERRIT_HOSTS):
                return True
        return False

    def install(self):
        """Install dependencies."""
        curl_command = (
            'curl -sLo '
            '`git rev-parse --git-dir`/hooks/commit-msg '
            'https://gerrit-review.googlesource.com/tools/hooks/commit-msg')
        process = subprocess.Popen(
            curl_command, **self.subprocess_args(shell=True))
        code = process.wait()
        if not code:
            chmod_command = 'chmod +x `git rev-parse --git-dir`/hooks/commit-msg'
            process = subprocess.Popen(
                chmod_command, **self.subprocess_args(shell=True))
            code = process.wait()
            if not code:
                return
            raise base_installer.InstallError(
                'There was an error running `{}`.'.format(chmod_command))
        raise base_installer.InstallError(
            'There was an error running `{}`.'.format(curl_command))
