from grow.common import config
from grow.common import utils
from xtermcolor import colorize
import json
import logging
import os
import subprocess
import sys
import urllib

RELEASES_API = 'https://api.github.com/repos/grow/pygrow/releases'
INSTALLER_COMMAND = '/usr/bin/python -c "$(curl -fsSL https://raw.github.com/grow/pygrow/master/install.py)"'


class Error(Exception):
  pass


class LatestVersionCheckError(Error):
  pass


def get_this_version():
  return config.VERSION


def get_latest_version():
  try:
    releases = json.loads(urllib.urlopen(RELEASES_API).read())
    return releases[0]['tag_name']
  except Exception as e:
    text = 'Cannot check for updates to the SDK while offline.'
    logging.error(colorize(text, ansi=198))
    raise LatestVersionCheckError(str(e))


def check_version(auto_update_prompt=False):
  try:
    theirs = get_latest_version()
    yours = config.VERSION
  except LatestVersionCheckError:
    return

  if theirs <= yours:
    return

  print ''
  print '  Please update to the newest version of the SDK. See http://growsdk.org.'
  print '  Your version: {}, latest version: {}'.format(
      colorize(yours, ansi=226), colorize(theirs, ansi=226))
  if utils.is_packaged_app() and auto_update_prompt:
    # If the installation was successful, restart the process.
    if (raw_input('Auto update now? [y/N]: ').lower() == 'y'
        and subprocess.call(INSTALLER_COMMAND, shell=True) == 0):
      logging.info('Restarting...')
      os.execl(sys.argv[0], *sys.argv)
  else:
    print '  Update using: ' + colorize('pip install --upgrade grow', ansi=200)
  print ''
