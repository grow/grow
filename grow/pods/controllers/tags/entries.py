from grow.pods.blueprints import blueprints


def entries(collection, order_by=None, reverse=None, _pod=None):
  blueprint = blueprints.Blueprint.get(collection_path=collection, pod=_pod)
  return [doc for doc in blueprint.list_documents(order_by=order_by, reverse=reverse)]
