# coding: utf8
"""Utility functions for managing the sdk."""

import logging
import os
import platform
import subprocess
import sys
import requests
import semantic_version
from grow.common import colors
from grow.common import config
from grow.common import rc_config
from grow.common import utils


VERSION = config.VERSION
RELEASES_API = 'https://api.github.com/repos/grow/grow/releases'
INSTALLER_COMMAND = ('/usr/bin/python -c "$(curl -fsSL '
                     'https://raw.github.com/grow/grow/master/install.py)"')

PLATFORM = None
if 'Linux' in platform.system():
    PLATFORM = 'linux'
elif 'Darwin' in platform.system():
    PLATFORM = 'mac'


class Error(Exception):
    pass


class LatestVersionCheckError(Error):
    pass


def get_this_version():
    return VERSION


def get_latest_version():
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
                if PLATFORM in each_asset.get('name', '').lower():
                    return release['tag_name']
    except LatestVersionCheckError:
        raise
    except Exception as err:
        logging.error(colors.stylize(str(err), colors.ERROR))
        text = 'Unable to check for the latest version: {}'.format(str(err))
        logging.error(colors.stylize(text, colors.ERROR))
        raise LatestVersionCheckError(str(err))


def check_sdk_version(pod):
    sdk_version = get_this_version()
    requires_version = pod.grow_version
    if requires_version is None:
        return
    if (semantic_version.Version(sdk_version)
            not in semantic_version.Spec(requires_version)):
        text = 'ERROR! Pod requires Grow SDK version: {}'.format(
            requires_version)
        logging.error(colors.stylize(text, colors.ERROR))
        raise LatestVersionCheckError(str(text))


def check_for_sdk_updates(auto_update_prompt=False):
    grow_rc_config = rc_config.RC_CONFIG
    if not grow_rc_config.needs_update_check:
        return
    try:
        theirs = get_latest_version()
        yours = get_this_version()
        # Mark that we have performed a check for the update.
        grow_rc_config.reset_update_check()
        grow_rc_config.write()
    except LatestVersionCheckError:
        return
    if semantic_version.Version(theirs) <= semantic_version.Version(yours):
        return
    url = 'https://github.com/grow/grow/releases/tag/{}'.format(theirs)
    logging.info('')
    logging.info('  Please update to the newest version of the Grow SDK.')
    logging.info('  See release notes: {}'.format(url))
    logging.info('  Your version: {}, latest version: {}'.format(
        colors.stylize(yours, colors.EMPHASIS), colors.stylize(theirs, colors.EMPHASIS)))

    if utils.is_packaged_app() and auto_update_prompt:
        use_auto_update = grow_rc_config.get('update.always', False)

        if use_auto_update:
            logging.info('  > Auto-updating to version: {}'.format(
                colors.stylize(theirs, colors.HIGHLIGHT)))
        else:
            choice = raw_input(
                'Auto update now? [Y]es / [n]o / [a]lways: ').strip().lower()
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
        else:
            text = (
                'In-place update failed. Update manually or use:\n'
                '  curl https://install.grow.io | bash')
            logging.error(text)
            sys.exit(-1)
    else:
        logging.info('  Update using: ' +
                     colors.stylize('pip install --upgrade grow', colors.CAUTION))
    print ''
