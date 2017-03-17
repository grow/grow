"""Dependency graph for content references."""

import os

class Error(Exception):
    pass


class BadFieldsError(Error, ValueError):
    pass


class DependencyGraph(object):
    def __init__(self):
        self.reset()

    def add_all(self, path_to_dependencies):
        """Add all from a dict of paths to dependencies."""

        for key, value in path_to_dependencies.iteritems():
            self.add_references(key, value)

    def add(self, source, reference):
        """Add reference made in a source file to the graph."""
        if not reference:
            return

        if source not in self._dependencies:
            self._dependencies[source] = set()
        self._dependencies[source].add(reference)

        # Bi-directional dependency references for easier lookup.
        if reference not in self._dependents:
            self._dependents[reference] = set()
        self._dependents[reference].add(source)

    def add_references(self, source, references):
        """Add references made in a source file to the graph."""
        if not references:
            return

        self._dependencies[source] = set(references)

        # Bi-directional dependency references for easier lookup.
        for reference in references:
            if reference not in self._dependents:
                self._dependents[reference] = set()
            self._dependents[reference].add(source)

    def export(self):
        result = {}

        for key in self._dependencies:
            values = list(self._dependencies[key])
            values.sort()
            result[key] = values

        return result

    def get_dependents(self, reference):
        """
        Gets dependents that rely upon the reference or a collection that
        contains the reference.
        """
        return (self._dependents.get(reference, set())
            | self._dependents.get(os.path.dirname(reference), set())
            | set([reference]))

    def get_dependencies(self, source):
        return self._dependencies.get(source, set())

    def reset(self):
        self._dependents = {}
        self._dependencies = {}
