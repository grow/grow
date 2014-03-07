from grow.pods.preprocessors import sass_preprocessor
from grow.pods.preprocessors import closure_compiler



class Preprocessor(object):

  @classmethod
  def get(self, kind, *args, **kwargs):
    if kind == sass_preprocessor.SassPreprocessor.KIND:
      return sass_preprocessor.SassPreprocessor(*args, **kwargs)
    elif kind == closure_compiler.ClosureCompiler.KIND:
      return closure_compiler.ClosureCompilerPreprocessor(*args, **kwargs)
    raise ValueError('Invalid preprocessor: {}'.format(kind))
