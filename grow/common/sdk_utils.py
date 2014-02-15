import logging
import urllib
from grow.common import config


class Error(Exception):
  pass


class LatestVersionCheckError(Error):
  pass


def get_this_version():
  return config.VERSION


def get_latest_version():
  logging.info('Checking for updates to the Grow SDK...')
  version_manifest = 'https://raw.github.com/grow/pygrow/master/grow/VERSION'
  try:
    version = urllib.urlopen(version_manifest).read()
    return version.strip()
#  except urllib.errors.URLError as e:
  except Exception as e:
    logging.exception('Could not check for updates.')
    raise LatestVersionCheckError(str(e))


def check_version(quiet=False):
  try:
    theirs = get_latest_version()
    yours = config.VERSION
    if theirs > yours:
      logging.info('---')
      logging.info('Your version: {}, latest version: {}'.format(yours, theirs))
      logging.info('A newer version of the SDK is available. Please update now: http://growapp.org')
      logging.info('---')
    else:
      logging.info('Your Grow SDK is the latest version: {}'.format(yours))
  except LatestVersionCheckError:
    if not quiet:
      raise
