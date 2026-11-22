import importlib
import importlib.metadata

try:
    __version__ = importlib.metadata.version('grow')
except importlib.metadata.PackageNotFoundError:
    __version__ = '2.3.0'

_LAZY_EXPORTS = {
    'Pod': ('grow.pods.pods', 'Pod'),
    'Preprocessor': ('grow.preprocessors.base', 'BasePreprocessor'),
    'Translator': ('grow.translators.base', 'Translator'),
}


def __getattr__(name):
    if name in _LAZY_EXPORTS:
        module_name, attr_name = _LAZY_EXPORTS[name]
        module = importlib.import_module(module_name)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


__all__ = ['Pod', 'Preprocessor', 'Translator', '__version__']
