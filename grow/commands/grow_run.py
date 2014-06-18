"""Starts a pod server for a single pod.

Usage: grow run [options] [<pod_path>]

  --help
  --debug                  Run the server in debug mode
  --host=<host>            IP address or hostname to bind the server
                           to [default: localhost]
  --port=<port>            Port to bind the server to [default: 8080]
  --open                   open a web browser when starting the server
  --skip_sdk_update_check  Skip the check for SDK updates
"""

from docopt import docopt
from grow.common import sdk_utils
from grow.pods import env
from grow.pods import pods
from grow.pods import storage
from grow.server import manager
import os
import threading


if __name__ == '__main__':
  args = docopt(__doc__)

  if not args['--skip_sdk_update_check']:
    thread = threading.Thread(target=sdk_utils.check_version, args=(True,))
    thread.start()

  args['--port'] = int(args['--port'])
  root = os.path.abspath(os.path.join(os.getcwd(), args['<pod_path>'] or '.'))
  environment = env.Env(env.EnvConfig(host=args['--host'], port=args['--port']))
  pod = pods.Pod(root, storage=storage.FileStorage, env=environment)
  manager.start(
      pod, host=args['--host'], port=args['--port'],
      open_browser=args['--open'], debug=args['--debug'])
