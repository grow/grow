"""Routes trie for mapping grow documents to paths."""

import collections


URL_SEPARATOR = '/'


class Error(Exception):
    """Base routes error."""
    pass


class PathConflictError(Error):
    """Error when there is a conflict of paths in the routes trie."""

    def __init__(self, path, pod_path, locale):
        super(PathConflictError, self).__init__(
            'Path already exists: {} ({} : {})'.format(path, pod_path, locale))
        self.path = path
        self.pod_path = pod_path
        self.locale = locale


class Routes(object):
    """Routes container for mapping paths to documents."""

    def __init__(self):
        self._root = RouteTrie()

    @property
    def docs(self):
        """Generator for returning all the docs in the routes."""
        for item in self._root.docs:
            yield item

    def add(self, path, pod_path, locale):
        """Adds a document to the routes trie."""
        if not path:
            return
        self._root.add(path, pod_path, locale)

    def add_doc(self, doc):
        """Adds a document to the routes trie."""
        self.add(doc.get_serving_path(), doc.pod_path, str(doc.locale))

    def match(self, path):
        """Uses a path to attempt to match a path in the routes."""
        return self._root.match(path)

    def remove(self, path):
        """Removes a path from the routes."""
        return self._root.remove(path)

    def update(self, other):
        """Allow updating the current routes with other Routes."""
        # Add all the docs from the other Routes.
        for item in other.docs:
            self.add(*item)

    def __add__(self, other):
        """Allow adding routes togethers to form a new routes."""
        routes = self.__class__()
        # Add all the docs from the current Routes.
        for item in self.docs:
            routes.add(*item)
        # Add all the docs from the other Routes.
        for item in other.docs:
            routes.add(*item)
        return routes


class RouteTrie(object):
    """A trie for routes."""

    def __init__(self):
        self._root = RouteNode()

    @staticmethod
    def clean_path(path):
        """Clean the path to work with the trie."""
        if path and path[0] == URL_SEPARATOR:
            path = path[1:]
        if path and path[-1] == URL_SEPARATOR:
            path = path[0:-1]
        return path

    @staticmethod
    def segments(path):
        """Clean the and break the path to work with the trie."""
        path = RouteTrie.clean_path(path)
        return collections.deque(path.split(URL_SEPARATOR))

    @property
    def docs(self):
        """Generator for returning all docs in the trie."""
        for item in self._root.docs:
            yield item

    def add(self, path, pod_path, locale):
        """Add a new doc to the route trie."""
        segments = self.segments(path)
        self._root.add(segments, path, pod_path, locale)

    def match(self, path):
        """Matches a path against the known trie looking for a match."""
        segments = self.segments(path)
        return self._root.match(segments)

    def remove(self, path):
        """Removes a path from the trie."""
        segments = self.segments(path)
        return self._root.remove(segments)


class RouteNode(object):
    """Individual node in the routes trie."""

    def __init__(self):
        super(RouteNode, self).__init__()
        self.path = None
        self.pod_path = None
        self.locale = None
        self._children = {}

    @property
    def docs(self):
        """Generator for walking through the node docs.

        Yields:
            Path, pod_path, and locale at this node and all children.
        """
        if self.path is not None:
            yield self.path, self.pod_path, self.locale

        # Yield docs in the path order.
        for key in sorted(self._children):
            for item in self._children[key].docs:
                yield item

    def add(self, segments, path, pod_path, locale):
        """Recursively add into the trie based upon the given segments."""
        if not segments:
            if self.pod_path:
                raise PathConflictError(path, pod_path, locale)
            self.pod_path = pod_path
            self.locale = locale
            self.path = path
            return

        segment = segments.popleft()

        # Add a normal node.
        if segment not in self._children:
            self._children[segment] = RouteNode()
        self._children[segment].add(segments, path, pod_path, locale)

    def match(self, segments):
        """Performs the trie matching to find a doc in the trie."""
        if not segments:
            return self.path, self.pod_path, self.locale
        segment = segments.popleft()
        if segment in self._children:
            return self._children[segment].match(segments)
        return None, None, None

    def remove(self, segments):
        """Finds and removes a path in the trie."""
        if not segments:
            removed = self.path, self.pod_path, self.locale
            self.path = None
            self.pod_path = None
            self.locale = None
            return removed
        segment = segments.popleft()
        if segment in self._children:
            return self._children[segment].remove(segments)
        return None, None, None
