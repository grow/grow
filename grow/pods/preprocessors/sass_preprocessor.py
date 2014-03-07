import logging
import os
import re
import sass
from grow.pods.preprocessors import base

SUFFIXES = frozenset(['sass', 'scss'])
SUFFIX_PATTERN = re.compile('[.](' + '|'.join(map(re.escape, SUFFIXES)) + ')$')



class SassPreprocessor(base.BasePreprocessor):

  KIND = 'sass'

  def set_params(self, sass_dir, out_dir, suffix='.min.css', output_style=None):
    self.suffix = suffix
    self.sass_dir = sass_dir
    self.out_dir = out_dir
    self.output_style = output_style

  def run(self):
    sass_dir = os.path.abspath(os.path.join(self.pod.root, self.sass_dir.lstrip('/')))
    out_dir = os.path.abspath(os.path.join(self.pod.root, self.out_dir.lstrip('/')))
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
        css_fullname = os.path.join(css_path, os.path.splitext(name)[0]) + self.suffix
        css = sass.compile(filename=sass_fullname, include_paths=[_root_sass])
        with open(css_fullname, 'w') as css_file:
          css_file.write(css)
        result[sass_fullname] = css_fullname
      elif os.path.isdir(sass_fullname):
        css_fullname = os.path.join(css_path, name)
        subresult = self.build_directory(sass_fullname, css_fullname,
                      _root_sass, _root_css)
        result.update(subresult)
    for sass_path, out_path in result.iteritems():
      logging.info('Compiled {} -> {}'.format(sass_path.replace(self.pod.root, ''),
                                              out_path.replace(self.pod.root, '')))
    return result

  def list_watched_dirs(self):
    return [self.sass_dir]
