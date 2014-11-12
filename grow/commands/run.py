from grow.common import sdk_utils
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
@click.option('--debug', default=False,
              help='Whether to run in debug mode.')
@click.option('--browser', is_flag=True, default=False,
              help='Whether to open a browser upon startup.')
@click.option('--skip_sdk_update_check', default=False,
              help='Whether to skip checking for updates to the Grow SDK.')
def run(pod_path, host, port, debug, browser, skip_sdk_update_check):
  """Starts a development server for a single pod."""
  if not skip_sdk_update_check:
    thread = threading.Thread(target=sdk_utils.check_version, args=(True,))
    thread.start()
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path or '.'))
  environment = env.Env(env.EnvConfig(host=host, port=port, name='dev'))
  pod = pods.Pod(root, storage=storage.FileStorage, env=environment)
  manager.start(pod, host=host, port=port, open_browser=browser, debug=debug)
