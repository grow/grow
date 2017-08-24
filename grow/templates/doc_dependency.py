"""Utility class for tracking a doc dependency."""


# pylint: disable=too-few-public-methods
class DocDependency(object):
    """Used to easily track a dependencies for a document."""

    def __init__(self, doc):
        self.doc = doc
        self.dependency_graph = self.doc.pod.podcache.dependency_graph if doc else None

    def __call__(self, pod_path):
        if self.dependency_graph and pod_path:
            self.dependency_graph.add(self.doc.pod_path, pod_path)
