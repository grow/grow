#!/usr/bin/python

import os
import sys
sys.path.extend([os.path.join(os.path.dirname(__file__), '..')])
from grow import submodules
submodules.fix_imports()

from google.apputils import appcommands
from grow import commands

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')


def main(argv):
  appcommands.AddCmd('dump', commands.DumpCmd)
  appcommands.AddCmd('get', commands.GetCmd)
  appcommands.AddCmd('init', commands.InitCmd)
  appcommands.AddCmd('run', commands.RunCmd)
  appcommands.AddCmd('up', commands.UpCmd)


if __name__ == '__main__':
  appcommands.Run()
