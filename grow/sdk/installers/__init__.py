"""Grow prerequisite installers."""

from grow.sdk.installers import extensions_installer
from grow.sdk.installers import npm_installer

# The order here determines the order the installers are run.
BUILT_IN_INSTALLERS = [
    npm_installer.NpmInstaller,
    extensions_installer.ExtensionsInstaller,
]
