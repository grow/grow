from . import blogger
from . import contentful_preprocessor
from . import google_drive
from . import gulp
from . import sass_preprocessor
from grow.common import utils
from protorpc import protojson
import json

_preprocessor_kinds_to_classes = {}

_builtins = (
    blogger.BloggerPreprocessor,
    contentful_preprocessor.ContentfulPreprocessor,
    google_drive.GoogleDocsPreprocessor,
    google_drive.GoogleSheetsPreprocessor,
    gulp.GulpPreprocessor,
    sass_preprocessor.SassPreprocessor,
)


def register_preprocessor(class_obj):
    _preprocessor_kinds_to_classes[class_obj.KIND] = class_obj


def config_from_json(preprocessor_class, content):
    config_class = preprocessor_class.Config
    return protojson.decode_message(config_class, content)


def make_preprocessor(kind, config, pod):
    autorun = config.pop('autorun', True)
    name = config.pop('name', None)
    tags = config.pop('tags', None)
    inject = config.pop('inject', False)
    class_obj = _preprocessor_kinds_to_classes.get(kind)
    if class_obj is None:
        raise ValueError('No preprocessor for "{}".'.format(kind))
    if isinstance(config, dict):
        config = json.dumps(config)
        config = config_from_json(class_obj, config)
    return class_obj(pod, config, autorun=autorun, name=name, tags=tags, inject=inject)


def register_builtins():
    for builtin in _builtins:
        register_preprocessor(builtin)


def register_extensions(extension_paths, pod_root):
    for path in extension_paths:
        cls = utils.import_string(path, [pod_root])
        register_preprocessor(cls)


register_builtins()
