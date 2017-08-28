"""Testing utility for working with google service APIs."""

import mock


class GoogleServiceMock(object):
    """Utility for creating mocks for Google APIs."""

    @classmethod
    def get_batch_requests(cls, mocked):
        """Return all batch requests from the mocked object."""
        requests = []
        for _, kwargs in mocked.call_args_list:
            requests += kwargs['body']['requests']
        return requests

    @classmethod
    def mock_drive_service(cls, create=None):
        """Create mock for a google drive service."""
        mock_service = mock.Mock()

        mock_permissions = mock.Mock()
        mock_service.permissions.return_value = mock_permissions

        mock_permissions_create = mock.Mock()
        mock_permissions.create.return_value = mock_permissions_create

        mock_permissions_create.execute.return_value = create

        return {
            'service': mock_service,
            'permissions': mock_permissions,
            'permissions.create': mock_permissions_create,
        }

    @classmethod
    def mock_sheets_service(cls, create=None, get=None, values=None):
        """Create mock for a google sheets service."""
        mock_service = mock.Mock()

        mock_spreadsheets = mock.Mock()
        mock_service.spreadsheets.return_value = mock_spreadsheets

        mock_batch_update = mock.Mock()
        mock_spreadsheets.batchUpdate = mock_batch_update

        mock_create = mock.Mock()
        mock_create.execute.return_value = create
        mock_spreadsheets.create.return_value = mock_create

        mock_get = mock.Mock()
        mock_get.execute.return_value = get
        mock_spreadsheets.get.return_value = mock_get

        mock_values_get = mock.Mock()
        mock_values_get.execute.return_value = values
        mock_values = mock.Mock()
        mock_values.get.return_value = mock_values_get
        mock_spreadsheets.values.return_value = mock_values

        return {
            'service': mock_service,
            'spreadsheets': mock_spreadsheets,
            'spreadsheets.batchUpdate': mock_batch_update,
            'spreadsheets.create': mock_create,
            'spreadsheets.get': mock_get,
            'spreadsheets.values.get': mock_values_get,
        }
