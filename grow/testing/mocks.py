"""Mocks for testing grow functionality."""

import mock


def mock_collection(basename=None, root=None):
    """Mock grow collection."""
    collection = mock.Mock()
    type(collection).basename = mock.PropertyMock(return_value=basename)
    type(collection).root = mock.PropertyMock(return_value=root)
    return collection


def mock_doc(pod=None, base=None, date=None, locale=None,
             collection_base_path=None, collection=None, view=None,
             serving_path=None, path_params=None):
    """Mock grow document."""
    doc = mock.Mock()
    type(doc).base = mock.PropertyMock(return_value=base)
    type(doc).date = mock.PropertyMock(return_value=date)
    type(doc).pod = mock.PropertyMock(return_value=pod)
    type(doc).locale = mock.PropertyMock(return_value=locale)
    type(doc).path_params = mock.PropertyMock(return_value=path_params)
    if not collection:
        collection = mock_collection()
    type(doc).collection = mock.PropertyMock(return_value=collection)
    type(doc).collection_base_path = mock.PropertyMock(
        return_value=collection_base_path)
    type(doc).view = mock.PropertyMock(return_value=view or '/view/base.html')
    doc.has_serving_path.return_value = bool(serving_path)
    doc.get_serving_path.return_value = serving_path
    return doc


def mock_env(fingerprint=None):
    """Mock grow environment."""
    env = mock.Mock()
    prop_fingerprint = mock.PropertyMock(return_value=fingerprint)
    type(env).fingerprint = prop_fingerprint
    return env


def mock_locale(identifier, alias=None):
    """Mock locale object."""
    # pylint: disable=unused-argument
    def __str__(self):
        return identifier
    locale = mock.Mock()
    locale.__str__ = __str__
    type(locale).alias = mock.PropertyMock(return_value=alias)
    type(locale).alias = mock.PropertyMock(return_value=alias)
    return locale


def mock_pod(podspec=None, env=None):
    """Mock grow pod."""
    pod = mock.Mock()
    mock_podspec = mock.Mock()
    if not podspec:
        podspec = {}
    mock_podspec.get_config.return_value = podspec
    type(pod).podspec = mock.PropertyMock(return_value=mock_podspec)
    if not env:
        env = mock_env()
    type(pod).env = mock.PropertyMock(return_value=env)
    return pod


def mock_static_doc(pod, path_format=None, locale=None):
    """Mock grow static document."""
    doc = mock.Mock()
    type(doc).pod = mock.PropertyMock(return_value=pod)
    type(doc).path_format = mock.PropertyMock(return_value=path_format)
    type(doc).locale = mock.PropertyMock(return_value=locale)
    return doc
