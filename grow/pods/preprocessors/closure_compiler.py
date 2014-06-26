import closure
import itertools
import os
import subprocess
from protorpc import messages
from grow.pods.preprocessors import base
from grow.common import utils

# Needed for code freezing.
from .closure_lib import closurebuilder


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
  KIND = 'closurecompiler'

  class Config(messages.Message):
    compilation_level = messages.EnumField(
        CompilationLevel, 1, default=CompilationLevel.SIMPLE_OPTIMIZATIONS)
    externs = messages.StringField(2, repeated=True)
    js_output_file = messages.StringField(3)
    js = messages.StringField(4, repeated=True)
    output_wrapper = messages.StringField(5)

  def build_flags(self):
    flags = []
    flags += ['--compilation_level', _levels[self.config.compilation_level]]
    for js_file in self.config.js:
      flags += ['--js', self.normalize_path(js_file)]
    for extern in self.config.externs:
      flags += ['--externs', self.normalize_path(extern)]
    if self.config.output_wrapper:
      flags += ['--output_wrapper', self.config.output_wrapper]
    return flags

  def _compile(self):
    jar = closure.get_jar_filename()
    proc = subprocess.Popen(['java', '-jar', jar] + self.build_flags(),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    err = proc.stderr.read()
    if err:
      raise base.PreprocessorError(err)
    else:
      return proc.stdout.read()

  def run(self):
    output = self._compile()
    js_output_file = self.normalize_path(self.config.js_output_file)
    self.pod.storage.write(js_output_file, output)
    self.logger.info('Compiled: {}'.format(js_output_file))

  def list_watched_dirs(self):
    dirs = set()
    for js_file in self.config.js:
      dirs.add(os.path.dirname(js_file.lstrip('/')))
    return list(dirs)



class ClosureBuilderPreprocessor(base.BasePreprocessor):
  KIND = 'closurebuilder'

  class Config(messages.Message):
    compiler_flags = messages.MessageField(ClosureCompilerPreprocessor.Config, 1)
    namespace = messages.StringField(2, repeated=True)
    root = messages.StringField(3, repeated=True)
    output_mode = messages.EnumField(OutputMode, 4, default=OutputMode.SCRIPT)
    input = messages.StringField(6, repeated=True)
    output_file = messages.StringField(7)

  def _compile(self):
    flags = []
    flags += ['--compiler_jar', closure.get_jar_filename()]
    flags += ['--output_mode', _output_modes[self.config.output_mode]]
    for root in self.config.root:
      flags += ['--root', self.normalize_path(root)]
    for input in self.config.input:
      flags += ['--input', self.normalize_path(input)]
    for namespace in self.config.namespace:
      flags += ['--namespace', self.normalize_path(namespace)]
    if self.config.compiler_flags:
      compiler_preprocessor = ClosureCompilerPreprocessor(self.pod, self.config.compiler_flags)
      compiler_flags = compiler_preprocessor.build_flags()
      for name, val in itertools.izip(*[iter(compiler_flags)]*2):
        compiler_flag = '{}="{}"'.format(name, val)
        flags += ['--compiler_flags', compiler_flag]

    builder_command = os.path.join(
        utils.get_grow_dir(), 'pods', 'preprocessors', 'closure_lib',
        'closurebuilder.py')
    self.logger.info('Running Closure Builder -> {}...'.format(self.config.output_file))
    proc = subprocess.Popen([builder_command] + flags,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    err = proc.stderr.read()
    print err
    result = proc.stdout.read()
    if result is None:
      raise base.PreprocessorError('Error')
    return result

  def run(self):
    output = self._compile()
    output_file = self.normalize_path(self.config.output_file)
    self.pod.storage.write(output_file, output)
    self.logger.info('Built: {}'.format(output_file))

  def list_watched_dirs(self):
    dirs = set()
    for path in self.config.input:
      dirs.add(os.path.dirname(path.lstrip('/')))
    return list(dirs)
