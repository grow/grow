from . import google_translator_toolkit
from . import google_sheets
from grow.preprocessors import google_drive
from grow.common import oauth
from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
from nose.plugins import skip
import mock
import time
import unittest


class GoogleSheetsTranslatorTestCase(unittest.TestCase):

    def _mock_drive_service(self, create=None):
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

    def _mock_sheets_service(self, create=None, get=None):
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

        return {
            'service': mock_service,
            'spreadsheets': mock_spreadsheets,
            'spreadsheets.batchUpdate': mock_batch_update,
            'spreadsheets.create': mock_create,
            'spreadsheets.get': mock_get,
        }

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    @mock.patch.object(google_sheets.GoogleSheetsTranslator, '_generate_new_sheet_id')
    @mock.patch.object(google_sheets.GoogleSheetsTranslator, '_create_service')
    @mock.patch.object(google_drive.BaseGooglePreprocessor, 'create_service')
    def test_create_sheet(self, mock_create_service_drive, mock_create_service_sheets, mock_generate_new_sheet_id):
        mock_drive_service = self._mock_drive_service()
        mock_sheets_service = self._mock_sheets_service(create={
            'spreadsheetId': '98765',
            'sheets': [
                {
                    'properties': {
                        'sheetId': '1234',
                        'title': 'es',
                    }
                }
            ]
        }, get={
            'spreadsheetId': 76543,
        })
        mock_create_service_drive.return_value = mock_drive_service['service']
        mock_create_service_sheets.return_value = mock_sheets_service[
            'service']
        mock_generate_new_sheet_id.side_effect = [765, 654, 543, 432, 321]

        translator = self.pod.get_translator('google_sheets')
        translator.upload()

        mock_sheets_service['spreadsheets.batchUpdate'].assert_called_with(
            spreadsheetId='98765',
            body={
                'requests': [{
                    'addSheet': {
                        'properties': {
                          'gridProperties': {
                              'columnCount': 4,
                              'rowCount': 2,
                              'frozenColumnCount': 1,
                              'frozenRowCount': 1
                          },
                            'sheetId': 765,
                            'title': 'fr'
                        }
                    }
                }, {
                    'appendCells': {
                        'fields': 'userEnteredValue',
                        'rows': [{
                            'values': [{
                                'userEnteredValue': {
                                  'stringValue': 'en'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': 'fr'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': 'Extracted comments'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': 'Reference'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'About'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'About us'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'AboutDE'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Bar'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Contact'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Foo'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Goodnight Moon!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Hello World 2!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Hello World!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Higher Priority'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Home page'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Introduction'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Lower Priority'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Newest!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }],
                        'sheetId': 765
                    }
                }, {
                    'repeatCell': {
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True
                                },
                                'backgroundColor': {
                                    'blue': 0.933,
                                    'green': 0.933,
                                    'red': 0.933
                                }
                            }
                        },
                        'fields': 'userEnteredFormat',
                        'range': {
                            'endRowIndex': 1,
                            'startRowIndex': 0,
                            'sheetId': 765,
                            'startColumnIndex': 0
                        }
                    }
                }, {
                    'repeatCell': {
                        'cell': {
                            'userEnteredFormat': {
                                'wrapStrategy': 'WRAP'
                            }
                        },
                        'fields': 'userEnteredFormat',
                        'range': {
                            'endColumnIndex': 3,
                            'sheetId': 765,
                            'startColumnIndex': 0,
                            'startRowIndex': 1
                        }
                    }
                }, {
                    'repeatCell': {
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'foregroundColor': {
                                        'blue': 0.6196,
                                        'green': 0.6196,
                                        'red': 0.6196
                                    }
                                },
                                'wrapStrategy': 'WRAP'
                            }
                        },
                        'fields': 'userEnteredFormat',
                        'range': {
                            'endColumnIndex': 4,
                            'sheetId': 765,
                            'startColumnIndex': 2,
                            'startRowIndex': 1
                        }
                    }
                }, {
                    'addConditionalFormatRule': {
                        'index': 0,
                        'rule': {
                            'ranges': [{
                                'endColumnIndex': 2,
                                'sheetId': 765,
                                'startColumnIndex': 1,
                                'startRowIndex': 1
                            }],
                            'booleanRule': {
                                'condition': {
                                    'type': 'BLANK'
                                },
                                'format': {
                                    'backgroundColor': {
                                        'blue': 0.964,
                                        'green': 0.905,
                                        'red': 0.929
                                    }
                                }
                            }
                        }
                    }
                }, {
                    'addProtectedRange': {
                        'protectedRange': {
                            'warningOnly': True,
                            'protectedRangeId': 1000766,
                            'range': {
                                'endColumnIndex': 1,
                                'sheetId': 765,
                                'startColumnIndex': 0,
                                'startRowIndex': 1
                            },
                            'description': 'Original strings can only be edited in the source files.'
                        }
                    }
                }, {
                    'addProtectedRange': {
                        'protectedRange': {
                            'warningOnly': True,
                            'protectedRangeId': 1000767,
                            'range': {
                                'endColumnIndex': 3,
                                'sheetId': 765,
                                'startColumnIndex': 2,
                                'startRowIndex': 1
                            },
                            'description': 'Comment strings can only be edited in the source files.'
                        }
                    }
                }, {
                    'addProtectedRange': {
                        'protectedRange': {
                            'warningOnly': True,
                            'protectedRangeId': 1000768,
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 765,
                                'startColumnIndex': 3,
                                'startRowIndex': 1
                            },
                            'description': 'Source strings can only be edited in the source files.'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 765,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '1': {
                                    'condition': {
                                        'type': 'BLANK'
                                    }
                                }
                            },
                            'filterViewId': 3300766,
                            'title': 'Untranslated Strings'
                        }
                    }
                }, {
                    'updateDimensionProperties': {
                        'fields': 'pixelSize',
                        'range': {
                            'endIndex': 3,
                            'startIndex': 0,
                            'sheetId': 765,
                            'dimension': 'COLUMNS'
                        },
                        'properties': {
                            'pixelSize': 400
                        }
                    }
                }, {
                    'updateDimensionProperties': {
                        'fields': 'pixelSize',
                        'range': {
                            'endIndex': 4,
                            'startIndex': 3,
                            'sheetId': 765,
                            'dimension': 'COLUMNS'
                        },
                        'properties': {
                            'pixelSize': 200
                        }
                    }
                }, {
                    'updateDimensionProperties': {
                        'fields': 'hiddenByUser',
                        'range': {
                            'endIndex': 3,
                            'startIndex': 2,
                            'sheetId': 765,
                            'dimension': 'COLUMNS'
                        },
                        'properties': {
                            'hiddenByUser': True
                        }
                    }
                }, {
                    'addSheet': {
                        'properties': {
                            'gridProperties': {
                                'columnCount': 4,
                                'rowCount': 2,
                                'frozenColumnCount': 1,
                                'frozenRowCount': 1
                            },
                            'sheetId': 654,
                            'title': 'de'
                        }
                    }
                }, {
                    'appendCells': {
                        'fields': 'userEnteredValue',
                        'rows': [{
                            'values': [{
                                'userEnteredValue': {
                                  'stringValue': 'en'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': 'de'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': 'Extracted comments'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': 'Reference'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'About'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'\xdcber'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/pages/about.yaml'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'About us'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'\xdcber uns'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/pages/about.yaml'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'AboutDE'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'AboutDE'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/pages/about.yaml'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Bar'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'Bar'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/pages/intro.md'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Contact'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'Ber\xfchrung'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/pages/contact.yaml'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Foo'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'Foo'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/pages/intro.md'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Goodnight Moon!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'Gute Nacht Mond!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/posts/newer.md'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'HTML Page'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'HTML-Seite'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/pages/html.html'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Hello World 2!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'Hallo Welt 2!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'Main title 2.'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/views/home.html'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Hello World!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'Hallo Welt!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/posts/oldest.md, /content/posts/older.md, /views/home.html'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Home page'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'Startseite'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/pages/home.yaml'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Introduction'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'Einbringen'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/pages/intro.md'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Newest!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'Am neuesten!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/posts/newest.md'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Tagged String'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'Stichwort String'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'Tagged String description.'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/pages/home.yaml'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Tagged String in List 1'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'Stichwort String in Liste 1'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/pages/home.yaml'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Tagged String in List 2'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'Stichwort String in Liste 2'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/pages/home.yaml'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Tagged localized body.'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'Stichwort lokalisierte K\xf6rper.'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/pages/localized.yaml'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Tagged localized title.'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'Stichwort lokalisierten Titel.'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/pages/localized.yaml, /content/pages/home.yaml'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'YAML Test'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'/content/pages/yaml_test.html'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Missing 1'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Fuzzy string'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'Fuzzy string translation'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }],
                        'sheetId': 654
                    }
                }, {
                    'repeatCell': {
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True
                                },
                                'backgroundColor': {
                                    'blue': 0.933,
                                    'green': 0.933,
                                    'red': 0.933
                                }
                            }
                        },
                        'fields': 'userEnteredFormat',
                        'range': {
                            'endRowIndex': 1,
                            'startRowIndex': 0,
                            'sheetId': 654,
                            'startColumnIndex': 0
                        }
                    }
                }, {
                    'repeatCell': {
                        'cell': {
                            'userEnteredFormat': {
                                'wrapStrategy': 'WRAP'
                            }
                        },
                        'fields': 'userEnteredFormat',
                        'range': {
                            'endColumnIndex': 3,
                            'sheetId': 654,
                            'startColumnIndex': 0,
                            'startRowIndex': 1
                        }
                    }
                }, {
                    'repeatCell': {
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'foregroundColor': {
                                        'blue': 0.6196,
                                        'green': 0.6196,
                                        'red': 0.6196
                                    }
                                },
                                'wrapStrategy': 'WRAP'
                            }
                        },
                        'fields': 'userEnteredFormat',
                        'range': {
                            'endColumnIndex': 4,
                            'sheetId': 654,
                            'startColumnIndex': 2,
                            'startRowIndex': 1
                        }
                    }
                }, {
                    'addConditionalFormatRule': {
                        'index': 0,
                        'rule': {
                            'ranges': [{
                                'endColumnIndex': 2,
                                'sheetId': 654,
                                'startColumnIndex': 1,
                                'startRowIndex': 1
                            }],
                            'booleanRule': {
                                'condition': {
                                    'type': 'BLANK'
                                },
                                'format': {
                                    'backgroundColor': {
                                        'blue': 0.964,
                                        'green': 0.905,
                                        'red': 0.929
                                    }
                                }
                            }
                        }
                    }
                }, {
                    'addProtectedRange': {
                        'protectedRange': {
                            'warningOnly': True,
                            'protectedRangeId': 1000655,
                            'range': {
                                'endColumnIndex': 1,
                                'sheetId': 654,
                                'startColumnIndex': 0,
                                'startRowIndex': 1
                            },
                            'description': 'Original strings can only be edited in the source files.'
                        }
                    }
                }, {
                    'addProtectedRange': {
                        'protectedRange': {
                            'warningOnly': True,
                            'protectedRangeId': 1000656,
                            'range': {
                                'endColumnIndex': 3,
                                'sheetId': 654,
                                'startColumnIndex': 2,
                                'startRowIndex': 1
                            },
                            'description': 'Comment strings can only be edited in the source files.'
                        }
                    }
                }, {
                    'addProtectedRange': {
                        'protectedRange': {
                            'warningOnly': True,
                            'protectedRangeId': 1000657,
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 654,
                                'startColumnIndex': 3,
                                'startRowIndex': 1
                            },
                            'description': 'Source strings can only be edited in the source files.'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 654,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '1': {
                                    'condition': {
                                        'type': 'BLANK'
                                    }
                                }
                            },
                            'filterViewId': 3300655,
                            'title': 'Untranslated Strings'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 654,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '3': {
                                    'condition': {
                                        'values': [{
                                            'userEnteredValue': u'/views/home.html'
                                        }],
                                        'type': 'TEXT_CONTAINS'
                                    }
                                }
                            },
                            'filterViewId': 63754494,
                            'title': u'/views/home.html'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 654,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '3': {
                                    'condition': {
                                        'values': [{
                                            'userEnteredValue': u'/content/posts/oldest.md'
                                        }],
                                        'type': 'TEXT_CONTAINS'
                                    }
                                }
                            },
                            'filterViewId': 7765831,
                            'title': u'/content/posts/oldest.md'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 654,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '3': {
                                    'condition': {
                                        'values': [{
                                            'userEnteredValue': u'/content/pages/html.html'
                                        }],
                                        'type': 'TEXT_CONTAINS'
                                    }
                                }
                            },
                            'filterViewId': 94981896,
                            'title': u'/content/pages/html.html'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 654,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '3': {
                                    'condition': {
                                        'values': [{
                                            'userEnteredValue': u'/content/pages/home.yaml'
                                        }],
                                        'type': 'TEXT_CONTAINS'
                                    }
                                }
                            },
                            'filterViewId': 76990244,
                            'title': u'/content/pages/home.yaml'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 654,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '3': {
                                    'condition': {
                                        'values': [{
                                            'userEnteredValue': u'/content/pages/about.yaml'
                                        }],
                                        'type': 'TEXT_CONTAINS'
                                    }
                                }
                            },
                            'filterViewId': 30141631,
                            'title': u'/content/pages/about.yaml'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 654,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '3': {
                                    'condition': {
                                        'values': [{
                                            'userEnteredValue': u'/content/pages/contact.yaml'
                                        }],
                                        'type': 'TEXT_CONTAINS'
                                    }
                                }
                            },
                            'filterViewId': 10436384,
                            'title': u'/content/pages/contact.yaml'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 654,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '3': {
                                    'condition': {
                                        'values': [{
                                            'userEnteredValue': u'/content/pages/localized.yaml'
                                        }],
                                        'type': 'TEXT_CONTAINS'
                                    }
                                }
                            },
                            'filterViewId': 73702399,
                            'title': u'/content/pages/localized.yaml'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 654,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '3': {
                                    'condition': {
                                        'values': [{
                                            'userEnteredValue': u'/content/posts/newest.md'
                                        }],
                                        'type': 'TEXT_CONTAINS'
                                    }
                                }
                            },
                            'filterViewId': 30413282,
                            'title': u'/content/posts/newest.md'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 654,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '3': {
                                    'condition': {
                                        'values': [{
                                            'userEnteredValue': u'/content/pages/intro.md'
                                        }],
                                        'type': 'TEXT_CONTAINS'
                                    }
                                }
                            },
                            'filterViewId': 28957040,
                            'title': u'/content/pages/intro.md'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 654,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '3': {
                                    'condition': {
                                        'values': [{
                                            'userEnteredValue': u'/content/pages/yaml_test.html'
                                        }],
                                        'type': 'TEXT_CONTAINS'
                                    }
                                }
                            },
                            'filterViewId': 64787988,
                            'title': u'/content/pages/yaml_test.html'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 654,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '3': {
                                    'condition': {
                                        'values': [{
                                            'userEnteredValue': u'/content/posts/newer.md'
                                        }],
                                        'type': 'TEXT_CONTAINS'
                                    }
                                }
                            },
                            'filterViewId': 45578352,
                            'title': u'/content/posts/newer.md'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 654,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '3': {
                                    'condition': {
                                        'values': [{
                                            'userEnteredValue': u'/content/posts/older.md'
                                        }],
                                        'type': 'TEXT_CONTAINS'
                                    }
                                }
                            },
                            'filterViewId': 81100327,
                            'title': u'/content/posts/older.md'
                        }
                    }
                }, {
                    'updateDimensionProperties': {
                        'fields': 'pixelSize',
                        'range': {
                            'endIndex': 3,
                            'startIndex': 0,
                            'sheetId': 654,
                            'dimension': 'COLUMNS'
                        },
                        'properties': {
                            'pixelSize': 400
                        }
                    }
                }, {
                    'updateDimensionProperties': {
                        'fields': 'pixelSize',
                        'range': {
                            'endIndex': 4,
                            'startIndex': 3,
                            'sheetId': 654,
                            'dimension': 'COLUMNS'
                        },
                        'properties': {
                            'pixelSize': 200
                        }
                    }
                }, {
                    'updateDimensionProperties': {
                        'fields': 'hiddenByUser',
                        'range': {
                            'endIndex': 3,
                            'startIndex': 2,
                            'sheetId': 654,
                            'dimension': 'COLUMNS'
                        },
                        'properties': {
                            'hiddenByUser': False
                        }
                    }
                }, {
                    'addSheet': {
                        'properties': {
                            'gridProperties': {
                                'columnCount': 4,
                                'rowCount': 2,
                                'frozenColumnCount': 1,
                                'frozenRowCount': 1
                            },
                            'sheetId': 543,
                            'title': 'en'
                        }
                    }
                }, {
                    'appendCells': {
                        'fields': 'userEnteredValue',
                        'rows': [{
                            'values': [{
                                'userEnteredValue': {
                                  'stringValue': 'en'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': 'en'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': 'Extracted comments'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': 'Reference'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'About'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'About us'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'AboutDE'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Bar'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Contact'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Foo'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Goodnight Moon!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Hello World 2!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Hello World!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Higher Priority'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Home page'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Introduction'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Lower Priority'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Newest!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }],
                        'sheetId': 543
                    }
                }, {
                    'repeatCell': {
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True
                                },
                                'backgroundColor': {
                                    'blue': 0.933,
                                    'green': 0.933,
                                    'red': 0.933
                                }
                            }
                        },
                        'fields': 'userEnteredFormat',
                        'range': {
                            'endRowIndex': 1,
                            'startRowIndex': 0,
                            'sheetId': 543,
                            'startColumnIndex': 0
                        }
                    }
                }, {
                    'repeatCell': {
                        'cell': {
                            'userEnteredFormat': {
                                'wrapStrategy': 'WRAP'
                            }
                        },
                        'fields': 'userEnteredFormat',
                        'range': {
                            'endColumnIndex': 3,
                            'sheetId': 543,
                            'startColumnIndex': 0,
                            'startRowIndex': 1
                        }
                    }
                }, {
                    'repeatCell': {
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'foregroundColor': {
                                        'blue': 0.6196,
                                        'green': 0.6196,
                                        'red': 0.6196
                                    }
                                },
                                'wrapStrategy': 'WRAP'
                            }
                        },
                        'fields': 'userEnteredFormat',
                        'range': {
                            'endColumnIndex': 4,
                            'sheetId': 543,
                            'startColumnIndex': 2,
                            'startRowIndex': 1
                        }
                    }
                }, {
                    'addConditionalFormatRule': {
                        'index': 0,
                        'rule': {
                            'ranges': [{
                                'endColumnIndex': 2,
                                'sheetId': 543,
                                'startColumnIndex': 1,
                                'startRowIndex': 1
                            }],
                            'booleanRule': {
                                'condition': {
                                    'type': 'BLANK'
                                },
                                'format': {
                                    'backgroundColor': {
                                        'blue': 0.964,
                                        'green': 0.905,
                                        'red': 0.929
                                    }
                                }
                            }
                        }
                    }
                }, {
                    'addProtectedRange': {
                        'protectedRange': {
                            'warningOnly': True,
                            'protectedRangeId': 1000544,
                            'range': {
                                'endColumnIndex': 1,
                                'sheetId': 543,
                                'startColumnIndex': 0,
                                'startRowIndex': 1
                            },
                            'description': 'Original strings can only be edited in the source files.'
                        }
                    }
                }, {
                    'addProtectedRange': {
                        'protectedRange': {
                            'warningOnly': True,
                            'protectedRangeId': 1000545,
                            'range': {
                                'endColumnIndex': 3,
                                'sheetId': 543,
                                'startColumnIndex': 2,
                                'startRowIndex': 1
                            },
                            'description': 'Comment strings can only be edited in the source files.'
                        }
                    }
                }, {
                    'addProtectedRange': {
                        'protectedRange': {
                            'warningOnly': True,
                            'protectedRangeId': 1000546,
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 543,
                                'startColumnIndex': 3,
                                'startRowIndex': 1
                            },
                            'description': 'Source strings can only be edited in the source files.'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 543,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '1': {
                                    'condition': {
                                        'type': 'BLANK'
                                    }
                                }
                            },
                            'filterViewId': 3300544,
                            'title': 'Untranslated Strings'
                        }
                    }
                }, {
                    'updateDimensionProperties': {
                        'fields': 'pixelSize',
                        'range': {
                            'endIndex': 3,
                            'startIndex': 0,
                            'sheetId': 543,
                            'dimension': 'COLUMNS'
                        },
                        'properties': {
                            'pixelSize': 400
                        }
                    }
                }, {
                    'updateDimensionProperties': {
                        'fields': 'pixelSize',
                        'range': {
                            'endIndex': 4,
                            'startIndex': 3,
                            'sheetId': 543,
                            'dimension': 'COLUMNS'
                        },
                        'properties': {
                            'pixelSize': 200
                        }
                    }
                }, {
                    'updateDimensionProperties': {
                        'fields': 'hiddenByUser',
                        'range': {
                            'endIndex': 3,
                            'startIndex': 2,
                            'sheetId': 543,
                            'dimension': 'COLUMNS'
                        },
                        'properties': {
                            'hiddenByUser': True
                        }
                    }
                }, {
                    'addSheet': {
                        'properties': {
                            'gridProperties': {
                                'columnCount': 4,
                                'rowCount': 2,
                                'frozenColumnCount': 1,
                                'frozenRowCount': 1
                            },
                            'sheetId': 432,
                            'title': 'it'
                        }
                    }
                }, {
                    'appendCells': {
                        'fields': 'userEnteredValue',
                        'rows': [{
                            'values': [{
                                'userEnteredValue': {
                                  'stringValue': 'en'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': 'it'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': 'Extracted comments'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': 'Reference'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'About'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'About us'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'AboutDE'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Bar'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Contact'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Foo'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Goodnight Moon!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Hello World 2!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Hello World!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Higher Priority'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Home page'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Introduction'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Lower Priority'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Newest!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }]
                        }],
                        'sheetId': 432
                    }
                }, {
                    'repeatCell': {
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True
                                },
                                'backgroundColor': {
                                    'blue': 0.933,
                                    'green': 0.933,
                                    'red': 0.933
                                }
                            }
                        },
                        'fields': 'userEnteredFormat',
                        'range': {
                            'endRowIndex': 1,
                            'startRowIndex': 0,
                            'sheetId': 432,
                            'startColumnIndex': 0
                        }
                    }
                }, {
                    'repeatCell': {
                        'cell': {
                            'userEnteredFormat': {
                                'wrapStrategy': 'WRAP'
                            }
                        },
                        'fields': 'userEnteredFormat',
                        'range': {
                            'endColumnIndex': 3,
                            'sheetId': 432,
                            'startColumnIndex': 0,
                            'startRowIndex': 1
                        }
                    }
                }, {
                    'repeatCell': {
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'foregroundColor': {
                                        'blue': 0.6196,
                                        'green': 0.6196,
                                        'red': 0.6196
                                    }
                                },
                                'wrapStrategy': 'WRAP'
                            }
                        },
                        'fields': 'userEnteredFormat',
                        'range': {
                            'endColumnIndex': 4,
                            'sheetId': 432,
                            'startColumnIndex': 2,
                            'startRowIndex': 1
                        }
                    }
                }, {
                    'addConditionalFormatRule': {
                        'index': 0,
                        'rule': {
                            'ranges': [{
                                'endColumnIndex': 2,
                                'sheetId': 432,
                                'startColumnIndex': 1,
                                'startRowIndex': 1
                            }],
                            'booleanRule': {
                                'condition': {
                                    'type': 'BLANK'
                                },
                                'format': {
                                    'backgroundColor': {
                                        'blue': 0.964,
                                        'green': 0.905,
                                        'red': 0.929
                                    }
                                }
                            }
                        }
                    }
                }, {
                    'addProtectedRange': {
                        'protectedRange': {
                            'warningOnly': True,
                            'protectedRangeId': 1000433,
                            'range': {
                                'endColumnIndex': 1,
                                'sheetId': 432,
                                'startColumnIndex': 0,
                                'startRowIndex': 1
                            },
                            'description': 'Original strings can only be edited in the source files.'
                        }
                    }
                }, {
                    'addProtectedRange': {
                        'protectedRange': {
                            'warningOnly': True,
                            'protectedRangeId': 1000434,
                            'range': {
                                'endColumnIndex': 3,
                                'sheetId': 432,
                                'startColumnIndex': 2,
                                'startRowIndex': 1
                            },
                            'description': 'Comment strings can only be edited in the source files.'
                        }
                    }
                }, {
                    'addProtectedRange': {
                        'protectedRange': {
                            'warningOnly': True,
                            'protectedRangeId': 1000435,
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 432,
                                'startColumnIndex': 3,
                                'startRowIndex': 1
                            },
                            'description': 'Source strings can only be edited in the source files.'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 432,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '1': {
                                    'condition': {
                                        'type': 'BLANK'
                                    }
                                }
                            },
                            'filterViewId': 3300433,
                            'title': 'Untranslated Strings'
                        }
                    }
                }, {
                    'updateDimensionProperties': {
                        'fields': 'pixelSize',
                        'range': {
                            'endIndex': 3,
                            'startIndex': 0,
                            'sheetId': 432,
                            'dimension': 'COLUMNS'
                        },
                        'properties': {
                            'pixelSize': 400
                        }
                    }
                }, {
                    'updateDimensionProperties': {
                        'fields': 'pixelSize',
                        'range': {
                            'endIndex': 4,
                            'startIndex': 3,
                            'sheetId': 432,
                            'dimension': 'COLUMNS'
                        },
                        'properties': {
                            'pixelSize': 200
                        }
                    }
                }, {
                    'updateDimensionProperties': {
                        'fields': 'hiddenByUser',
                        'range': {
                            'endIndex': 3,
                            'startIndex': 2,
                            'sheetId': 432,
                            'dimension': 'COLUMNS'
                        },
                        'properties': {
                            'hiddenByUser': True
                        }
                    }
                }, {
                    'addSheet': {
                        'properties': {
                            'gridProperties': {
                                'columnCount': 4,
                                'rowCount': 2,
                                'frozenColumnCount': 1,
                                'frozenRowCount': 1
                            },
                            'sheetId': 321,
                            'title': 'ja'
                        }
                    }
                }, {
                    'appendCells': {
                        'fields': 'userEnteredValue',
                        'rows': [{
                            'values': [{
                                'userEnteredValue': {
                                  'stringValue': 'en'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': 'ja'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': 'Extracted comments'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': 'Reference'
                                }
                            }]
                        }, {
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': u'Hello World!'
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': ''
                                }
                            }, {
                                'userEnteredValue': {
                                    'stringValue': u'source/templates/home.html'
                                }
                            }]
                        }],
                        'sheetId': 321
                    }
                }, {
                    'repeatCell': {
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True
                                },
                                'backgroundColor': {
                                    'blue': 0.933,
                                    'green': 0.933,
                                    'red': 0.933
                                }
                            }
                        },
                        'fields': 'userEnteredFormat',
                        'range': {
                            'endRowIndex': 1,
                            'startRowIndex': 0,
                            'sheetId': 321,
                            'startColumnIndex': 0
                        }
                    }
                }, {
                    'repeatCell': {
                        'cell': {
                            'userEnteredFormat': {
                                'wrapStrategy': 'WRAP'
                            }
                        },
                        'fields': 'userEnteredFormat',
                        'range': {
                            'endColumnIndex': 3,
                            'sheetId': 321,
                            'startColumnIndex': 0,
                            'startRowIndex': 1
                        }
                    }
                }, {
                    'repeatCell': {
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'foregroundColor': {
                                        'blue': 0.6196,
                                        'green': 0.6196,
                                        'red': 0.6196
                                    }
                                },
                                'wrapStrategy': 'WRAP'
                            }
                        },
                        'fields': 'userEnteredFormat',
                        'range': {
                            'endColumnIndex': 4,
                            'sheetId': 321,
                            'startColumnIndex': 2,
                            'startRowIndex': 1
                        }
                    }
                }, {
                    'addConditionalFormatRule': {
                        'index': 0,
                        'rule': {
                            'ranges': [{
                                'endColumnIndex': 2,
                                'sheetId': 321,
                                'startColumnIndex': 1,
                                'startRowIndex': 1
                            }],
                            'booleanRule': {
                                'condition': {
                                    'type': 'BLANK'
                                },
                                'format': {
                                    'backgroundColor': {
                                        'blue': 0.964,
                                        'green': 0.905,
                                        'red': 0.929
                                    }
                                }
                            }
                        }
                    }
                }, {
                    'addProtectedRange': {
                        'protectedRange': {
                            'warningOnly': True,
                            'protectedRangeId': 1000322,
                            'range': {
                                'endColumnIndex': 1,
                                'sheetId': 321,
                                'startColumnIndex': 0,
                                'startRowIndex': 1
                            },
                            'description': 'Original strings can only be edited in the source files.'
                        }
                    }
                }, {
                    'addProtectedRange': {
                        'protectedRange': {
                            'warningOnly': True,
                            'protectedRangeId': 1000323,
                            'range': {
                                'endColumnIndex': 3,
                                'sheetId': 321,
                                'startColumnIndex': 2,
                                'startRowIndex': 1
                            },
                            'description': 'Comment strings can only be edited in the source files.'
                        }
                    }
                }, {
                    'addProtectedRange': {
                        'protectedRange': {
                            'warningOnly': True,
                            'protectedRangeId': 1000324,
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 321,
                                'startColumnIndex': 3,
                                'startRowIndex': 1
                            },
                            'description': 'Source strings can only be edited in the source files.'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 321,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '1': {
                                    'condition': {
                                        'type': 'BLANK'
                                    }
                                }
                            },
                            'filterViewId': 3300322,
                            'title': 'Untranslated Strings'
                        }
                    }
                }, {
                    'addFilterView': {
                        'filter': {
                            'range': {
                                'endColumnIndex': 4,
                                'sheetId': 321,
                                'startColumnIndex': 0,
                                'startRowIndex': 0
                            },
                            'criteria': {
                                '3': {
                                    'condition': {
                                        'values': [{
                                            'userEnteredValue': u'source/templates/home.html'
                                        }],
                                        'type': 'TEXT_CONTAINS'
                                    }
                                }
                            },
                            'filterViewId': 39896814,
                            'title': u'source/templates/home.html'
                        }
                    }
                }, {
                    'updateDimensionProperties': {
                        'fields': 'pixelSize',
                        'range': {
                            'endIndex': 3,
                            'startIndex': 0,
                            'sheetId': 321,
                            'dimension': 'COLUMNS'
                        },
                        'properties': {
                            'pixelSize': 400
                        }
                    }
                }, {
                    'updateDimensionProperties': {
                        'fields': 'pixelSize',
                        'range': {
                            'endIndex': 4,
                            'startIndex': 3,
                            'sheetId': 321,
                            'dimension': 'COLUMNS'
                        },
                        'properties': {
                            'pixelSize': 200
                        }
                    }
                }, {
                    'updateDimensionProperties': {
                        'fields': 'hiddenByUser',
                        'range': {
                            'endIndex': 3,
                            'startIndex': 2,
                            'sheetId': 321,
                            'dimension': 'COLUMNS'
                        },
                        'properties': {
                            'hiddenByUser': True
                        }
                    }
                }]
            }
        )


if __name__ == '__main__':
    unittest.main()
