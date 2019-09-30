from .destinations import amazon_s3
from .destinations import git_destination
from .destinations import google_cloud_storage
from .destinations import local
from .destinations import scp
from .destinations import webreview_destination
from protorpc import protojson
import json

_destination_kinds_to_classes = None

_builtins = (
    amazon_s3.AmazonS3Destination,
    webreview_destination.WebReviewDestination,
    webreview_destination.LegacyJetwayDestination,
    git_destination.GitDestination,
    local.LocalDestination,
    google_cloud_storage.GoogleCloudStorageDestination,
    scp.ScpDestination)


def register_destination(class_obj):
    _destination_kinds_to_classes[class_obj.KIND] = class_obj


def register_builtins():
    global _destination_kinds_to_classes
    if _destination_kinds_to_classes is None:
        _destination_kinds_to_classes = {}
    for builtin in _builtins:
        register_destination(builtin)


def make_deployment(kind, config, name='default'):
    if _destination_kinds_to_classes is None:
        register_builtins()
    class_obj = _destination_kinds_to_classes.get(kind)
    if class_obj is None:
        raise ValueError('No configuration exists for "{}".'.format(kind))
    if isinstance(config, dict):
        config = json.dumps(config)
        config = config_from_json(class_obj, config)
    return class_obj(config, name=name)


def config_from_json(deployment_class, content):
    config_class = deployment_class.Config
    return protojson.decode_message(config_class, content)
