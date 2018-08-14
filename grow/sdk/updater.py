# coding: utf8
"""Grow update class."""

import os
import subprocess
import sys
import requests
import semantic_version
from grow.common import colors
from grow.common import decorators
from grow.common import logger as grow_logger
from grow.common import rc_config
from grow.common import system


RELEASES_API = 'https://api.github.com/repos/grow/grow/releases'
TAGS_URL_FORMAT = 'https://github.com/grow/grow/releases/tag/{}'
INSTALLER_COMMAND = ('/usr/bin/python -c "$(curl -fsSL '
                     'https://raw.github.com/grow/grow/master/install.py)"')


class Error(Exception):
    """Base error for updaters."""
    pass


class LatestVersionCheckError(Error):
    """Error checking for the latest version."""
    pass


class Updater(object):
    """Grow updater for dependencies."""

    def __init__(self, required_spec=None, logger=None):
        self.logger = logger or grow_logger.LOGGER
        if required_spec:
            self.required_spec = semantic_version.Spec(required_spec)
        else:
            self.required_spec = None

    @property
    def current_version(self):
        """Current version of grow."""
        return system.VERSION

    @decorators.MemoizeProperty
    def latest_version(self):  # pylint: disable=no-self-use
        """Latest version available for current platform."""
        try:
            releases = requests.get(RELEASES_API).json()
            if 'message' in releases:
                text = 'Error while downloading release information: {}'.format(
                    releases['message'])
                self.logger.error(colors.stylize(text, colors.ERROR))
                raise LatestVersionCheckError(str(text))
            for release in releases:
                if release['prerelease']:
                    continue
                for each_asset in release['assets']:
                    if system.PLATFORM in each_asset.get('name', '').lower():
                        return release['tag_name']
            raise LatestVersionCheckError(
                'Unable to find a release for {} platform.'.format(system.PLATFORM))
        except LatestVersionCheckError:
            raise
        except Exception as err:
            self.logger.exception(colors.stylize(str(err), colors.ERROR))
            text = 'Unable to check for the latest version: {}'.format(str(err))
            self.logger.error(colors.stylize(text, colors.ERROR))
            raise LatestVersionCheckError(str(err))

    def check_for_updates(self, auto_update_prompt=False):
        """Check for updates to the sdk."""
        grow_rc_config = rc_config.RC_CONFIG

        # Rate limited update checks.
        if not grow_rc_config.needs_update_check:
            return

        try:
            sem_current = semantic_version.Version(self.current_version)
            sem_latest = semantic_version.Version(self.latest_version)
            # Mark that we have performed a check for the update.
            grow_rc_config.reset_update_check()
            grow_rc_config.write()
        except LatestVersionCheckError:
            return

        if sem_latest <= sem_current:
            return

        url = TAGS_URL_FORMAT.format(self.latest_version)
        self.logger.info('')
        self.logger.info('  Please update to the newest version of the Grow SDK.')
        self.logger.info('  Release notes: {}'.format(url))
        self.logger.info('  Your version: {}, latest version: {}'.format(
            colors.stylize(str(sem_current), colors.EMPHASIS),
            colors.stylize(str(sem_latest), colors.EMPHASIS)))

        if system.is_packaged_app() and auto_update_prompt:
            use_auto_update = grow_rc_config.get('update.always', False)

            if use_auto_update:
                self.logger.info('  > Auto-updating to version: {}'.format(
                    colors.stylize(str(sem_latest), colors.HIGHLIGHT)))
            else:  # pragma: no cover
                choice = raw_input(
                    'Auto update now? [Y]es / [n]o / [a]lways: ').strip().lower()
                if choice not in ('y', 'a', ''):
                    return
                if choice == 'a':
                    grow_rc_config.set('update.always', True)
                    grow_rc_config.write()

            if subprocess.call(INSTALLER_COMMAND, shell=True) == 0:
                self.logger.info('Restarting...')
                try:
                    # Restart on successful install.
                    os.execl(sys.argv[0], *sys.argv)
                except OSError:
                    self.logger.info(
                        'Unable to restart. Please manually restart grow.')
                    sys.exit(-1)
            else:
                text = (
                    'In-place update failed. Update manually or use:\n'
                    '  curl https://install.grow.io | bash')
                self.logger.error(text)
                sys.exit(-1)
        else:
            # pylint: disable=logging-not-lazy
            self.logger.info('  Update using: ' +
                             colors.stylize('pip install --upgrade grow', colors.CAUTION))
        self.logger.info('')

    def verify_required_spec(self):
        """Verify that the required version for the pod is met."""
        if self.required_spec is None:
            return
        sem_current = semantic_version.Version(self.current_version)
        if sem_current not in self.required_spec:
            text = 'ERROR! Pod requires Grow version: {}'.format(
                self.required_spec)
            self.logger.error(colors.stylize(text, colors.ERROR))
            raise LatestVersionCheckError(text)
