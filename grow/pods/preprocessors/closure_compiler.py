from grow.pods.preprocessors import base
from grow.common import utils
from protorpc import messages
import os
import subprocess
import time


class CompilationLevel(messages.Enum):
  SIMPLE_OPTIMIZATIONS = 1
  ADVANCED_OPTIMIZATIONS = 2
  WHITESPACE_ONLY = 3

_levels = {
    CompilationLevel.SIMPLE_OPTIMIZATIONS: 'SIMPLE_OPTIMIZATIONS',
    CompilationLevel.ADVANCED_OPTIMIZATIONS: 'ADVANCED_OPTIMIZATIONS',
    CompilationLevel.WHITESPACE_ONLY: 'WHITESPACE_ONLY',
}


class OutputMode(messages.Enum):
  LIST = 1
  SCRIPT = 2
  COMPILED = 3

_output_modes = {
    OutputMode.LIST: 'list',
    OutputMode.SCRIPT: 'script',
    OutputMode.COMPILED: 'compiled',
}


class ClosureCompilerPreprocessor(base.BasePreprocessor):
  KIND = 'closure_compiler'

  class Config(messages.Message):
    compilation_level = messages.EnumField(
        CompilationLevel, 1, default=CompilationLevel.SIMPLE_OPTIMIZATIONS)
    externs = messages.StringField(2, repeated=True)
    js_output_file = messages.StringField(3)
    js = messages.StringField(4, repeated=True)
    output_wrapper = messages.StringField(5)
    manage_closure_dependencies = messages.BooleanField(6)
    only_closure_dependencies = messages.BooleanField(7)
    generate_exports = messages.BooleanField(8)
    closure_entry_point = messages.StringField(9, repeated=True)
    angular_pass = messages.BooleanField(10)
    flagfile = messages.StringField(11)
    third_party = messages.BooleanField(12)

  def build_flags(self):
    flags = []
    flags += ['--compilation_level={}'.format(_levels[self.config.compilation_level])]
    for extern in self.config.externs:
      flags += ['--externs={}'.format(self.normalize_path(extern))]
    for js_file in self.config.js:
      flags += ['--js=\'{}\''.format(self.normalize_path(js_file))]
    for entry_point in self.normalize_multi(self.config.closure_entry_point):
      flags += ['--closure_entry_point={}'.format(entry_point)]
    if self.config.output_wrapper:
      flags += ['--output_wrapper={}'.format(self.config.output_wrapper)]
    if self.config.manage_closure_dependencies:
      flags += ['--manage_closure_dependencies']
    if self.config.only_closure_dependencies:
      flags += ['--only_closure_dependencies']
    if self.config.generate_exports:
      flags += ['--generate_exports']
    if self.config.angular_pass:
      flags += ['--angular_pass']
    if self.config.third_party:
      flags += ['--third_party']
    if self.config.flagfile:
      flags += ['--flagfile=\'{}\''.format(self.config.flagfile)]
    return flags

  def _compile(self):
    jar = os.path.join(utils.get_grow_dir(), 'pods', 'preprocessors', 'closure_lib',
                       'compiler.jar')
    command = ['java', '-jar', jar] + self.build_flags()
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    err = proc.stderr.read()
    if err:
      raise base.PreprocessorError(err)
    else:
      return proc.stdout.read()

  def run(self):
    js_output_file = self.normalize_path(self.config.js_output_file)
    self.logger.info('Compiling: {}'.format(js_output_file))
    output = self._compile()
    self.pod.storage.write(js_output_file, output)
    self.logger.info('Compiled: {}'.format(js_output_file))

  def list_watched_dirs(self):
    dirs = set()
    for js_file in self.config.js:
      if js_file.startswith('/'):
        dirs.add(os.path.dirname(js_file.lstrip('/')))
    return list(dirs)

  def normalize_multi(self, val):
    if isinstance(val, basestring):
      return [val]
    return val

