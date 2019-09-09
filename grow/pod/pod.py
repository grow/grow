"""Grow pod container class."""

from grow.common import features as grow_features
from grow.common import logger as grow_logger
from grow.yaml import yaml_standard
from grow.performance import profile
from grow.pod import podspec
from grow.storage import storage


class Error(Exception):
    """Base pod error."""
    pass


class MissingPodspecError(Error):
    """No pod exists in root path."""
    pass


class Pod(grow_logger.Logger, profile.Profiler, storage.Storager, grow_features.Featurer):
    """Grow pod container."""

    def __init__(self, root_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_path = root_path

        if not self.storage.file_exists(podspec.POD_SPEC_FILE):
            raise MissingPodspecError(
                'Unable to find the {} file in the {} directory.'.format(
                    podspec.POD_SPEC_FILE, root_path))

        pod_spec_raw = self.storage.read_file(podspec.POD_SPEC_FILE)
        pod_spec_parsed = yaml_standard.load_yaml(pod_spec_raw)
        self.podspec = podspec.PodSpec(pod_spec_parsed)
