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

DOWNLOAD_URL_FORMAT = 'https://github.com/grow/pygrow/releases/download/{version}/{name}'
RELEASES_API = 'https://api.github.com/repos/grow/pygrow/releases'

if 'Linux' in platform.system():
  PLATFORM = 'linux'
elif 'Darwin' in platform.system():
  PLATFORM = 'mac'
else:
  print ('{} is not a supported platform. Please file an issue at '
         'https://github.com/grow/pygrow/issues'.format(sys.platform))
  sys.exit(-1)


def colorize(text):
  return text.format(**{
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


def hai(text):
  print colorize(text)


def orly(text):
  resp = raw_input(text)
  return resp.lower() == 'y'


def get_rc_path():
  if PLATFORM == 'linux':
    if os.path.exists(os.path.expanduser('~/.bash_profile')):
      basename = '.bash_profile'
    elif os.path.exists(os.path.expanduser('~/.profile')):
      basename = '.profile'
    else:
      basename = '.bashrc'
  elif PLATFORM == 'mac':
    basename = '.bash_profile'
  return '~/{}'.format(basename)


def install(rc_path=None, bin_path=None, force=False):
  release = json.loads(urllib.urlopen(RELEASES_API).read())[0]
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
  rc_path = os.path.expanduser(rc_path or get_rc_path())
  alias_cmd = 'alias grow="{}"'.format(bin_path)
  alias_comment = '# Added by Grow SDK Installer ({})'.format(datetime.datetime.now())

  hai('{yellow}Welcome to the installer for Grow SDK v%s{/yellow}' % version)
  hai('{yellow}Release notes: {/yellow}https://github.com/grow/pygrow/releases/tag/%s' % version)
  hai('{blue}==>{/blue} {green}This script will install:{/green} %s' % bin_path)

  has_alias = False
  if os.path.exists(rc_path):
    profile = open(rc_path).read()
    has_alias = bool(re.search('^{}$'.format(alias_cmd), profile, re.MULTILINE))
  if has_alias:
    hai('{blue}[✓]{/blue} {green}You already have an alias for "grow" in:{/green} %s' % rc_path)
  else:
    hai('{blue}==>{/blue} {green}An alias for "grow" will be created in:{/green} %s' % rc_path)

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
    zp.extract('grow', os.path.dirname(bin_path))
    fp.close()
    hai('{blue}[✓]{/blue} {green}Installed Grow SDK to:{/green} %s' % bin_path)
    stat = os.stat(bin_path)
    os.chmod(bin_path, stat.st_mode | 0111)
  finally:
    os.remove(temp_path)

  if not has_alias:
    fp = open(rc_path, 'a')
    fp.write('\n' + alias_comment + '\n')
    fp.write(alias_cmd)
    fp.close()
    hai('{blue}[✓]{/blue} {green}Created "grow" alias in:{/green} %s' % rc_path)
    hai('{green}All done. To use Grow SDK...{/green}')
    hai(' ...reload your shell session OR use `source {}`,'.format(rc_path))
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
