# coding: utf8
"""Utility functions for managing the sdk."""

import logging
import os
import platform
import subprocess
import sys
import urlparse
import requests
import semantic_version
from grow.common import config
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
    except Exception as e:
        logging.error(colorize(str(e), ansi=198))
        text = 'Unable to check for the latest version: {}'.format(str(e))
        logging.error(colorize(text, ansi=198))
        raise LatestVersionCheckError(str(e))


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
    try:
        theirs = get_latest_version()
        yours = config.VERSION
    except LatestVersionCheckError:
        return
    if theirs <= yours:
        return
    url = 'https://github.com/grow/grow/releases/tag/{}'.format(theirs)
    logging.info('')
    logging.info('  Please update to the newest version of the Grow SDK.')
    logging.info('  See release notes: {}'.format(url))
    logging.info('  Your version: {}, latest version: {}'.format(
        colorize(yours, ansi=226), colorize(theirs, ansi=82)))
    if utils.is_packaged_app() and auto_update_prompt:
        if raw_input('Auto update now? [y/N]: ').lower() != 'y':
            return
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


def install(pod, gerrit=None):
    if gerrit or has_gerrit_remote(pod) and gerrit is not False:
        install_gerrit_commit_hook(pod)
    if pod.file_exists('/package.json'):
        if pod.file_exists('/yarn.lock'):
            success = install_yarn(pod)
        else:
            success = install_npm(pod)
        if not success:
            return
    if pod.file_exists('/bower.json'):
        success = install_bower(pod)
        if not success:
            return
    if pod.file_exists('/gulpfile.js'):
        success = install_gulp(pod)
    if pod.file_exists('/extensions.txt'):
        success = install_extensions(pod)


def has_gerrit_remote(pod):
    KNOWN_GERRIT_HOSTS = (
        'googlesource.com',
    )
    repo = utils.get_git_repo(pod.root)
    if repo is None:
        return False
    for remote in repo.remotes:
        url = remote.config_reader.get('url')
        result = urlparse.urlparse(url)
        if result.netloc.endswith(KNOWN_GERRIT_HOSTS):
            return True


def install_gerrit_commit_hook(pod):
    error_message = '[✘] There was an error installing the Gerrit commit hook.'
    args = get_popen_args(pod)
    curl_command = (
        'curl -sLo '
        '`git rev-parse --git-dir`/hooks/commit-msg '
        'https://gerrit-review.googlesource.com/tools/hooks/commit-msg')
    chmod_command = 'chmod +x `git rev-parse --git-dir`/hooks/commit-msg'
    process = subprocess.Popen(curl_command, shell=True, **args)
    code = process.wait()
    if code:
        pod.logger.error(error_message)
        return False
    process = subprocess.Popen(chmod_command, shell=True, **args)
    code = process.wait()
    if code:
        pod.logger.error(error_message)
        return False
    pod.logger.info('[✓] Finished: Installed Gerrit Code Review commit hook.')
    return True


def install_npm(pod):
    args = get_popen_args(pod)
    npm_status_command = 'npm --version > /dev/null 2>&1'
    npm_not_found = subprocess.call(
        npm_status_command, shell=True, **args) == 127
    if npm_not_found:
        if PLATFORM == 'linux':
            pod.logger.error('[✘] The "npm" command was not found.')
            pod.logger.error(
                '    On Linux, you can install npm using: apt-get install nodejs')
        elif PLATFORM == 'mac':
            pod.logger.error('[✘] The "npm" command was not found.')
            pod.logger.error(
                '    Using brew (https://brew.sh), you can install using: brew install node')
            pod.logger.error(
                '    If you do not have brew, you can download Node.js from https://nodejs.org')
        else:
            pod.logger.error('[✘] The "npm" command was not found.')
            pod.logger.error('    Download Node.js from https://nodejs.org')
        return
    pod.logger.info('[✓] "npm" is installed.')
    npm_command = 'npm install'
    process = subprocess.Popen(npm_command, shell=True, **args)
    code = process.wait()
    if not code:
        pod.logger.info('[✓] Finished: npm install.')
        return True
    pod.logger.error('[✘] There was an error running "npm install".')


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


def install_extensions(pod):
    args = get_popen_args(pod)
    pip_status_command = 'pip --version > /dev/null 2>&1'
    pip_not_found = subprocess.call(
        pip_status_command, shell=True, **args) == 127
    if pip_not_found:
        pod.logger.error('[✘] The "pip" command was not found.')
        return
    extensions_dir = pod.extensions_dir
    pod.logger.info('[✓] "pip" is installed.')
    command = 'pip install -U -t {} -r extensions.txt'
    pip_command = command.format(extensions_dir)
    process = subprocess.Popen(pip_command, shell=True, **args)
    code = process.wait()
    if not code:
        init_file_name = '/{}/__init__.py'.format(extensions_dir)
        if not pod.file_exists(init_file_name):
            pod.write_file(init_file_name, '')
        text = '[✓] Installed: extensions.txt -> {}'
        pod.logger.info(text.format(extensions_dir))
        return True
    pod.logger.error('[✘] There was an error running "{}".'.format(pip_command))


def install_yarn(pod):
    args = get_popen_args(pod)
    yarn_status_command = 'yarn --version > /dev/null 2>&1'
    yarn_not_found = subprocess.call(
        yarn_status_command, shell=True, **args) == 127
    if yarn_not_found:
        pod.logger.error('[✘] The "yarn" command was not found.')
        pod.logger.error('    Please install using: yarn install -g yarn')
        return
    pod.logger.info('[✓] "yarn" is installed.')
    yarn_command = 'yarn install'
    process = subprocess.Popen(yarn_command, shell=True, **args)
    code = process.wait()
    if not code:
        pod.logger.info('[✓] Finished: yarn install.')
        return True
    pod.logger.error('[✘] There was an error running "yarn install".')
