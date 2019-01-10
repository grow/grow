# coding: utf8
"""Base installer class."""

import colored
from grow.sdk.installers import base_installer


EXTRA_FORMAT = '{}\n   {}'
MESSAGE_FORMAT = '[{}] {}'


class Error(Exception):
    """Base error for installers."""
    pass


class Installer(object):
    """Grow installer for dependencies."""

    def __init__(self, installers, pod):
        self.installers = installers
        self.pod = pod

    @staticmethod
    def format_message(message, extras=None):
        """Format a message with support for extra lines."""
        if extras:
            for extra in extras:
                message = EXTRA_FORMAT.format(message, extra)
        return message

    @classmethod
    def failure(cls, message, extras=None):
        """Generate a formatted failure message."""
        message = cls.format_message(message, extras)
        styling = colored.fg('red') + colored.attr('bold')
        return colored.stylize(MESSAGE_FORMAT.format('✘', message), styling)

    @classmethod
    def success(cls, message, extras=None):
        """Generate a formatted success message."""
        message = cls.format_message(message, extras)
        styling = colored.fg('green')
        return colored.stylize(MESSAGE_FORMAT.format('✓', message), styling)

    def run_installers(self):
        """Run each installer to install prerequisites."""
        for installer in self.installers:
            if not installer.should_run:
                continue

            with self.pod.profile.timer('Installer.run_installers.{}'.format(installer.KIND)):
                try:
                    installer.check_prerequisites()
                except base_installer.MissingPrerequisiteError as err:
                    self.pod.logger.error(
                        self.failure(err.message, extras=err.install_commands))
                    return False

                installer.install()

                messages = installer.post_install_messages
                if messages:
                    self.pod.logger.info(
                        self.success(messages[0], messages[1:] if len(messages) > 1 else []))
        # All installers were successful.
        return True
