from grow.pods.blueprints import blueprints


def entries(blueprint=None, order_by=None, reverse=None, pod=None):
  blueprint = blueprints.Blueprint.get(collection_path=blueprint, pod=pod)
  return [doc for doc in blueprint.list_documents(order_by=order_by, reverse=reverse)]
