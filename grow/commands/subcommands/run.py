"""Command to run the local development server."""

import os
import click
from grow.commands import shared
from grow.common import rc_config
from grow.pods import env
from grow.pods import pods
from grow import storage
from grow.server import manager


CFG = rc_config.RC_CONFIG.prefixed('grow.run')


# pylint: disable=too-many-locals, invalid-name, too-many-arguments
@click.command()
@shared.pod_path_argument
@click.option('--host', default=CFG.get('host', 'localhost'))
@click.option('--port', default=CFG.get('port', 8080))
@click.option('--https', default=CFG.get('https', False),
              help='Whether to use "https" in the local environment.')
@click.option('--debug/--no-debug', default=CFG.get('debug', False), is_flag=True,
              help='Whether to run in debug mode and show internal tracebacks'
                   ' when encountering exceptions.')
@click.option('--browser/--no-browser', '-b', is_flag=True,
              default=CFG.get('browser', False),
              help='Whether to open a browser upon startup.')
@click.option('--update-check/--no-update-check',
              default=CFG.get('update-check', True), is_flag=True,
              help='Whether to check for updates to Grow.')
@click.option('--ui/--no-ui', is_flag=CFG.get('ui', True), default=True,
              help='Whether to inject the Grow UI Tools.')
@shared.deployment_option(CFG)
@shared.preprocess_option(CFG)
@shared.reroute_option(CFG)
def run(host, port, https, debug, browser, update_check, preprocess, ui,
        pod_path, deployment, use_reroute):
    """Starts a development server for a single pod."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    scheme = 'https' if https else 'http'
    config = env.EnvConfig(host=host, port=port, name=env.Name.DEV,
                           scheme=scheme, cached=False, dev=True)
    environment = env.Env(config)
    pod = pods.Pod(
        root, storage=storage.FileStorage, env=environment,
        use_reroute=use_reroute)
    if deployment:
        deployment_obj = pod.get_deployment(deployment)
        pod.set_env(deployment_obj.config.env)
    if not ui:
        pod.disable(pod.FEATURE_UI)
    try:
        manager.start(pod, host=host, port=port, open_browser=browser,
                      debug=debug, preprocess=preprocess,
                      update_check=update_check)
    except pods.Error as e:
        raise click.ClickException(str(e))
    return pod
