import os
from grow.pods import errors
from grow.pods import pods
from grow.pods import storage



class Podgroup(object):

  def __init__(self, dirpath):
    self.dirpath = dirpath
    self.pods = []

  def load_pods_by_id(self, pod_ids):
    for pod_id in pod_ids:
      pod_dirpath = os.path.join(self.dirpath, pod_id)
      self.pods.append(pods.Pod(pod_dirpath))
    return self.pods

  def load_all_pods(self):
    podnames = storage.auto.listdir(self.dirpath)
    for podname in podnames:
      pod_dirpath = os.path.join(self.dirpath, podname)
      self.pods.append(pods.Pod(pod_dirpath))
    return self.pods

  def match_error(self, path, domain=None, status=None):
    for pod in self.pods:
      return pod.routes.match_error(path, domain=domain, status=status)

  def match(self, path, domain=None):
    for pod in self.pods:
      try:
        return pod.match(path, domain=domain)
      except errors.RouteNotFoundError:
        pass

  def get_loaded_pods(self):
    return self.pods
