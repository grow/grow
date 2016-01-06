from grow.pods.preprocessors import google_drive
from grow.pods.preprocessors import sass_preprocessor
from protorpc import protojson
import json

_preprocessor_kinds_to_classes = {}

_builtins = (
    google_drive.GoogleDocsPreprocessor,
    google_drive.GoogleSheetsPreprocessor,
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
    class_obj = _preprocessor_kinds_to_classes.get(kind)
    if class_obj is None:
        raise ValueError('No preprocessor for "{}".'.format(kind))
    if isinstance(config, dict):
        config = json.dumps(config)
        config = config_from_json(class_obj, config)
    return class_obj(pod, config, autorun=autorun, name=name)


def register_builtins():
    for builtin in _builtins:
        register_preprocessor(builtin)


register_builtins()
