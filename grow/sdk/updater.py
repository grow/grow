# coding: utf8
"""Grow update class."""

import logging
import os
import subprocess
import sys
import requests
import semantic_version
from grow.common import colors
from grow.common import config
from grow.common import rc_config
from grow.common import utils
from grow.sdk import sdk_utils


RELEASES_API = 'https://api.github.com/repos/grow/grow/releases'
TAGS_URL_FORMAT = 'https://github.com/grow/grow/releases/tag/{}'
INSTALLER_COMMAND = ('/usr/bin/python -c "$(curl -fsSL '
                     'https://raw.github.com/grow/grow/master/install.py)"')


class Error(Exception):
    """Base error for updaters."""

    def __init__(self, message):
        super(Error, self).__init__(message)
        self.message = message


class LatestVersionCheckError(Error):
    """Error checking for the latest version."""
    pass


class Updater(object):
    """Grow updater for dependencies."""

    def __init__(self, pod):
        self.pod = pod

    @property
    def current_version(self):
        """Current version of grow."""
        return config.VERSION

    @utils.cached_property
    def latest_version(self):  # pylint: disable=no-self-use
        """Latest version available for current platform."""
        try:
            releases = requests.get(RELEASES_API).json()
            if 'message' in releases:
                text = 'Error while downloading release information: {}'.format(
                    releases['message'])
                logging.error(colors.stylize(text, colors.ERROR))
                raise LatestVersionCheckError(str(text))
            for release in releases:
                if release['prerelease']:
                    continue
                for each_asset in release['assets']:
                    if sdk_utils.PLATFORM in each_asset.get('name', '').lower():
                        return release['tag_name']
            raise LatestVersionCheckError(
                'Unable to find a release for {} platform.'.format(sdk_utils.PLATFORM))
        except LatestVersionCheckError:
            raise
        except Exception as err:
            logging.exception(colors.stylize(str(err), colors.ERROR))
            text = 'Unable to check for the latest version: {}'.format(str(err))
            logging.error(colors.stylize(text, colors.ERROR))
            raise LatestVersionCheckError(str(err))

    def check_for_updates(self, auto_update_prompt=False, force=False):
        """Check for updates to the sdk."""
        grow_rc_config = rc_config.RC_CONFIG

        # Rate limited update checks.
        if not grow_rc_config.needs_update_check and not force:
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
        logging.info('')
        logging.info('  Please update to the newest version of the Grow SDK.')
        logging.info('  Release notes: {}'.format(url))
        logging.info('  Your version: {}, latest version: {}'.format(
            colors.stylize(str(sem_current), colors.EMPHASIS),
            colors.stylize(str(sem_latest), colors.EMPHASIS)))

        if auto_update_prompt:
            use_auto_update = grow_rc_config.get('update.always', False)

            if use_auto_update:
                logging.info('  > Auto-updating to version: {}'.format(
                    colors.stylize(str(sem_latest), colors.HIGHLIGHT)))
            else:  # pragma: no cover
                try:
                    choice = input(
                        'Auto update now? [Y]es / [n]o / [a]lways: ').strip().lower()
                except KeyboardInterrupt:
                    choice = 'n'
                if choice not in ('y', 'a', ''):
                    return
                if choice == 'a':
                    grow_rc_config.set('update.always', True)
                    grow_rc_config.write()

            if subprocess.call(INSTALLER_COMMAND, shell=True) == 0:
                logging.info('Restarting...')
                try:
                    # Restart on successful install.
                    os.execl(sys.argv[0], *sys.argv)
                except OSError:
                    logging.info(
                        'Unable to restart. Please manually restart grow.')
                    sys.exit(-1)
            else:
                text = (
                    'In-place update failed. Update manually or use:\n'
                    '  curl https://install.grow.io | bash')
                logging.error(text)
                sys.exit(-1)
        else:
            install_command = colors.stylize('pip install --upgrade grow', colors.CAUTION)
            logging.info('  Update using: {}'.format(install_command))
        logging.info('')
        return True

    def verify_required_version(self):
        """Verify that the required version for the pod is met."""
        if self.pod.grow_version is None:
            return
        sem_current = semantic_version.Version(self.current_version)
        grow_version_pattern = '{}'.format(self.pod.grow_version)
        # Include pre-releases in the version check.
        if '-' not in grow_version_pattern:
            grow_version_pattern = '{}-'.format(grow_version_pattern)
        spec_required = semantic_version.SimpleSpec(grow_version_pattern)
        if sem_current not in spec_required:
            text = 'ERROR! Pod requires Grow SDK version: {}'.format(
                self.pod.grow_version)
            logging.error(colors.stylize(text, colors.ERROR))
            raise LatestVersionCheckError(text)
