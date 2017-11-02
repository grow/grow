"""Grow prerequisite installers."""

from grow.sdk.installers import npm_installer

BUILT_IN_INSTALLERS = [
    npm_installer.NpmInstaller,
]
