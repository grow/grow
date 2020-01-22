# -*- mode: python -*-

import glob
import importlib
import os
import stdlib_list
import sys
from PyInstaller.utils.hooks import collect_submodules

IS_DARWIN = sys.platform == 'darwin'

def glob_datas(dir_path):
  files = []
  def recursive_glob(main_path, files):
    for path in glob.glob(main_path):
      if os.path.isfile(path):
        files.append(path)
      recursive_glob(path + '/*', files)
  recursive_glob(dir_path + '/*', files)
  return [(path.replace('grow/', ''), path, 'DATA') for path in files]


# Only include PIL.Imaging and PyQt4 on Darwin.
# TODO(jeremydw): See if we can kill this.
if IS_DARWIN:
  hiddenimports = [
      'PIL.Imaging',
      'PyQt4.QtCore',
  ]
else:
  hiddenimports = []


hiddenimports += [
    'babel.dates',
    'babel.numbers',
    'babel.plural',
    'markdown',
    'markdown.extensions',
    'pkg_resources.py2_warn',
    'pygments.formatters',
    'pygments.formatters.html',
    'pygments.lexers',
    'pygments.lexers.configs',
    'pygments.lexers.data',
    'pygments.lexers.php',
    'pygments.lexers.shell',
    'pygments.lexers.special',
    'pygments.lexers.templates',
    'werkzeug',
    'werkzeug._internal',
    'werkzeug.datastructures',
    'werkzeug.debug',
    'werkzeug.exceptions',
    'werkzeug.formparser',
    'werkzeug.http',
    'werkzeug.local',
    'werkzeug.routing',
    'werkzeug.script',
    'werkzeug.security',
    'werkzeug.serving',
    'werkzeug.test',
    'werkzeug.testapp',
    'werkzeug.urls',
    'werkzeug.useragents',
    'werkzeug.utils',
    'werkzeug.wrappers',
    'werkzeug.wsgi',
]

# Ensure the stdlib is included in its entirety for extensions.
hiddenimports += stdlib_list.stdlib_list('2.7')

try:
  hiddenimports += collect_submodules('pkg_resources._vendor')
except AssertionError:
  pass  # Environment doesn't need this to be collected.


package_imports = [
  ('text_unidecode', ['data.bin']),
]

datas = []
for package, files in package_imports:
    package_root = os.path.dirname(importlib.import_module(package).__file__)
    datas.extend((os.path.join(package_root, f), package) for f in files)

# Longer paths precede shorter paths for path-stripping.
env_paths = []
if 'VIRTUAL_ENV' in os.environ:
  env_paths.append(
    os.path.join(os.environ['VIRTUAL_ENV'], 'lib', 'python2.7', 'site-packages'))
env_paths.append('.')

a = Analysis([
                'bin/grow',
             ],
             datas=datas,
             pathex=env_paths,
             hiddenimports=hiddenimports,
             hookspath=None,
             runtime_hooks=None)


a.datas += [
    ('VERSION', 'grow/VERSION', 'DATA'),
    ('data/cacerts.txt', 'grow/data/cacerts.txt', 'DATA'),
    ('httplib2/cacerts.txt', 'grow/data/cacerts.txt', 'DATA'),
]
a.datas += glob_datas('grow/ui/admin/assets')
a.datas += glob_datas('grow/ui/admin/partials')
a.datas += glob_datas('grow/ui/admin/views')
a.datas += glob_datas('grow/ui/dist')
a.datas += glob_datas('grow/pods/templates')


# Include PyQt4 on Darwin. TODO(jeremydw): See if we can kill this.
if IS_DARWIN:
  try:
    def get_qt4_path():
      import PyQt4
      qt4_path = PyQt4.__path__[0]
      return qt4_path
    dict_tree = Tree(get_qt4_path(), prefix='PyQt4', excludes=["*.pyc"])
    a.datas += dict_tree
  except ImportError:
    pass


pyz = PYZ(a.pure,
          name='growsdk')


exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='grow',
          debug=False,
          strip=None,
          upx=True,
          console=True)
