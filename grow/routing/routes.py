"""Routes trie for mapping grow documents to paths."""

import collections


PREFIX_PARAMETER = ':'
PREFIX_WILDCARD = '*'
URL_SEPARATOR = '/'


class Error(Exception):
    """Base routes error."""
    pass


class PathConflictError(Error):
    """Error when there is a conflict of paths in the routes trie."""

    def __init__(self, path, value, existing):
        super(PathConflictError, self).__init__(
            'Path already exists: {} ({} != {})'.format(path, existing, value))
        self.path = path
        self.value = value


class PathParamNameConflictError(Error):
    """Error when there is a conflict of path param names in the routes trie."""

    def __init__(self, path, new_param, existing_param):
        super(PathParamNameConflictError, self).__init__(
            'Path param differs from existing param: {} ({} vs {})'.format(
                path, new_param, existing_param))
        self.path = path
        self.new_param = new_param
        self.existing_param = existing_param


class Routes(object):
    """Routes container for mapping paths to documents."""

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

    def __init__(self):
        self._root = RouteTrie()

    def __len__(self):
        return len(self._root)

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

    def reset(self):
        """Resets the routes."""
        self._root = RouteTrie()

    def remove(self, path):
        """Removes a path from the routes."""
        return self._root.remove(path)

    def update(self, other):
        """Allow updating the current routes with other Routes."""
        # Add all the nodes from the other Routes.
        for item in other.nodes:
            self.add(*item)


class RoutesSimple(Routes):
    """Routes container for mapping simple paths to values."""

    def __init__(self):
        super(RoutesSimple, self).__init__()
        self._root = RoutesDict()

    def reset(self):
        """Resets the routes."""
        self._root = RoutesDict()


class RoutesDict(object):
    """Dictionary based routing tree for faster creation."""

    def __init__(self):
        self._root = {}

    def __len__(self):
        return len(self._root)

    @property
    def nodes(self):
        """Generator for returning all nodes in the trie."""
        for path in sorted(self._root):
            yield path, self._root[path]

    def add(self, path, value):
        """Add a new doc to the route trie."""
        if path in self._root and self._root[path] != value:
            raise PathConflictError(path, value, self._root[path])
        self._root[path] = value

    def match(self, path):
        """Matches a path against the known routes looking for a match."""
        value = self._root.get(path, None)
        if value is None:
            return None
        return MatchResult(path, value)

    def remove(self, path):
        """Removes a path from the trie."""
        value = self._root.pop(path, None)
        if value is None:
            return None
        return MatchResult(path, value)


class RouteTrie(object):
    """A trie for routes."""

    def __init__(self):
        self._root = RouteNode()

    def __len__(self):
        i = 0
        for _ in self.nodes:
            i = i + 1
        return i

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

    def __init__(self, param_name=None):
        super(RouteNode, self).__init__()
        self.path = None
        self.value = None
        self.param_name = param_name
        self._dynamic_children = {}
        self._static_children = {}

    def __repr__(self):
        return "<RouteNode({}, {})>".format(self.path, self.param_name)

    @property
    def nodes(self):
        """Generator for walking through the node nodes.

        Yields:
            Path, value at this node and all children.
        """
        if self.path is not None:
            yield self.path, self.value

        # Yield nodes in the path order.
        for key in sorted(self._static_children):
            for item in self._static_children[key].nodes:
                yield item

        for key in sorted(self._dynamic_children):
            for item in self._dynamic_children[key].nodes:
                yield item

    def _dynamic_params(self, matched, last_segment):
        # Parameterized nodes need to add in their param when returning.
        if matched is not None and self.param_name:
            matched.params[self.param_name] = last_segment
        return matched

    def add(self, segments, path, value):
        """Recursively add into the trie based upon the given segments."""

        if not segments:
            if self.path and self.value != value:
                raise PathConflictError(path, value, self.value)
            self.path = path
            self.value = value
            return

        segment = segments.popleft()

        # Insert as a parameterized node.
        if segment and segment[0] is PREFIX_PARAMETER:
            segment = segment[1:]  # Don't need the prefix character.
            if PREFIX_PARAMETER in self._dynamic_children:
                # If there is already a prefix in use, cannot have a conflicting
                # param_name or it causes issues with params on match.
                if self._dynamic_children[PREFIX_PARAMETER].param_name != segment:
                    raise PathParamNameConflictError(
                        path, segment, self._dynamic_children[PREFIX_PARAMETER].param_name)
            if PREFIX_PARAMETER not in self._dynamic_children:
                new_node = RouteNode(param_name=segment)
                self._dynamic_children[PREFIX_PARAMETER] = new_node
            self._dynamic_children[PREFIX_PARAMETER].add(segments, path, value)
            return

        # Insert as a wildcard node.
        if segment and segment[0] is PREFIX_WILDCARD:
            segment = segment[1:]  # Don't need the prefix character.
            if (PREFIX_WILDCARD in self._dynamic_children
                    and self._dynamic_children[PREFIX_WILDCARD].value != value):
                raise PathConflictError(
                    path, value, self._dynamic_children[PREFIX_WILDCARD].value)
            new_node = RouteWildcardNode(param_name=segment or PREFIX_WILDCARD)
            new_node.add([], path, value)
            self._dynamic_children[PREFIX_WILDCARD] = new_node
            return

        # Add a static node.
        if segment not in self._static_children:
            self._static_children[segment] = RouteNode()
        self._static_children[segment].add(segments, path, value)

    def match(self, segments, last_segment=None):
        """Performs the trie matching to find a doc in the trie."""

        if not segments:
            # Check for removed nodes.
            if self.path is None:
                return None
            matched = MatchResult(self.path, self.value)
            return self._dynamic_params(matched, last_segment)

        segment = segments.popleft()

        # Match static children first, then fallback to dynamic.
        if segment in self._static_children:
            matched = self._static_children[segment].match(
                segments, last_segment=segment)
            if matched is not None:
                return self._dynamic_params(matched, last_segment)

        # Check if this is a parameterized segement.
        if PREFIX_PARAMETER in self._dynamic_children:
            matched = self._dynamic_children[PREFIX_PARAMETER].match(
                segments, last_segment=segment)
            if matched is not None:
                return self._dynamic_params(matched, last_segment)

        # Check for the wildcard catch all.
        if PREFIX_WILDCARD in self._dynamic_children:
            matched = self._dynamic_children[PREFIX_WILDCARD].match(
                segments, last_segment=segment)
            return self._dynamic_params(matched, last_segment)

        # Add the current segment back since this is not a match.
        segments.appendleft(segment)
        return None

    def remove(self, segments):
        """Finds and removes a path in the trie."""

        if not segments:
            removed = MatchResult(self.path, self.value)
            self.path = None
            self.value = None
            return removed
        segment = segments.popleft()

        # Static nodes.
        if segment in self._static_children:
            return self._static_children[segment].remove(segments)

        # Parameter nodes.
        if segment and segment[0] == PREFIX_PARAMETER:
            if PREFIX_PARAMETER in self._dynamic_children:
                return self._dynamic_children[PREFIX_PARAMETER].remove(segments)

        # Wildcard nodes.
        if segment and segment[0] == PREFIX_WILDCARD:
            if PREFIX_WILDCARD in self._dynamic_children:
                return self._dynamic_children[PREFIX_WILDCARD].remove(segments)

        return None


class RouteWildcardNode(RouteNode):
    """Individual wildcard node in the routes trie."""

    def match(self, segments, last_segment=None):
        """Matches the rest of the segments as the wildcard portion."""

        # Handle deleted node.
        if self.path is None:
            return None

        # Add the last segment back to be joined.
        if last_segment:
            segments.appendleft(last_segment)
        segment = URL_SEPARATOR.join(segments)

        return self._dynamic_params(
            MatchResult(self.path, self.value), segment)

    def remove(self, segments):
        """Finds and removes a path in the trie."""
        removed = MatchResult(self.path, self.value)
        self.path = None
        self.value = None
        return removed


class MatchResult(object):
    """Node information for a trie match."""

    def __init__(self, path, value, params=None):
        self.path = path
        self.value = value
        self.params = params if params is not None else {}
