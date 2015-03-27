import sys
import mock
from mock import patch
from nose.tools import *
from azure_cli.azurectl_exceptions import *
from azure_cli.storage import Storage

import azure_cli

from collections import namedtuple


class TestStorage:
    def setup(self):
        account = mock.Mock()
        credentials = namedtuple(
            'credentials',
            ['private_key', 'certificate', 'subscription_id']
        )
        account.publishsettings = mock.Mock(
            return_value=credentials(
                private_key='abc',
                certificate='abc',
                subscription_id='4711'
            )
        )
        self.storage = Storage(account, 'some-container')

    @raises(AzureStorageFileNotFound)
    def test_upload_storage_file_not_found(self):
        self.storage.upload('some-blob', None)

    @raises(AzureStorageUploadError)
    @patch('azure_cli.storage.XZ.uncompressed_size')
    def test_upload(self, mock_uncompressed_size):
        mock_uncompressed_size.return_value = 1024
        self.storage.upload('../data/config', None, 1024)

    @raises(AzureStorageDeleteError)
    def test_delete(self):
        self.storage.delete('some-blob')

    def test_print_upload_status(self):
        self.storage.print_upload_status()
        assert self.storage.upload_status == \
            {'current_bytes': 0, 'total_bytes': 0}
