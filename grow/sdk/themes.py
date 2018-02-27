"""Grow theme management."""

import io
import logging
import zipfile
import requests

THEME_ARCHIVE_URL = 'https://github.com/growthemes/{}/archive/master.zip'
# with zipfile.ZipFile('spam.zip', 'r') as source:
#     source.read('eggs.txt')


class GrowTheme(object):
    """Grow theme."""

    def __init__(self, theme_name):
        self.theme_name = theme_name
        self.archive_url = THEME_ARCHIVE_URL.format(self.theme_name)

    def extract(self, pod, force=False):
        """Extract the source archive into the destination pod."""
        request = requests.get(self.archive_url)
        archive = zipfile.ZipFile(io.BytesIO(request.content), 'r')

        logging.info('Extracting {} into {}'.format(self.archive_url, pod.root))

        if not force:
            # Validate that it won't overwrite any files.
            print archive.namelist()
