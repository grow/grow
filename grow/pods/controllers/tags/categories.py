from grow.pods.blueprints import blueprints
import itertools


def categories(collection=None, collections=None, reverse=None, order_by=None, _pod=None):
  if isinstance(collection, blueprints.Blueprint):
    blueprint = collection
  elif isinstance(collection, basestring):
    blueprint = blueprints.Blueprint.get(collection_path=collection, pod=_pod)
  else:
    raise ValueError('"{}" must be a Collection or collection path.'.format(collection))

  category_list = blueprint.list_categories()
  def order_func(doc):
    return category_list.index(doc.category)

  docs = [doc for doc in blueprint.list_documents(reverse=reverse, order_by='order')]
  docs = sorted(docs, key=order_func)
  items = itertools.groupby(docs, key=order_func)
  return ((category_list[index], pages) for index, pages in items)
