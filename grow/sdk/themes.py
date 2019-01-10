"""Grow theme management."""

import io
import logging
import zipfile
import requests

THEME_ARCHIVE_URL = 'https://github.com/growthemes/{}/archive/master.zip'


class GrowTheme(object):
    """Grow theme."""

    def __init__(self, theme_name):
        self.theme_name = theme_name
        self.archive_url = THEME_ARCHIVE_URL.format(self.theme_name)

    @property
    def archive(self):
        """Download the archive zip and open."""
        logging.info('Downloading `{}` from Github'.format(self.theme_name))
        request = requests.get(self.archive_url)
        return zipfile.ZipFile(io.BytesIO(request.content), 'r')

    def extract(self, pod, force=False):
        """Extract the source archive into the destination pod."""
        with self.archive as archive:
            logging.info('Extracting theme into {}'.format(pod.root))

            # Automatically enable "force" for empty directories.
            if pod.list_dir('/') == []:
                force = True

            archive_prefix_dir = '{}-master'.format(self.theme_name)
            archive_files = [name[len(archive_prefix_dir):] for name in archive.namelist()]

            # Validate that it won't overwrite any files.
            if not force:
                for file_name in archive_files:
                    if file_name == '/':
                        continue
                    if pod.file_exists(file_name):
                        text = ('{}{} already exists. Delete the directory contents before'
                                ' proceeding or use --force.')
                        logging.warn(text.format(pod.root, file_name))
                        return

            for file_name in archive_files:
                if file_name.endswith('/'):
                    continue

                pod.write_file(
                    file_name, archive.read('{}{}'.format(archive_prefix_dir, file_name)))

            logging.info('Pod ready to go: {}'.format(pod.root))
