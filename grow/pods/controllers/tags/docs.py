from grow.pods.collectionz import collectionz


def docs(collection, order_by=None, reverse=None, _pod=None):
  collection = collectionz.Collection.get(collection_path=collection, pod=_pod)
  return [doc for doc in collection.list_documents(order_by=order_by, reverse=reverse)]
