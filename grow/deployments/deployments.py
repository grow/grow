import json
from .destinations import amazon_s3
from .destinations import local
from .destinations import google_cloud_storage
from .destinations import zip_file
from .destinations import scp
from protorpc import protojson

_deployment_names_to_classes = {}

_builtins = (
    amazon_s3.AmazonS3Deployment,
    local.LocalDeployment,
    google_cloud_storage.GoogleCloudStorageDeployment,
    zip_file.ZipFileDeployment,
    scp.ScpDeployment)


def register_deployment(class_obj):
  _deployment_names_to_classes[class_obj.NAME] = class_obj


def register_builtins():
  for builtin in _builtins:
    _deployment_names_to_classes[builtin.NAME] = builtin


def make_deployment(name, config):
  class_obj = _deployment_names_to_classes.get(name)
  if isinstance(config, dict):
    config = json.dumps(config)
    config = config_from_json(class_obj, config)
  if class_obj:
    return class_obj(config)
  raise ValueError('No configuration exists for "{}".'.format(name))


def config_from_json(deployment_class, content):
  config_class = deployment_class.Config
  return protojson.decode_message(config_class, content)


register_builtins()
