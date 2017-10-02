"""Routes trie for mapping grow documents to paths."""

import collections


URL_SEPARATOR = '/'


class Error(Exception):
    """Base routes error."""
    pass


class PathConflictError(Error):
    """Error when there is a conflict of paths in the routes trie."""

    def __init__(self, path, value):
        super(PathConflictError, self).__init__(
            'Path already exists: {} ({})'.format(path, value))
        self.path = path
        self.value = value


class Routes(object):
    """Routes container for mapping paths to documents."""

    def __init__(self):
        self._root = RouteTrie()

    def __len__(self):
        i = 0
        for _ in self.nodes:
            i = i + 1
        return i

    @property
    def nodes(self):
        """Generator for returning all the nodes in the routes."""
        for item in self._root.nodes:
            yield item

    @property
    def paths(self):
        """Generator for returning all the paths in the routes."""
        for path, _ in self._root.nodes:
            yield path

    def add(self, path, value):
        """Adds a document to the routes trie."""
        if not path:
            return
        self._root.add(path, value)

    def match(self, path):
        """Uses a path to attempt to match a path in the routes."""
        return self._root.match(path)

    def remove(self, path):
        """Removes a path from the routes."""
        return self._root.remove(path)

    def update(self, other):
        """Allow updating the current routes with other Routes."""
        # Add all the nodes from the other Routes.
        for item in other.nodes:
            self.add(*item)

    def __add__(self, other):
        """Allow adding routes togethers to form a new routes."""
        routes = self.__class__()
        # Add all the nodes from the current Routes.
        for item in self.nodes:
            routes.add(*item)
        # Add all the nodes from the other Routes.
        for item in other.nodes:
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
    def nodes(self):
        """Generator for returning all nodes in the trie."""
        for item in self._root.nodes:
            yield item

    def add(self, path, value):
        """Add a new doc to the route trie."""
        segments = self.segments(path)
        self._root.add(segments, path, value)

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
        self.value = None
        self._children = {}

    @property
    def nodes(self):
        """Generator for walking through the node nodes.

        Yields:
            Path, value at this node and all children.
        """
        if self.path is not None:
            yield self.path, self.value

        # Yield nodes in the path order.
        for key in sorted(self._children):
            for item in self._children[key].nodes:
                yield item

    def add(self, segments, path, value):
        """Recursively add into the trie based upon the given segments."""
        if not segments:
            if self.value:
                raise PathConflictError(path, value)
            self.path = path
            self.value = value
            return

        segment = segments.popleft()

        # Add a normal node.
        if segment not in self._children:
            self._children[segment] = RouteNode()
        self._children[segment].add(segments, path, value)

    def match(self, segments):
        """Performs the trie matching to find a doc in the trie."""
        if not segments:
            return self.path, self.value
        segment = segments.popleft()
        if segment in self._children:
            return self._children[segment].match(segments)
        return None, None

    def remove(self, segments):
        """Finds and removes a path in the trie."""
        if not segments:
            removed = self.path, self.value
            self.path = None
            self.value = None
            return removed
        segment = segments.popleft()
        if segment in self._children:
            return self._children[segment].remove(segments)
        return None, None
