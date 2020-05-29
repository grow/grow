"""Custom importing for pod extensions."""

import importlib.util
import os


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

        return getattr(module, extension_class_name)
