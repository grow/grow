# -*- mode: python -*-

from PyInstaller.hooks.hookutils import collect_submodules

a = Analysis([
                'bin/grow',
             ],
             pathex=[
                '.',
                './env/lib/python2.7/site-packages/',
             ],
             hiddenimports=[
		'PIL.Imaging',
		'PyQt4.QtCore',
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
             ],
             hookspath=None,
             runtime_hooks=None)

a.datas += [
    ('VERSION', 'grow/VERSION', 'DATA'),
    ('server/templates/error.html', 'grow/server/templates/error.html', 'DATA'),
    ('data/cacerts.txt', 'grow/data/cacerts.txt', 'DATA'),
]

def get_crypto_path():
  import Crypto
  crypto_path = Crypto.__path__[0]
  return crypto_path

dict_tree = Tree(get_crypto_path(), prefix='Crypto', excludes=["*.pyc"])
a.datas += dict_tree

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
