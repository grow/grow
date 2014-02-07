def docs(collection, order_by=None, reverse=None, _pod=None):
  collection = _pod.get_collection(collection)
  return [doc for doc in collection.list_documents(order_by=order_by, reverse=reverse)]
