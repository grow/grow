from grow.pods.preprocessors import sass_preprocessor



class Preprocessor(object):

  @classmethod
  def get(self, kind, *args, **kwargs):
    if kind == 'sass':
      return sass_preprocessor.SassPreprocessor(*args, **kwargs)
    raise ValueError('Invalid preprocessor: {}'.format(kind))
