import logging
import os
from grow.pods.preprocessors import base


class CompilationLevel(object):
  SIMPLE_OPTIMIZATIONS = 'SIMPLE_OPTIMIZATIONS'
  ADVANCED_OPTIMIZATIONS = 'ADVANCED_OPTIMIZATIONS'
  WHITESPACE_ONLY = 'WHITESPACE_ONLY'


class ClosureCompilerPreprocessor(base.BasePreprocessor):

  KIND = 'closure-compiler'

  def set_params(self, out_file, compilation_level=CompilationLevel.SIMPLE_OPTIMIZATIONS):
    self.out_file = out_file
    self.compilation_level = compilation_level

  def run(self):
    pass
    sass_dir = os.path.abspath(os.path.join(self.pod.root, self.sass_dir.lstrip('/')))
    out_dir = os.path.abspath(os.path.join(self.pod.root, self.out_dir.lstrip('/')))

  def list_watched_dirs(self):
    return [self.sass_dir]
