import os
import re

regex = re.compile('((?:[^-]+)-(?:[^-]+)-(?:[^-]+))-dot-')


def get_changeset(hostname):
  matches = regex.findall(hostname)
  return matches[0] if matches else None


def make_staging_url(changeset, path='', hostname=None):
  if hostname is None:
    hostname = os.environ.get('DEFAULT_VERSION_HOSTNAME', '')
  return 'https://{}-dot-{}{}'.format(changeset, hostname, path)
