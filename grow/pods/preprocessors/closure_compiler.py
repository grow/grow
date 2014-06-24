import closure
import os
import subprocess
from protorpc import messages
from grow.pods.preprocessors import base


class CompilationLevel(messages.Enum):
  SIMPLE_OPTIMIZATIONS = 1
  ADVANCED_OPTIMIZATIONS = 2
  WHITESPACE_ONLY = 3

_levels = {
    CompilationLevel.SIMPLE_OPTIMIZATIONS: 'SIMPLE_OPTIMIZATIONS',
    CompilationLevel.ADVANCED_OPTIMIZATIONS: 'ADVANCED_OPTIMIZATIONS',
    CompilationLevel.WHITESPACE_ONLY: 'WHITESPACE_ONLY',
}


class Config(messages.Message):
  compilation_level = messages.EnumField(
      CompilationLevel, 1, default=CompilationLevel.SIMPLE_OPTIMIZATIONS)
  externs = messages.StringField(2, repeated=True)
  js_output_file = messages.StringField(3)
  js = messages.StringField(4, repeated=True)
  output_wrapper = messages.StringField(5)


class ClosureCompilerPreprocessor(base.BasePreprocessor):
  KIND = 'closurecompiler'
  Config = Config

  def run(self):
    js_output_file = self.normalize_path(self.config.js_output_file)
    flags = [
        '--js_output_file', js_output_file,
        '--compilation_level', _levels[self.config.compilation_level],
    ]
    for js_file in [self.normalize_path(path) for path in self.config.js]:
      flags += ['--js', js_file]
    for extern in [self.normalize_path(path) for path in self.config.externs]:
      flags += ['--externs', extern]
    if self.config.output_wrapper:
      flags += ['--output_wrapper', self.config.output_wrapper]

    jar = closure.get_jar_filename()
    proc = subprocess.Popen(['java', '-jar', jar] + flags,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    err = proc.stderr.read()
    if err:
      self.logger.info(err)
    else:
      self.logger.info('Compiled: {}'.format(js_output_file))

  def list_watched_dirs(self):
    dirs = set()
    for js_file in self.config.js:
      dirs.add(os.path.dirname(js_file.lstrip('/')))
    return list(dirs)
