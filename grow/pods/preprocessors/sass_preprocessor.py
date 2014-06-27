import logging
import os
import re
import sass
from grow.pods.preprocessors import base
from protorpc import messages

SUFFIXES = frozenset(['sass', 'scss'])
SUFFIX_PATTERN = re.compile('[.](' + '|'.join(map(re.escape, SUFFIXES)) + ')$')


class Config(messages.Message):
  sass_dir = messages.StringField(1)
  out_dir = messages.StringField(2)
  suffix = messages.StringField(3, default='.min.css')
  output_style = messages.StringField(4)


class SassPreprocessor(base.BasePreprocessor):
  KIND = 'sass'
  Config = Config

  def run(self):
    sass_dir = os.path.abspath(os.path.join(self.root, self.config.sass_dir.lstrip('/')))
    out_dir = os.path.abspath(os.path.join(self.root, self.config.out_dir.lstrip('/')))
    self.build_directory(sass_dir, out_dir)

  def build_directory(self, sass_path, css_path, _root_sass=None, _root_css=None):
    _root_sass = sass_path if _root_sass is None else _root_sass
    _root_css = css_path if _root_css is None else _root_css
    result = {}
    if not os.path.isdir(css_path):
      os.mkdir(css_path)
    for name in os.listdir(sass_path):
      if not SUFFIX_PATTERN.search(name) or name.startswith('_'):
        continue
      sass_fullname = os.path.join(sass_path, name)
      if os.path.isfile(sass_fullname):
        basename = os.path.splitext(name)[0]
        css_fullname = os.path.join(css_path, basename) + self.config.suffix
        try:
          css = sass.compile(filename=sass_fullname, include_paths=[_root_sass])
        except sass.CompileError as e:
          logging.error(str(e))
          return result
        with open(css_fullname, 'w') as css_file:
          css_file.write(css)
        result[sass_fullname] = css_fullname
      elif os.path.isdir(sass_fullname):
        css_fullname = os.path.join(css_path, name)
        subresult = self.build_directory(sass_fullname, css_fullname,
                      _root_sass, _root_css)
        result.update(subresult)
    for sass_path, out_path in result.iteritems():
      self.logger.info(
          'Compiled {} -> {}'.format(sass_path.replace(self.root, ''),
                                     out_path.replace(self.root, '')))
    return result

  def list_watched_dirs(self):
    return [self.config.sass_dir]
