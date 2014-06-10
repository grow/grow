from grow.pods.collectionz import collectionz
import collections
import itertools
import jinja2
import markdown



def categories(collection=None, collections=None, reverse=None, order_by=None, _pod=None):
  if isinstance(collection, collectionz.Collection):
    collection = collection
  elif isinstance(collection, basestring):
    collection = _pod.get_collection(collection)
  else:
    text = '{} must be a Collection instance or a collection path, found: {}.'
    raise ValueError(text.format(collection, type(collection)))

  category_list = collection.list_categories()
  def order_func(doc):
    return category_list.index(doc.category)

  docs = [doc for doc in collection.list_documents(reverse=reverse, order_by='order')]
  docs = sorted(docs, key=order_func)
  items = itertools.groupby(docs, key=order_func)
  return ((category_list[index], pages) for index, pages in items)


def docs(collection, locale=None, order_by=None, _pod=None):
  collection = _pod.get_collection(collection)
  return collection.search_docs(locale=locale, order_by=order_by)


def markdown_filter(value):
  return markdown.markdown(value.decode('utf-8'))


def static(path, _pod=None):
  # TODO(jeremydw): Implement this.
  return path


def get_doc(pod_path, locale=None, _pod=None):
  return _pod.get_doc(pod_path, locale=locale)


class Menu(object):

  def __init__(self):
    self.items = collections.OrderedDict()

  def build(self, nodes):
    self._recursive_build(self.items, None, nodes)

  def iteritems(self):
    return self.items.iteritems()

  def _recursive_build(self, tree, parent, nodes):
    children = [n for n in nodes if n.parent == parent]
    for child in children:
      tree[child] = collections.OrderedDict()
      self._recursive_build(tree[child], child, nodes)


def nav(collection=None, locale=None, _pod=None):
  collection_obj = _pod.get_collection('/content/' + collection)
  results = collection_obj.search_docs(order_by='order', locale=locale)
  menu = Menu()
  menu.build(results)
  return menu


def breadcrumb(doc, _pod=None):
  pass


def url(pod_path, locale=None, _pod=None):
  doc = _pod.get_doc(pod_path, locale=locale)
  return doc.url


@jinja2.contextfilter
def render_filter(ctx, template):
  if isinstance(template, basestring):
    template = jinja2.Template(template)
  return template.render(ctx)
