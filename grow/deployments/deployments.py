from grow.deployments.amazon_s3 import *
from grow.deployments.file_system import *
from grow.deployments.google_cloud_storage import *
from grow.deployments.google_cloud_storage_from_app_engine import *
from grow.deployments.podserver import *
from grow.deployments.zip_file import *



class Deployment(object):

  @classmethod
  def get(cls, kind, *args, **kwargs):
    if kind == 'gcs':
      return GoogleCloudStorageDeployment(*args, **kwargs)
    elif kind == 's3':
      return AmazonS3Deployment(*args, **kwargs)
    raise ValueError('No configuration exists for "{}".'.format(kind))
