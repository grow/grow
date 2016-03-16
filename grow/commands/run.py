from grow.common import sdk_utils
from grow.pods import env
from grow.pods import pods
from grow.pods import storage
from grow.server import manager
import click
import os
import threading
import twisted


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
@click.option('--skip_sdk_update_check', default=False, is_flag=True,
              help='Whether to skip checking for updates to the Grow SDK.')
@click.option('--preprocess/--no-preprocess', default=True, is_flag=True,
              help='Whether to run preprocessors on server start.')
def run(host, port, https, debug, browser, skip_sdk_update_check, preprocess,
        pod_path):
    """Starts a development server for a single pod."""
    if not skip_sdk_update_check:
        update_func = sdk_utils.check_for_sdk_updates
        thread = threading.Thread(target=update_func, args=(True,))
        thread.start()
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    scheme = 'https' if https else 'http'
    config = env.EnvConfig(host=host, port=port, name='dev',
                           scheme=scheme, cached=False)
    environment = env.Env(config)
    pod = pods.Pod(root, storage=storage.FileStorage, env=environment)
    try:
        try:
            manager.start(pod, host=host, port=port, open_browser=browser,
                          debug=debug, preprocess=preprocess)
        except pods.Error as e:
            raise click.ClickException(str(e))
    except twisted.internet.error.ReactorNotRunning:
        # Swallow flaky error when quitting with ctrl+c.
        pass
