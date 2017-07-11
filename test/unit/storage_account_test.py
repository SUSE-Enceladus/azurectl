from .test_helper import argv_kiwi_tests

import sys
import mock
from collections import namedtuple
from mock import patch
from mock import call
from pytest import raises
from azurectl.account.service import AzureAccount
from azurectl.config.parser import Config
from azurectl.storage.account import StorageAccount
import azurectl

from azurectl.azurectl_exceptions import (
    AzureStorageAccountCreateError,
    AzureStorageAccountDeleteError,
    AzureStorageAccountListError,
    AzureStorageAccountShowError,
    AzureStorageAccountUpdateError
)


class TestStorageAccount:
    def setup(self):
        account = AzureAccount(
            Config(
                region_name='East US 2', filename='../data/config'
            )
        )
        self.service = mock.Mock()
        account.get_management_service = mock.Mock(return_value=self.service)
        account.get_blob_service_host_base = mock.Mock(
            return_value='.blob.test.url'
        )
        account.storage_key = mock.Mock()

        self.containers_list = ['container_a', 'container_b']
        self.mock_storage_service = mock.Mock(
            storage_service_keys=None,
            storage_service_properties=mock.Mock(
                status='Created',
                account_type='Standard_GRS',
                description='mock storage service',
                geo_secondary_region='West US',
                creation_time='2015-12-09T07:53:54Z',
                geo_primary_region='East US 2',
                label='mockstorageservice',
                status_of_primary='Available',
                location='East US 2',
                affinity_group='',
                last_geo_failover_time='',
                status_of_secondary='Available',
                endpoints=[
                    'https://mockstorageservice.blob.core.windows.net/',
                    'https://mockstorageservice.queue.core.windows.net/',
                    'https://mockstorageservice.table.core.windows.net/',
                    'https://mockstorageservice.file.core.windows.net/'
                ],
                geo_replication_enabled='True'
            ),
            url=(
                'https://management.core.windows.net/' +
                '00000000-0000-0000-0000-000000000000/services/' +
                'storageservices/mockstorageservice'
            ),
            service_name='mockstorageservice',
            capabilities='None',
            extended_properties={
                'ResourceGroup': 'Default-Storage-EastUS2',
                'ResourceLocation': 'East US 2'
            },
            containers=None
        )
        self.keyed_service = mock.Mock(
            storage_service_keys=mock.Mock(
                primary='1234567890abcdef==',
                secondary='fedcba0987654321=='
            )
        )
        self.expected_list_result = [{
            "backup": {
                "backup-region": "West US",
                "backup-region-status": "Available",
                "last-failover": "",
                "status": "Available"
            },
            "backup-strategy": "--geo-redundant",
            "description": "mock storage service",
            "endpoints": [
                "https://mockstorageservice.blob.core.windows.net/",
                "https://mockstorageservice.queue.core.windows.net/",
                "https://mockstorageservice.table.core.windows.net/",
                "https://mockstorageservice.file.core.windows.net/"
            ],
            "label": "mockstorageservice",
            "name": "mockstorageservice",
            "region": "East US 2",
            "status": "Created"
        }]
        self.expected_show_result = {
            "backup": {
                "backup-region": "West US",
                "backup-region-status": "Available",
                "last-failover": "",
                "status": "Available"
            },
            "backup-strategy": "--geo-redundant",
            "containers": self.containers_list,
            "description": "mock storage service",
            "endpoints": [
                "https://mockstorageservice.blob.core.windows.net/",
                "https://mockstorageservice.queue.core.windows.net/",
                "https://mockstorageservice.table.core.windows.net/",
                "https://mockstorageservice.file.core.windows.net/"
            ],
            "keys": {
                "primary": self.keyed_service.storage_service_keys.primary,
                "secondary": self.keyed_service.storage_service_keys.secondary
            },
            "label": "mockstorageservice",
            "name": "mockstorageservice",
            "region": "East US 2",
            "status": "Created"
        }

        self.my_request = mock.Mock(request_id=42)

        self.storage_account = StorageAccount(account)

    def test_list(self):
        self.service.list_storage_accounts.return_value = [
            self.mock_storage_service
        ]
        result = self.storage_account.list()
        assert result == self.expected_list_result

    def test_exists_false(self):
        self.service.get_storage_account_properties.side_effect = Exception
        assert self.storage_account.exists('some-name') is False

    def test_exists_true(self):
        assert self.storage_account.exists('some-name') is True

    def test_list_error(self):
        self.service.list_storage_accounts.side_effect = Exception
        with raises(AzureStorageAccountListError):
            self.storage_account.list()

    @patch('azurectl.storage.account.Container.list')
    def test_show(self, mock_container_list):
        self.service.get_storage_account_keys.return_value = \
            self.keyed_service
        self.service.get_storage_account_properties.return_value = \
            self.mock_storage_service
        mock_container_list.return_value = self.containers_list
        result = self.storage_account.show(
            self.mock_storage_service.service_name
        )
        assert result == self.expected_show_result

    def test_show_error(self):
        self.service.get_storage_account_properties.side_effect = Exception
        with raises(AzureStorageAccountShowError):
            self.storage_account.show('mockstorageservice')

    def test_show_add_keys_error(self):
        self.service.get_storage_account_keys.side_effect = Exception
        self.service.get_storage_account_properties.return_value = \
            self.mock_storage_service
        with raises(AzureStorageAccountShowError):
            self.storage_account.show('mockstorageservice')

    def test_create(self):
        self.service.create_storage_account.return_value = self.my_request
        result = self.storage_account.create(
            'mockstorageservice',
            None,
            None,
            '--locally-redundant'
        )
        assert result == self.my_request.request_id

    def test_create_error(self):
        self.service.create_storage_account.side_effect = Exception
        with raises(AzureStorageAccountCreateError):
            result = self.storage_account.create(
                'mockstorageservice',
                None,
                None,
                '--locally-redundant'
            )

    @patch('azurectl.storage.account.Container.list')
    def test_basic_update(self, mock_container_list):
        self.service.update_storage_account.return_value = \
            self.my_request
        self.service.get_storage_account_keys.return_value = \
            self.keyed_service
        self.service.get_storage_account_properties.return_value = \
            self.mock_storage_service
        mock_container_list.return_value = self.containers_list
        result = self.storage_account.update(
            'mockstorageservice',
            None,
            None,
            '--locally-redundant'
        )
        assert result == 42

    def test_update_error(self):
        self.service.update_storage_account.side_effect = Exception
        with raises(AzureStorageAccountUpdateError):
            result = self.storage_account.update(
                'mockstorageservice',
                None,
                None,
                '--locally-redundant'
            )

    @patch('azurectl.storage.account.Container.list')
    def test_update_keys(self, mock_container_list):
        self.service.regenerate_storage_account_keys.return_value = \
            self.my_request
        self.service.update_storage_account.return_value = \
            self.my_request
        self.service.get_storage_account_keys.return_value = \
            self.keyed_service
        self.service.get_storage_account_properties.return_value = \
            self.mock_storage_service
        mock_container_list.return_value = self.containers_list

        # primary key
        result = self.storage_account.update(
            'mockstorageservice',
            None,
            None,
            '--locally-redundant',
            regenerate_primary_key=True
        )
        self.service.regenerate_storage_account_keys.assert_called_with(
            'mockstorageservice',
            'Primary'
        )

        # secondary key
        result = self.storage_account.update(
            'mockstorageservice',
            None,
            None,
            '--locally-redundant',
            regenerate_secondary_key=True
        )
        self.service.regenerate_storage_account_keys.assert_called_with(
            'mockstorageservice',
            'Secondary'
        )

    def test_delete(self):
        self.service.delete_storage_account.return_value = self.my_request
        result = self.storage_account.delete('mockstorageservice')
        assert result == self.my_request.request_id

    def test_delete_error(self):
        self.service.delete_storage_account.side_effect = Exception
        with raises(AzureStorageAccountDeleteError):
            self.storage_account.delete('mockstorageservice')
