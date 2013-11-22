from grow.deployments import base
from grow.deployments import google_cloud_storage_from_app_engine


class GrowChannelFromAppEngineDeployment(google_cloud_storage_from_app_engine.GoogleStorageFromAppEngineDeployment):

  def __init__(self, bucket_name, keys):
    self.bucket_name = bucket_name
    self.keys = keys
#    super(GrowChannelFromAppEngineDeployment, self).__init__(self, bub
