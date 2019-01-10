"""Dependency graph for content references."""

import fnmatch
import os
from collections import OrderedDict


class DependencyGraph(object):
    """Dependency graph for tracking relationships between the pod content."""

    def __init__(self):
        self._dependents = {}
        self._dependencies = {}
        self._is_dirty = False

    @staticmethod
    def normalize_path(pod_path):
        """Normalize a pod path."""
        if pod_path and not pod_path.startswith('/'):
            pod_path = '/{}'.format(pod_path)
        return pod_path

    @property
    def is_dirty(self):
        """Have the contents of the dependency graph been modified?"""
        return self._is_dirty

    def add_all(self, path_to_dependencies):
        """Add all from a dict of paths to dependencies."""
        for path, dependencies in path_to_dependencies.iteritems():
            self.add_references(path, dependencies)

    def add(self, source, reference):
        """Add reference made in a source file to the graph."""
        if not source or not reference:
            return

        source = DependencyGraph.normalize_path(source)
        reference = DependencyGraph.normalize_path(reference)

        if source not in self._dependencies:
            self._dependencies[source] = set()
        self._dependencies[source].add(reference)

        # Source are a dependent to themselves.
        if source not in self._dependents:
            self._dependents[source] = set()
        if source not in self._dependents[source]:
            self._is_dirty = True
        self._dependents[source].add(source)

        # Bi-directional dependency references for easier lookup.
        if reference not in self._dependents:
            self._dependents[reference] = set()
        if source not in self._dependents[reference]:
            self._is_dirty = True
        self._dependents[reference].add(source)

    def add_references(self, source, references):
        """Add references made in a source file to the graph."""
        if not references:
            return

        source = DependencyGraph.normalize_path(source)

        self._dependencies[source] = set(references)

        # Source are a dependent to themselves.
        if source not in self._dependents:
            self._dependents[source] = set()
        if source not in self._dependents[source]:
            self._is_dirty = True
        self._dependents[source].add(source)

        # Bi-directional dependency references for easier lookup.
        for reference in references:
            reference = DependencyGraph.normalize_path(reference)
            if reference not in self._dependents:
                self._dependents[reference] = set()

            # Track when the dependency graph has changed.
            if source not in self._dependents[reference]:
                self._is_dirty = True
            self._dependents[reference].add(source)

    def export(self):
        """Formats the dependency graph for export."""
        result = OrderedDict()
        for key in sorted(self._dependencies.iterkeys()):
            result[key] = sorted(list(self._dependencies[key]))
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
        """Get the dependencies of a specific source."""
        return self._dependencies.get(source, set())

    def mark_clean(self):
        """Mark that the dependency graph is clean."""
        self._is_dirty = False

    def match_dependents(self, reference):
        """
        Match dependents that rely upon the reference or a collection that
        contains the reference using a glob pattern.
        """
        matched_dependents = set()
        for dependent in self._dependents:
            if fnmatch.fnmatch(dependent, reference):
                matched_dependents = (
                    matched_dependents | self._dependents.get(dependent) | set([dependent]))
        return matched_dependents

    def reset(self):
        """Reset all the dependency tracking."""
        self._dependents = {}
        self._dependencies = {}
        self._is_dirty = False
