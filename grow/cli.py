#!/usr/bin/python

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

import os
import sys
sys.path.extend([os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')])
from grow import submodules
submodules.fix_imports()

from google.apputils import appcommands
from grow import commands


def main(argv):
  appcommands.AddCmd('deploy', commands.DeployCmd)
  appcommands.AddCmd('dump', commands.DumpCmd)
  appcommands.AddCmd('get', commands.GetCmd)
  appcommands.AddCmd('init', commands.InitCmd)
  appcommands.AddCmd('run', commands.RunCmd)
  appcommands.AddCmd('up', commands.UpCmd)
  appcommands.AddCmd('test', commands.TestCmd)


if __name__ == '__main__':
  appcommands.Run()
