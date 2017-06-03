#!/usr/bin/env python
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
import urllib
import urllib2
import zipfile

DOWNLOAD_URL_FORMAT = 'https://github.com/grow/grow/releases/download/{version}/{name}'
RELEASES_API = 'https://api.github.com/repos/grow/grow/releases'
ALIAS_FILES_LINUX = ['.bash_aliases', '.bash_profile', '.profile', '.bashrc']
ALIAS_FILES_MAC = ['.bash_profile']
ALIAS_FILES_DEFAULT = '.bashrc'
ALIAS_RE = re.compile(r'^alias grow\=([\'"])(.*)\1$', re.MULTILINE)

if 'Linux' in platform.system():
  PLATFORM = 'linux'
elif 'Darwin' in platform.system():
  PLATFORM = 'mac'
else:
  print ('{} is not a supported platform. Please file an issue at '
         'https://github.com/grow/grow/issues'.format(sys.platform))
  sys.exit(-1)


def hai(text, *args):
  print text.format(*args, **{
    'blue': '\033[0;34m',
    '/blue': '\033[0;m',
    'red': '\033[0;31m',
    '/red': '\033[0;m',
    'green': '\033[0;32m',
    '/green': '\033[0;m',
    'yellow': '\033[0;33m',
    '/yellow': '\033[0;m',
    'white': '\033[0;37m',
    '/white': '\033[0;m',
  })


def orly(text):
  resp = raw_input(text)
  return resp.lower() == 'y'


def find_conflicting_aliases(existing_aliases, bin_path):
  files_to_alias = {}
  for filename, paths in existing_aliases.iteritems():
    conflicting = [path for path in paths if path != bin_path]
    if conflicting:
      files_to_alias[filename] = conflicting
  return files_to_alias


def find_matching_alias(existing_aliases, bin_path):
  for filename, paths in existing_aliases.iteritems():
    matching = [path for path in paths if path == bin_path]
    if matching:
      return filename
  return None


def get_alias_path():
  alias_files = ALIAS_FILES_LINUX if PLATFORM == 'linux' else ALIAS_FILES_MAC
  for basename in alias_files:
    basepath = os.path.expanduser('~/{}'.format(basename))
    if os.path.exists(basepath):
        return basepath
  return os.path.expanduser('~/{}'.format(ALIAS_FILES_DEFAULT))


def get_existing_aliases():
  files_to_alias = {}
  alias_files = ALIAS_FILES_LINUX if PLATFORM == 'linux' else ALIAS_FILES_MAC
  for basename in alias_files:
    basepath = os.path.expanduser('~/{}'.format(basename))
    if os.path.exists(basepath):
      profile = open(basepath).read()
      matches = re.findall(ALIAS_RE, profile)
      if matches:
        files_to_alias[basepath] = [x[1] for x in matches]
  return files_to_alias


def install(rc_path=None, bin_path=None, force=False):
  resp = json.loads(urllib.urlopen(RELEASES_API).read())
  try:
    release = resp[0]
  except KeyError:
    print 'There was a problem accessing the GitHub Releases API.'
    if 'message' in resp:
      print resp['message']
    sys.exit(-1)

  version = release['tag_name']
  asset = None
  for each_asset in release['assets']:
    if PLATFORM in each_asset.get('name', '').lower():
      asset = each_asset
      break
  if asset is None:
    print 'Release not yet available for platform: {}.'.format(platform.system())
    print 'Please try again in a few minutes.'
    sys.exit(-1)

  download_url = DOWNLOAD_URL_FORMAT.format(version=version, name=asset['name'])

  bin_path = os.path.expanduser(bin_path or '~/bin/grow')
  rc_path = os.path.expanduser(rc_path or get_alias_path())
  alias_cmd = 'alias grow="{}"'.format(bin_path)
  alias_comment = '# Added by Grow SDK Installer ({})'.format(datetime.datetime.now())

  hai('{yellow}Welcome to the installer for Grow SDK v{}{/yellow}', version)
  hai('{yellow}Release notes: {/yellow}https://github.com/grow/grow/releases/tag/{}', version)
  hai('{blue}==>{/blue} {green}This script will install:{/green} {}', bin_path)

  existing_aliases = get_existing_aliases()
  conflicting_aliases = find_conflicting_aliases(existing_aliases, bin_path)
  matching_alias = find_matching_alias(existing_aliases, bin_path)

  has_alias = bool(matching_alias)
  has_conflicts = bool(conflicting_aliases)

  if has_conflicts:
    hai('{red}[✗] You have conflicting aliases for "grow" in:{/red} {}', ' '.join([x for x in conflicting_aliases]))

  if has_alias:
    hai('{blue}[✓]{/blue} {green}You already have an alias for "grow" in:{/green} {}', rc_path)
  else:
    hai('{blue}==>{/blue} {green}An alias for "grow" will be created in:{/green} {}', rc_path)

  if not force:
    result = orly('Continue? [y/N]: ')
    if not result:
      hai('Aborted installation.')
      sys.exit(-1)

  remote = urllib2.urlopen(download_url)
  try:
    hai('Downloading from {}'.format(download_url))
    local, temp_path = tempfile.mkstemp()
    local = os.fdopen(local, 'w')
    while True:
      content = remote.read(1048576)  # 1MB.
      if not content:
        sys.stdout.write(' done!\n')
        break
      local.write(content)
      sys.stdout.write('.')
      sys.stdout.flush()
    remote.close()
    local.close()
    fp = open(temp_path, 'rb')
    zp = zipfile.ZipFile(fp)
    try:
      zp.extract('grow', os.path.dirname(bin_path))
    except IOError as e:
      if 'Text file busy' in str(e):
        hai('Unable to overwrite {}. Try closing Grow and installing again.'.format(bin_path))
        hai('You can use the installer by running: curl https://install.grow.io| bash')
        sys.exit(-1)
      raise
    fp.close()
    hai('{blue}[✓]{/blue} {green}Installed Grow SDK to:{/green} {}', bin_path)
    stat = os.stat(bin_path)
    os.chmod(bin_path, stat.st_mode | 0111)
  finally:
    os.remove(temp_path)

  if not has_alias:
    fp = open(rc_path, 'a')
    fp.write('\n' + alias_comment + '\n')
    fp.write(alias_cmd)
    fp.close()
    hai('{blue}[✓]{/blue} {green}Created "grow" alias in:{/green} {}', rc_path)
    hai('{green}All done. To use Grow SDK...{/green}')
    hai(' ...reload your shell session OR use `source {}`,', rc_path)
    hai(' ...then type `grow` and press enter.')


def parse_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('--bin-path', default=None,
                      help='Where to install `grow` executable.')
  parser.add_argument('--force', dest='force', action='store_true',
                      help='Whether to force install and bypass prompts.')
  parser.add_argument('--rc-path', default=None,
                      help='Profile to update with PATH.')
  parser.set_defaults(force=False)
  return parser.parse_args()


def main():
  args = parse_args()
  install(rc_path=args.rc_path, bin_path=args.bin_path, force=args.force)


if __name__ == '__main__':
  main()
