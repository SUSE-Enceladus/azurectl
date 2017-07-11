from .test_helper import argv_kiwi_tests

import datetime
import sys
import mock
from mock import patch
from urllib.parse import urlparse
from pytest import raises
from azurectl.storage.container import Container
import azurectl
from collections import namedtuple

from azurectl.azurectl_exceptions import (
    AzureCannotInit,
    AzureContainerCreateError,
    AzureContainerDeleteError,
    AzureContainerListContentError,
    AzureContainerListError
)

MOCK_STORAGE_NAME = 'mock-storage'


class TestContainer:
    def setup(self):
        name = namedtuple("name", "name")
        self.name_list = [name(name="a"), name(name="b")]
        account = mock.Mock()
        credentials = namedtuple(
            'credentials',
            ['private_key', 'certificate', 'subscription_id']
        )
        account.storage_name = mock.Mock(return_value=MOCK_STORAGE_NAME)
        account.storage_key = mock.Mock(
            return_value='fI8bhf6QAvgwCgR9qJyoNLHQ9F73fQ97e3/e8jMCFSiFioaB' +
            'iAU0oSGcFACtniSY6pS3L5GKNzPCK0FF6M+O4A=='
        )
        account.publishsettings = mock.Mock(
            return_value=credentials(
                private_key='abc',
                certificate='abc',
                subscription_id='4711'
            )
        )
        self.container = Container(account)

    def test_container_alternate_init(self):
        container = Container(
            account_name=self.container.account_name,
            key=self.container.account_key,
            blob_service_host_base=self.container.blob_service_host_base
        )
        assert container.account_name == self.container.account_name
        assert container.account_key == self.container.account_key
        assert container.blob_service_host_base == \
            self.container.blob_service_host_base

    def test_container_failed_init(self):
        with raises(AzureCannotInit):
            Container()

    @patch('azurectl.storage.container.BaseBlobService.list_containers')
    def test_list(self, mock_list_containers):
        mock_list_containers.return_value = self.name_list
        assert self.container.list() == ['a', 'b']

    @patch('azurectl.storage.container.BaseBlobService.delete_container')
    def test_delete(self, mock_delete):
        assert self.container.delete('container_name') is True
        mock_delete.assert_called_once_with(
            container_name='container_name', fail_not_exist=True
        )

    @patch('azurectl.storage.container.BaseBlobService.create_container')
    def test_create(self, mock_create):
        assert self.container.create('container_name') is True
        mock_create.assert_called_once_with(
            container_name='container_name', fail_on_exist=True
        )

    @patch('azurectl.storage.container.BaseBlobService.delete_container')
    def test_delete_raises(self, mock_delete):
        mock_delete.side_effect = Exception
        with raises(AzureContainerDeleteError):
            self.container.delete('container_name')

    @patch('azurectl.storage.container.BaseBlobService.create_container')
    def test_create_raises(self, mock_create):
        mock_create.side_effect = Exception
        with raises(AzureContainerCreateError):
            self.container.create('container_name')

    @patch('azurectl.storage.container.BaseBlobService.list_containers')
    def test_list_raises(self, mock_list_containers):
        mock_list_containers.side_effect = AzureContainerListError
        with raises(AzureContainerListError):
            self.container.list()

    @patch('azurectl.storage.container.BaseBlobService.list_blobs')
    def test_content(self, mock_list_blobs):
        mock_list_blobs.return_value = self.name_list
        assert self.container.content('some-container') == \
            {'some-container': ['a', 'b']}

    @patch('azurectl.storage.container.BaseBlobService.list_blobs')
    def test_content_raises(self, mock_list_blobs):
        mock_list_blobs.side_effect = AzureContainerListContentError
        with raises(AzureContainerListContentError):
            self.container.content('some-container')

    def test_sas(self):
        container = 'mock-container'
        start = datetime.datetime(2015, 1, 1)
        expiry = datetime.datetime(2015, 12, 31)
        permissions = 'rl'
        parsed = urlparse(
            self.container.sas(container, start, expiry, permissions)
        )
        assert parsed.scheme == 'https'
        assert parsed.netloc == MOCK_STORAGE_NAME + \
            '.blob.core.windows.net'
        assert parsed.path == '/' + container
        assert 'st=2015-01-01T00%3A00%3A00Z' in parsed.query
        assert 'se=2015-12-31T00%3A00%3A00Z' in parsed.query
        assert 'sp=rl' in parsed.query
        assert 'sr=c' in parsed.query
        assert 'sig=' in parsed.query  # can't actively validate the signature

    @patch('azurectl.storage.container.BaseBlobService.get_container_properties')
    def test_exists_false(self, mock_properties):
        mock_properties.side_effect = Exception
        assert self.container.exists('container_name') is False

    @patch('azurectl.storage.container.BaseBlobService.get_container_properties')
    def test_exists_true(self, mock_properties):
        assert self.container.exists('container_name') is True
