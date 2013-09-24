from grow.pods.blueprints import blueprints


def nav(blueprint=None, pod=None):
  blueprint = blueprints.Blueprint.get(nickname=blueprint, pod=pod)
  return [doc.to_message() for doc in blueprint.list_documents()]
