from grow.common import config
from grow.common import utils
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
  logging.info('Checking for updates to the Grow SDK...')
  try:
    releases = json.loads(urllib.urlopen(RELEASES_API).read())
    return releases[0]['tag_name']
  except Exception as e:
    text = 'Could not check for updates to the SDK. Are you online?'
    logging.error(utils.colorize('{red}%s{/red}' % text))
    raise LatestVersionCheckError(str(e))


def check_version(auto_update_prompt=False):
  try:
    theirs = get_latest_version()
    yours = config.VERSION
  except LatestVersionCheckError:
    return

  if theirs > yours:
    logging.info('---')
    logging.info(utils.colorize('{green}Your version: %s,{/green} {yellow}latest version: %s{/yellow}' % (yours, theirs)))
    logging.info('A newer version of the SDK is available, so please update yours. See http://growsdk.org.')
    if utils.is_packaged_app() and auto_update_prompt:
      # If the installation was successful, restart the process.
      if (raw_input('Auto update now? [y/N]: ').lower() == 'y'
          and subprocess.call(INSTALLER_COMMAND, shell=True) == 0):
        logging.info('Restarting...')
        os.execl(sys.argv[0], *sys.argv)
    else:
      logging.info('Update using: pip install --upgrade grow')
    logging.info('---')
  else:
    logging.info('You have the latest version: {}'.format(yours))
