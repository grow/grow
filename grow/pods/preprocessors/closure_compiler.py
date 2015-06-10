from grow.pods.preprocessors import base
from protorpc import messages
import os


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

  def run(self):
    message = (
        'The built-in Closure Compiler preprocessor has been deprecated.\n'
        'You must invoke the compiler using compiler.jar, such as through gulp or grunt.\n'
        'See: https://github.com/grow/pygrow/issues/77')
    raise base.PreprocessorError(message)

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

