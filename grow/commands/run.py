from grow.pods import env
from grow.pods import pods
from grow.pods import storage
from grow.server import manager
import click
import os
import threading


@click.command()
@click.argument('pod_path', default='.')
@click.option('--host', default='localhost')
@click.option('--port', default=8080)
@click.option('--https', default=False,
              help='Whether to use "https" in the local environment.')
@click.option('--debug/--no-debug', default=False, is_flag=True,
              help='Whether to run in debug mode and show internal tracebacks'
                   ' when encountering exceptions.')
@click.option('--browser/--no-browser', '-b', is_flag=True, default=False,
              help='Whether to open a browser upon startup.')
@click.option('--update-check/--no-update-check', default=True, is_flag=True,
              help='Whether to check for updates to Grow.')
@click.option('--preprocess/--no-preprocess', '-p/-np',
              default=True, is_flag=True,
              help='Whether to run preprocessors on server start.')
@click.option('--ui/--no-ui', '-b', is_flag=True, default=True,
              help='Whether to inject the Grow UI Tools.')
def run(host, port, https, debug, browser, update_check, preprocess, ui,
        pod_path):
    """Starts a development server for a single pod."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    scheme = 'https' if https else 'http'
    config = env.EnvConfig(host=host, port=port, name=env.Name.DEV,
                           scheme=scheme, cached=False, dev=True)
    environment = env.Env(config)
    pod = pods.Pod(root, storage=storage.FileStorage, env=environment)

    if not ui:
        pod.disable(pod.FEATURE_UI)

    try:
        manager.start(pod, host=host, port=port, open_browser=browser,
                      debug=debug, preprocess=preprocess,
                      update_check=update_check)
    except pods.Error as e:
        raise click.ClickException(str(e))
