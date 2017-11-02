"""NPM installer class."""

from grow.sdk.installers import base_installer


class NpmInstaller(base_installer.BaseInstaller):
    """Grow npm installer."""

    KIND = 'NPM'

    @property
    def should_run(self):
        """Should the installer run?"""
        return True

    def check_prerequisites(self):
        """Check if required prerequisites are installed or available."""
        pass

    def install(self):
        """Install dependencies using npm."""
        pass
