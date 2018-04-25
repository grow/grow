"""Shared options or arguments for cli commands."""

import click
from grow.common import rc_config


CFG = rc_config.RC_CONFIG.prefixed('grow.shared')


def pod_path_argument(func):
    """Argument for pod path."""
    return click.argument('pod_path', default='.')(func)


def deployment_option(config):
    """Option for changing env based on deployment name."""
    shared_default = CFG.get('deployment', None)
    config_default = config.get('deployment', shared_default)

    def _decorator(func):
        return click.option(
            '--deployment', default=config_default,
            help='Name of the deployment config to use.')(func)
    return _decorator


def force_untranslated_option(config):
    """Option for forcing untranslated string deployment."""
    shared_default = CFG.get('force-untranslated', False)
    config_default = config.get('force-untranslated', shared_default)

    def _decorator(func):
        return click.option(
            '--force-untranslated', 'force_untranslated',
            default=config_default, is_flag=True,
            help='Whether to force untranslated strings to be uploaded.')(func)
    return _decorator


def include_header_option(config):
    """Option for preserving catalog header."""
    shared_default = CFG.get('include-header', False)
    config_default = config.get('include-header', shared_default)

    def _decorator(func):
        return click.option(
            '--include-header',
            default=config_default, is_flag=True,
            help='Whether to preserve headers at the beginning of catalogs.')(func)
    return _decorator


def include_obsolete_option(config, default_value=False):
    """Option for including obsolete translations."""
    shared_default = CFG.get('include-obsolete', default_value)
    config_default = config.get('include-obsolete', shared_default)

    help_text = ('Whether to include obsolete messages. If false, obsolete'
                 ' messages will be removed from the catalog template.')

    if default_value is False:
        help_text = '{} {}'.format(
            help_text, 'By default, Grow cleans obsolete messages from the catalog template.')

    def _decorator(func):
        return click.option(
            '--include-obsolete/--no-include-obsolete',
            default=config_default, is_flag=True, help=help_text)(func)
    return _decorator


def locale_option(help_text=None, multiple=True):
    """Option for providing locale(s)."""
    if help_text is None:
        help_text = 'Locale to target.'

    def _decorator(func):
        return click.option(
            '--locale', type=str, multiple=multiple, help=help_text)(func)
    return _decorator


def localized_option(config):
    """Option for localizing catalogs."""
    shared_default = CFG.get('localized', None)
    config_default = config.get('localized', shared_default)

    def _decorator(func):
        return click.option(
            '--localized/--no-localized',
            is_flag=True, default=config_default,
            help='Whether to create localized message catalogs. Use this'
                 ' option if content varies by locale.')(func)
    return _decorator


def out_dir_option(config, help_text=None):
    """Option for localizing catalogs."""
    shared_default = CFG.get('out-dir', None)
    config_default = config.get('out-dir', shared_default)

    if help_text is None:
        help_text = 'Directory to output files.'

    def _decorator(func):
        return click.option(
            '--out-dir', '--out_dir',
            type=str, default=config_default, help=help_text)(func)
    return _decorator


def path_option(func):
    """Option for specifying a path for extraction."""
    return click.option(
        '--path',
        type=str, multiple=True,
        help='Which paths to extract strings from. By default, all paths'
             ' are extracted. This option is useful if you\'d like to'
             ' generate a partial messages file representing just a'
             ' specific set of files.')(func)


def preprocess_option(config):
    """Option for running preprocessors."""
    shared_default = CFG.get('preprocess', True)
    config_default = config.get('preprocess', shared_default)

    def _decorator(func):
        return click.option(
            '--preprocess/--no-preprocess', '-p/-np',
            is_flag=True, default=config_default,
            help='Whether to run preprocessors.')(func)
    return _decorator


def reroute_option(config):
    """Option for using new age router and rendering pipeline."""
    shared_default = CFG.get('re-route', True)
    config_default = config.get('re-route', shared_default)

    def _decorator(func):
        return click.option(
            '--re-route/--old-routing', 'use_reroute', is_flag=True, default=config_default,
            help='Use new routing/rendering pipeline.')(func)
    return _decorator


def service_option(func):
    """Option for configuring the transltor service to use."""
    return click.option('--service', '-s', type=str,
                        help='Name of the translator service to use. This option is'
                        ' only required if more than one service is configured.')(func)


def threaded_option(config):
    """Option for using threading when rendering."""
    shared_default = CFG.get('threaded', True)
    config_default = config.get('threaded', shared_default)

    def _decorator(func):
        return click.option(
            '--threaded/--no-threaded', '-t/-nt', is_flag=True,
            default=config_default,
            help='Use threading during rendering pipeline.')(func)
    return _decorator
