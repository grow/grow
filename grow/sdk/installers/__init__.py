"""Grow prerequisite installers."""

from grow.sdk.installers import (
    bower_installer,
    extensions_installer,
    gerrit_installer,
    gulp_installer,
    npm_installer,
    nvm_installer,
)

# The order here determines the order the installers are run.
BUILT_IN_INSTALLERS = [
    extensions_installer.ExtensionsInstaller,
    gerrit_installer.GerritInstaller,
    nvm_installer.NvmInstaller,  # Before any node based installers.
    npm_installer.NpmInstaller,
    bower_installer.BowerInstaller,  # After the npm install.
    gulp_installer.GulpInstaller,  # After the npm install.
]
