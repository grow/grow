from grow.common import config
from grow.pods import errors
from grow.pods import pods
from grow.pods import storage
from grow.server import podgroups
from werkzeug import routing
import collections
import datetime
import json
import logging
import os
import pickle
import time


class Error(Exception):
  pass


class LiveRoutingMapNotFound(Error):
  pass


class PodNotLiveError(Error, IOError):
  pass


class AlreadyLaunchedError(Error, ValueError):
  pass


PodNotFoundError = errors.PodNotFoundError


LivePods = collections.namedtuple(
    'LivePods', ['pod_names_to_data', 'routing_map'])


def get_live_podgroup():
  live_pods = get_live_pods()
  pod_ids = ['{}.{}'.format(pod_name, data['changeset'])
             for pod_name, data in
             live_pods.pod_names_to_data.iteritems()]
  podgroup = podgroups.Podgroup(config.PODS_DIR)
  podgroup.load_pods_by_id(pod_ids)
  return podgroup


def get_live_pods():
  path = config.LIVE_PODS_FILE
  try:
    return pickle.load(storage.auto.open(path))
  except (storage.NotFoundError, IOError):
    raise LiveRoutingMapNotFound('No pods have been deployed.')


def launch(pod_name, changeset, opt_ttl=None, user=None):
  logging.info('Launching pod "{}" at changeset "{}".'.format(pod_name, changeset))
  try:
    live_pods = get_live_pods()
  # TODO(jeremydw): ImportError might just mean a depickling error!
  except (LiveRoutingMapNotFound, ImportError):
    live_pods = LivePods(pod_names_to_data={}, routing_map=routing.Map())

  canary_pod = pods.Pod('{}/{}'.format(config.PODS_DIR, changeset))
  if not canary_pod.exists:
    raise PodNotFoundError('Pod "{}" at changeset "{}" does not exist.'.format(
        pod_name, changeset))

#  canary_routing_map = canary_pod.get_routing_map()
#  composite_routing_map = live_routing_map + canary_routing_map
  if pod_name not in live_pods.pod_names_to_data:
    live_pods.pod_names_to_data[pod_name] = {}

  old_changeset = live_pods.pod_names_to_data[pod_name].get('changeset')
  if old_changeset:
    logging.info(
        'Replacing old changeset "{}" with new changeset "{}".'.
        format(old_changeset, changeset))
    if old_changeset == changeset:
      message = 'Pod "{}" is already launched at changeset "{}".'.format(
          pod_name, old_changeset)
      raise AlreadyLaunchedError(message)

  live_pods.pod_names_to_data[pod_name] = {
      'changeset': changeset,
      'launched': datetime.datetime.now(),
      'launched_by': user,
  }
  save_live_pods(live_pods)
  return pod_name, old_changeset, changeset


def save_live_pods(live_pods):
  file_obj = storage.auto.open(config.LIVE_PODS_FILE, mode='w')
  pickle.dump(live_pods, file_obj)
  file_obj.close()


def finalize_staged_files(pod, user=None):
  path = '{}/{}'.format(config.CHANGESETS_DIR, pod.nickname)
  try:
    changesets = json.load(storage.auto.open(path))
  except (storage.NotFoundError, IOError):
    changesets = {}
  changesets[pod.changeset] = {
      'staged': time.time(),
      'staged_by': user,
  }
  file_obj = storage.auto.open(path, mode='w')
  json.dump(changesets, file_obj, indent=2, separators=(',', ': '))
  file_obj.close()


def list_changesets_for_pod(pod_name):
  try:
    path = '{}/{}'.format(config.CHANGESETS_DIR, pod_name)
    changesets = json.load(storage.auto.open(path))
    for changeset, data in changesets.iteritems():
      # TODO: remove this
      if 'staged' in data:
        data['staged'] = datetime.datetime.fromtimestamp(data['staged'])
    return changesets
  except (storage.NotFoundError, IOError):
    raise PodNotFoundError(
        'Pod "{}" was not found, or it may not have been finalized upon '
        'upload.'.format(pod_name))


def stage(pod_name, changeset, pod_path, content):
  if not pod_path.startswith('/'):
    raise ValueError('Pod path "{}" must start with "/".'.format(pod_path))
  path = '/growlaunches/pods/{}.{}{}'.format(pod_name, changeset, pod_path)
  file_obj = storage.auto.write(path, content)
  file_obj.close()

  path = '{}/{}'.format(config.CHANGESETS_DIR, pod_name)
  try:
    changesets = json.load(storage.auto.open(path))
  except (storage.NotFoundError, IOError):
    changesets = {}
  changesets[changeset] = {}
  file_obj = storage.auto.open(path, mode='w')
  json.dump(changesets, file_obj, indent=2, separators=(',', ': '))
  file_obj.close()

  return path, file_obj


def takedown(pod_name, opt_ttl=None):
  live_pods = get_live_pods()
  if pod_name not in live_pods.pod_names_to_data:
    raise PodNotLiveError(
        'Pod "{}" is not launched, so it cannot be taken down.'.format(pod_name))
  data = live_pods.pod_names_to_data[pod_name]
  logging.info(
      'Taking down "{}", which was launched at changeset "{}"'.format(
      pod_name, data['changeset']))
  del live_pods.pod_names_to_data[pod_name]
  save_live_pods(live_pods)
  return data


def list_staged_pods():
  pod_names = storage.auto.listdir(config.CHANGESETS_DIR)
  return [os.path.basename(pod_name) for pod_name in pod_names]
