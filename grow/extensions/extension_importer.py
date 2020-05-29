"""Custom importing for pod extensions."""

import importlib.util
import os
import sys


class ExtensionImporter:
    """Custom find the extensions based on the pod path."""

    @staticmethod
    def find_extension(extension_ref, pod_root):
        """Using the pod path as the base to find the extension module."""
        extension_parts = extension_ref.split('.')
        extension_class_name = extension_parts.pop()
        module_name = extension_parts[-1]

        # Try first as the full module path.
        module_path = '{}{sep}{}.py'.format(
            pod_root, '/'.join(extension_parts), sep=os.path.sep)

        if not os.path.exists(module_path):
            module_path = '{}{sep}{}{sep}__init__.py'.format(
                pod_root, '/'.join(extension_parts), sep=os.path.sep)

        spec = importlib.util.spec_from_file_location(module_name, module_path)

        if not spec:
            raise ImportError(
                'Unable to load extension from {!r}'.format(extension_ref))

        # Import the module from the spec and execute to get access.
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # To prevent collisions of extensions between pod on the same process
        # the module keys need to be cleared.
        del sys.modules[module_name]
        ext_prefix = '{}.'.format(module_name)
        extension_keys = list(
            filter(lambda x: x.startswith(ext_prefix), sys.modules.keys()))
        for key in extension_keys:
            del sys.modules[key]

        return getattr(module, extension_class_name)
