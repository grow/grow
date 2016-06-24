# -*- mode: python -*-

import os
import glob
import sys
try:
    # PyInstaller==3.1
    from PyInstaller.utils.hooks import collect_submodules
except:
    # PyInstaller==2.1.1
    from PyInstaller.hooks.hookutils import collect_submodules


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
    'keyring',
    'keyring.backends.Gnome',
    'keyring.backends.Google',
    'keyring.backends.OS_X',
    'keyring.backends.SecretService',
    'keyring.backends.Windows',
    'keyring.backends.file',
    'keyring.backends.keyczar',
    'keyring.backends.kwallet',
    'keyring.backends.multi',
    'keyring.backends.pyfs',
    'keyring.credentials',
    'keyring.util.XDG',
    'keyring.util.escape',
    'markdown',
    'markdown.extensions',
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

try:
  hiddenimports += collect_submodules('pkg_resources._vendor')
except AssertionError:
  pass  # Environment doesn't need this to be collected.

a = Analysis([
                'bin/grow',
             ],
             pathex=[
                # Longer paths precede shorter paths for path-stripping.
                './env/lib/python2.7/site-packages/',
                '.',
             ],
             hiddenimports=hiddenimports,
             hookspath=None,
             runtime_hooks=None)


a.datas += [
    ('VERSION', 'grow/VERSION', 'DATA'),
    ('data/cacerts.txt', 'grow/data/cacerts.txt', 'DATA'),
    ('httplib2/cacerts.txt', 'grow/data/cacerts.txt', 'DATA'),
]
a.datas += glob_datas('grow/server/frontend')
a.datas += glob_datas('grow/server/templates')
a.datas += glob_datas('grow/pods/templates')


# Crypto doesn't seem to be needed when building on Mac. TODO(jeremydw):
# research this dependency and determine if it can be eliminated from
# non-Mac builds.
if not IS_DARWIN:
  def get_crypto_path():
    import Crypto
    crypto_path = Crypto.__path__[0]
    return crypto_path
  dict_tree = Tree(get_crypto_path(), prefix='Crypto', excludes=["*.pyc"])
  a.datas += dict_tree


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
