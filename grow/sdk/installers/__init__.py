"""Grow prerequisite installers."""

from grow.sdk.installers import extensions_installer
from grow.sdk.installers import gerrit_installer
from grow.sdk.installers import npm_installer

# The order here determines the order the installers are run.
BUILT_IN_INSTALLERS = [
    extensions_installer.ExtensionsInstaller,
    gerrit_installer.GerritInstaller,
    nvm_installer.NvmInstaller,  # Before any node based installers.
    npm_installer.NpmInstaller,
]
