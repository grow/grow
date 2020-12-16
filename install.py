#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Standalone Grow SDK installer. Downloads Grow SDK and sets up command aliases."""

import argparse
import datetime
import json
import os
import platform
import re
import sys
import tempfile
import zipfile
from urllib import request as url_request

DOWNLOAD_URL_FORMAT = 'https://github.com/grow/grow/releases/download/{version}/{name}'
RELEASES_API = 'https://api.github.com/repos/grow/grow/releases'
RC_FILES = ['.bashrc', '.zshrc', '.bash_profile', '.profile']
RC_FILE_DEFAULT = '.bashrc'
BIN_PATH = '~/bin/grow'

# TODO: Remove when no longer checking for alias.
ALIAS_FILES = ['.bash_aliases', '.bash_profile', '.profile', '.bashrc']
ALIAS_RE = re.compile(r'^alias grow\=([\'"])(.*)\1$', re.MULTILINE)

if 'Linux' in platform.system():
    PLATFORM = 'linux'
elif 'Darwin' in platform.system():
    PLATFORM = 'mac'
else:
    print('{} is not a supported platform. Please file an issue at '
          'https://github.com/grow/grow/issues'.format(sys.platform))
    sys.exit(-1)


def hai(text, *args):
    print(text.format(*args, **{
        'red': '\033[0;31m',
        '/red': '\033[0;m',
        'green': '\033[0;32m',
        '/green': '\033[0;m',
        'yellow': '\033[0;33m',
        '/yellow': '\033[0;m',
        'white': '\033[0;37m',
        '/white': '\033[0;m',
    }))


def orly(text, default=False):
    resp = input(text).strip().lower()
    if resp == 'y':
        return True
    elif resp == 'n':
        return False
    return default


# TODO: Remove when no longer checking for alias.
def get_existing_aliases():
    """Find all existing aliases using the regex."""
    files_to_alias = {}
    for basename in ALIAS_FILES:
        basepath = os.path.expanduser('~/{}'.format(basename))
        if os.path.exists(basepath):
            profile = open(basepath).read()
            matches = re.findall(ALIAS_RE, profile)
            if matches:
                files_to_alias[basepath] = [x[1] for x in matches]
    return files_to_alias


def get_rc_path():
    for basename in RC_FILES:
        basepath = os.path.expanduser('~/{}'.format(basename))
        if os.path.exists(basepath):
            return basepath
    return os.path.expanduser('~/{}'.format(RC_FILE_DEFAULT))


def get_release_for_platform(releases, platform):
    """Find the latest release available for the platform."""
    for release in releases:
        if release['prerelease']:
            continue
        for each_asset in release['assets']:
            if platform in each_asset.get('name', '').lower():
                return release
    return None


def has_bin_in_path(bin_path):
    """Determine if the binary path is part of the system paths."""
    return bin_path in os.environ['PATH'].split(':')


def install(rc_path=None, bin_path=None, force=False):
    """Download and install the binary."""
    resp = json.loads(url_request.urlopen(RELEASES_API).read())
    try:
        release = get_release_for_platform(resp, PLATFORM)
    except KeyError:
        hai('{red}There was a problem accessing the GitHub Releases API.{/red}')
        if 'message' in resp:
            hai('{red}{}{/red}', resp['message'])
        sys.exit(-1)

    if release is None:
        print(('Not available for platform: {}.'.format(platform.system())))
        sys.exit(-1)

    version = release['tag_name']
    asset = None
    for each_asset in release['assets']:
        if PLATFORM in each_asset.get('name', '').lower():
            asset = each_asset
            break

    download_url = DOWNLOAD_URL_FORMAT.format(
        version=version, name=asset['name'])

    bin_path = os.path.expanduser(bin_path or BIN_PATH)
    bin_dir = os.path.dirname(bin_path)
    rc_comment = '# Added by Grow SDK Installer ({})'.format(
        datetime.datetime.now())
    rc_path = os.path.expanduser(rc_path or get_rc_path())
    rc_path_append = 'export PATH={}:$PATH'.format(bin_dir)

    hai('{yellow}Welcome to the installer for Grow SDK v{}{/yellow}', version)
    hai('{yellow}Release notes: {/yellow}https://github.com/grow/grow/releases/tag/{}', version)
    hai('{yellow}[ ]{/yellow} {green}This script will install:{/green} {}', bin_path)

    bin_in_path = has_bin_in_path(bin_dir)

    if bin_in_path:
        hai(
            '{green}[✓] You already have the binary directory in PATH:{/green} {}',
            bin_dir)
    else:
        hai(
            '{yellow}[ ]{/yellow} {green}{} will be added to the PATH in:{/green} {}',
            bin_dir, rc_path)

    if not force:
        try:
            result = orly('Continue installation? [Y]es / [n]o: ', default=True)
        except KeyboardInterrupt:
            result = False
        if not result:
            hai('\n\r{red}Aborted installation.{/red}')
            sys.exit(-1)

    try:
        os.makedirs(bin_dir)
    except OSError:
        # If the directory already exists, let it go.
        pass

    remote = url_request.urlopen(download_url)
    try:
        hai('Downloading from {}'.format(download_url))
        local, temp_path = tempfile.mkstemp()
        with os.fdopen(local, 'w') as local_file:
            while True:
                content = remote.read(1048576)  # 1MB.
                if not content:
                    sys.stdout.write(' done!\n')
                    sys.stdout.flush()
                    break
                local_file.write(content)
                sys.stdout.write('.')
                sys.stdout.flush()
        remote.close()
        with open(temp_path, 'rb') as fp:
            zp = zipfile.ZipFile(fp)
            try:
                zp.extract('grow', os.path.dirname(bin_path))
            except IOError as e:
                if 'Text file busy' in str(e):
                    hai('Unable to overwrite {}. Try closing Grow and installing again.'.format(
                        bin_path))
                    hai('You can use the installer by running: curl https://install.grow.io | bash')
                    sys.exit(-1)
                raise
        hai('{green}[✓] Installed Grow SDK to:{/green} {}', bin_path)
        stat = os.stat(bin_path)
        os.chmod(bin_path, stat.st_mode | 0o111)
    finally:
        os.remove(temp_path)

    if not bin_in_path:
        with open(rc_path, 'a') as fp:
            fp.write('\n' + rc_comment + '\n')
            fp.write(rc_path_append)
        hai('{green}[✓] Added {} to path in:{/green} {}',
            bin_path, rc_path)

    hai('{green}[✓] All done. Grow v{} successfully installed.{/green}', version)

    if not bin_in_path:
        hai('   To use Grow: reload your shell session OR use `source {}`,', rc_path)
        hai('   then type `grow` and press enter.')

    # TODO: Remove when no longer checking for alias.
    aliases = get_existing_aliases()
    if aliases:
        hai('{red}Aliases for grow detected in: {}{/red}', ', '.join(list(aliases.keys())))
        hai('   {red}please remove the old aliases to prevent version conflicts.{/red}')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bin-path', default=None,
                        help='Where to install `grow` executable. Ex: ~/bin/grow')
    parser.add_argument('--force', dest='force', action='store_true',
                        help='Whether to force install and bypass prompts.')
    parser.add_argument('--rc-path', default=None,
                        help='Profile to update with PATH. Ex: ~/.bashrc')
    parser.set_defaults(force=False)
    return parser.parse_args()


def main():
    args = parse_args()
    install(rc_path=args.rc_path, bin_path=args.bin_path, force=args.force)


if __name__ == '__main__':
    main()
