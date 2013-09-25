#!/usr/bin/env python
# Copyright 2011 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import subprocess
import sys

COLOR_G = '\033[0;32m'  # Green.
COLOR_R = '\033[0;31m'  # Red.
COLOR_NONE = '\033[0;m'  # Reset to terminal's foreground color.

from grow import submodules
submodules.fix_imports()

print sys.path


def main():
  success = True

  # Add needed paths to the python path.
  tests_dir = os.path.normpath(os.path.join(os.path.dirname(__file__)))
  root_dir = tests_dir
  appengine_dir = '/usr/local/google_appengine/'
  sys.path.insert(0, appengine_dir)
  sys.path.insert(0, root_dir)
  print 'Running tests...'

  test_filenames = sys.argv[1:]
  if not test_filenames:
    test_filenames = []
    for root, unused_dirs, files in os.walk(tests_dir):
      # Skip modules directory.
      if 'modules' in root:
        continue
      new_tests = [os.path.join(root, f) for f in files]
      new_tests = [name.replace(tests_dir + '/', '') for name in new_tests]
      test_filenames.extend(new_tests)
    test_filenames = sorted(test_filenames)

  for basename in test_filenames:
    filename = os.path.join(tests_dir, basename)
    if not filename.endswith('_test.py'):
      continue

    sys.stdout.write('Testing %s\r' % basename)
    sys.stdout.flush()
    env = os.environ.copy()
    env['PYTHONPATH'] = ':'.join([tests_dir, root_dir, appengine_dir,
                                  env.get('PYTHONPATH', '')])
    process = subprocess.Popen([sys.executable, filename], env=env,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               stdin=subprocess.PIPE)
    try:
      stdout, stderr = process.communicate()
    except KeyboardInterrupt:
      process.terminate()
      print process.stdout.read()
      print process.stderr.read()
      sys.exit('Tests terminated.')

    # Certain tests output to stderr but correctly pass. For clarity, we hide
    # the output unless the test itself fails.
    if process.returncode != 0:
      msg = [COLOR_R, 'FAILED', COLOR_NONE, ': ', basename]
      print ''.join(msg)
      print stdout
      print stderr
      success = False
    else:
      msg = [COLOR_G, 'SUCCESS', COLOR_NONE, ': ', basename]
      print ''.join(msg)

  if success:
    print 'All tests were successful.'
  else:
    # Important: this returns a non-zero return code.
    sys.exit('One or more tests failed.')

if __name__ == '__main__':
  main()
