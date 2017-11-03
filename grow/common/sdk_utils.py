# coding: utf8
"""Utility functions for managing the sdk."""

import logging
import os
import platform
import subprocess
import sys
import requests
import semantic_version
from grow.common import config
from grow.common import rc_config
from grow.common import utils
from xtermcolor import colorize


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
            logging.error(colorize(text, ansi=198))
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
        logging.error(colorize(str(err), ansi=198))
        text = 'Unable to check for the latest version: {}'.format(str(err))
        logging.error(colorize(text, ansi=198))
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
        logging.error(colorize(text, ansi=197))
        raise LatestVersionCheckError(str(text))


def check_for_sdk_updates(auto_update_prompt=False):
    grow_rc_config = rc_config.RCConfig()
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
        colorize(yours, ansi=226), colorize(theirs, ansi=82)))

    if utils.is_packaged_app() and auto_update_prompt:
        use_auto_update = grow_rc_config.get('update.always', False)

        if use_auto_update:
            logging.info('  > Auto-updating to version: {}'.format(
                colorize(theirs, ansi=82)))
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
            os.execl(sys.argv[0], *sys.argv)  # Restart on successful install.
        else:
            text = (
                'In-place update failed. Update manually or use:\n'
                '  curl https://install.grow.io | bash')
            logging.error(text)
            sys.exit(-1)
    else:
        logging.info('  Update using: ' +
                     colorize('pip install --upgrade grow', ansi=200))
    print ''


def get_popen_args(pod):
    node_modules_path = os.path.join(pod.root, 'node_modules', '.bin')
    env = os.environ.copy()
    env['PATH'] = str(os.environ['PATH'] + os.path.pathsep + node_modules_path)
    if pod.env and pod.env.name:
        env['GROW_ENVIRONMENT_NAME'] = pod.env.name
    args = {
        'cwd': pod.root,
        'env': env,
    }
    if os.name == 'nt':
        args['shell'] = True
    return args


def install(pod):
    if pod.file_exists('/bower.json'):
        success = install_bower(pod)
        if not success:
            return
    if pod.file_exists('/gulpfile.js'):
        success = install_gulp(pod)


def install_bower(pod):
    args = get_popen_args(pod)
    bower_status_command = 'bower --version > /dev/null 2>&1'
    bower_not_found = subprocess.call(
        bower_status_command, shell=True, **args) == 127
    if bower_not_found:
        pod.logger.error('[✘] The "bower" command was not found.')
        pod.logger.error(
            '    Either add bower to package.json or install globally using:'
            ' sudo npm install -g bower')
        return
    pod.logger.info('[✓] "bower" is installed.')
    bower_command = 'bower install'
    process = subprocess.Popen(bower_command, shell=True, **args)
    code = process.wait()
    if not code:
        pod.logger.info('[✓] Finished: bower install.')
        return True
    pod.logger.error('[✘] There was an error running "bower install".')


def install_gulp(pod):
    args = get_popen_args(pod)
    gulp_status_command = 'gulp --version > /dev/null 2>&1'
    gulp_not_found = subprocess.call(
        gulp_status_command, shell=True, **args) == 127
    if gulp_not_found:
        pod.logger.error('[✘] The "gulp" command was not found.')
        pod.logger.error(
            '    Either add gulp to package.json or install globally using:'
            ' sudo npm install -g gulp')
        return
    pod.logger.info('[✓] "gulp" is installed.')
    return True
