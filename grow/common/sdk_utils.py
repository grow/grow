from grow.common import config
from grow.common import utils
from xtermcolor import colorize
import json
import logging
import os
import semantic_version
import subprocess
import sys
import urllib

RELEASES_API = 'https://api.github.com/repos/grow/pygrow/releases'
INSTALLER_COMMAND = ('/usr/bin/python -c "$(curl -fsSL '
                     'https://raw.github.com/grow/pygrow/master/install.py)"')


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


def check_sdk_version(pod):
  sdk_version = get_this_version()
  requires_version = pod.grow_version
  if requires_version is None:
    return
  if (semantic_version.Version(sdk_version)
      not in semantic_version.Spec(requires_version)):
    text = 'WARNING! Pod requires Grow SDK version: {}'.format(requires_version)
    text = colorize(text, ansi=197)
    pod.logger.info(text)


def check_for_sdk_updates(auto_update_prompt=False):
  try:
    theirs = get_latest_version()
    yours = config.VERSION
  except LatestVersionCheckError:
    return
  if theirs <= yours:
    return
  url = 'https://github.com/grow/pygrow/releases/tag/{}'.format(theirs)
  print ''
  print '  Please update to the newest version of the Grow SDK.'
  print '  See release notes: {}'.format(url)
  print '  Your version: {}, latest version: {}'.format(
      colorize(yours, ansi=226), colorize(theirs, ansi=82))
  if utils.is_packaged_app() and auto_update_prompt:
    # If the installation was successful, restart the process.
    if (raw_input('Auto update now? [y/N]: ').lower() == 'y'
        and subprocess.call(INSTALLER_COMMAND, shell=True) == 0):
      logging.info('Restarting...')
      os.execl(sys.argv[0], *sys.argv)
  else:
    print '  Update using: ' + colorize('pip install --upgrade grow', ansi=200)
  print ''
