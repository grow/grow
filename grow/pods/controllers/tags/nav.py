from grow.pods.blueprints import blueprints


def nav(collection, pod=None):
  blueprint = blueprints.Blueprint.get(nickname=collection, pod=pod)
  return [doc for doc in blueprint.list_documents()]
