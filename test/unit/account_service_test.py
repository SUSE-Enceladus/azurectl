from .test_helper import argv_kiwi_tests

import mock
from mock import patch
from azurectl.account.service import AzureAccount
from azurectl.config.parser import Config
from collections import namedtuple
import azurectl
from pytest import raises

from azurectl.azurectl_exceptions import (
    AzureConfigVariableNotFound,
    AzureConfigVariableNotFound,
    AzureManagementCertificateNotFound,
    AzureServiceManagementError,
    AzureServiceManagementError,
    AzureServiceManagementUrlNotFound,
    AzureSubscriptionCertificateDecodeError,
    AzureSubscriptionIdNotFound,
    AzureSubscriptionIdNotFound,
    AzureSubscriptionIdNotFound,
    AzureSubscriptionParseError,
    AzureSubscriptionParseError,
    AzureSubscriptionPKCS12DecodeError,
    AzureSubscriptionPrivateKeyDecodeError,
    AzureUnrecognizedManagementUrl
)


class TestAzureAccount:
    @patch('azurectl.account.service.NamedTemporaryFile')
    def setup(self, mock_temp):
        tempfile = mock.Mock()
        tempfile.name = 'tempfile'
        mock_temp.return_value = tempfile
        self.account = AzureAccount(
            Config(
                region_name='East US 2', filename='../data/config'
            )
        )
        azurectl.account.service.load_pkcs12 = mock.Mock()

    def __mock_management_service(
        self, endpoint, service_response=None, side_effect=None
    ):
        mock_service_function = mock.Mock()
        if side_effect:
            mock_service_function.side_effect = side_effect
        else:
            mock_service_function.return_value = service_response
        mock_service = mock.Mock(**{endpoint: mock_service_function})
        self.account.get_management_service = mock.Mock(
            return_value=mock_service
        )

    @patch('azurectl.account.service.ServiceManagementService')
    @patch('azurectl.account.service.dump_privatekey')
    @patch('azurectl.account.service.dump_certificate')
    @patch('azurectl.account.service.AzureAccount.get_management_url')
    @patch('azurectl.account.service.AzureAccount.certificate_filename')
    def test_service_error(
        self, mock_mgmt_cert, mock_mgmt_url, mock_dump_certificate,
        mock_dump_pkey, mock_service
    ):
        mock_mgmt_cert.return_value = 'certfile'
        mock_mgmt_url.return_value = 'test.url'
        mock_dump_certificate.return_value = 'abc'
        mock_dump_pkey.return_value = 'abc'
        mock_service.side_effect = AzureServiceManagementError
        with raises(AzureServiceManagementError):
            self.account.storage_names()

    def test_storage_name(self):
        assert self.account.storage_name() == 'bob'

    def test_storage_container(self):
        assert self.account.storage_container() == 'foo'

    @patch('azurectl.account.service.dump_privatekey')
    @patch('azurectl.account.service.dump_certificate')
    def test_subscription_cert_decode_error(
        self, mock_dump_certificate, mock_dump_pkey
    ):
        mock_dump_pkey.return_value = b'abc'
        mock_dump_certificate.side_effect = \
            AzureSubscriptionCertificateDecodeError
        with raises(AzureSubscriptionCertificateDecodeError):
            self.account.get_management_service()

    def test_subscription_management_cert_not_found(self):
        account_invalid = AzureAccount(
            Config(
                region_name='East US 2',
                filename='../data/config.missing_publishsettings_cert'
            )
        )
        with raises(AzureManagementCertificateNotFound):
            account_invalid.get_management_service()

    @patch('azurectl.account.service.load_pkcs12')
    @patch('azurectl.account.service.dump_privatekey')
    @patch('azurectl.account.service.dump_certificate')
    @patch('base64.b64decode')
    def test_subscription_id_missing(
        self, base64_decode, mock_dump_certificate,
        mock_dump_pkey, mock_pkcs12
    ):
        account_invalid = AzureAccount(
            Config(
                region_name='East US 2',
                filename='../data/config.missing_publishsettings_id'
            )
        )
        with raises(AzureSubscriptionIdNotFound):
            account_invalid.get_management_service()

    def test_get_management_url(self):
        mgmt_url = self.account.get_management_url()
        assert mgmt_url == 'test.url'

    def test_get_management_url_missing(self):
        account_invalid = AzureAccount(
            Config(
                region_name='East US 2',
                filename='../data/config.missing_mgmt_url'
            )
        )
        with raises(AzureServiceManagementUrlNotFound):
            account_invalid.get_management_url()

    @patch('azurectl.account.service.AzureAccount.get_management_url')
    def test_get_blob_service_host_base(self, mock_mgmt_url):
        mock_mgmt_url.return_value = 'management.test.url'
        host_base = self.account.get_blob_service_host_base()
        assert host_base == 'test.url'

    @patch('azurectl.account.service.AzureAccount.get_management_url')
    def test_get_blob_service_host_base_with_bad_url(self, mock_mgmt_url):
        mock_mgmt_url.return_value = 'invalid.test.url'
        with raises(AzureUnrecognizedManagementUrl):
            self.account.get_blob_service_host_base()

    def test_subscription_pkcs12_error(self):
        account_invalid = AzureAccount(
            Config(
                region_name='East US 2',
                filename='../data/config.corrupted_p12_cert'
            )
        )
        with raises(AzureSubscriptionPKCS12DecodeError):
            account_invalid.get_management_service()

    def test_empty_publishsettings(self):
        account_invalid = AzureAccount(
            Config(
                region_name='East US 2',
                filename='../data/config.empty_publishsettings'
            )
        )
        with raises(AzureSubscriptionParseError):
            account_invalid.get_management_url()

    def test_missing_publishsettings(self):
        account_invalid = AzureAccount(
            Config(
                region_name='East US 2',
                filename='../data/config.missing_publishsettings'
            )
        )
        with raises(AzureSubscriptionParseError):
            account_invalid.get_management_url()

    @patch('azurectl.account.service.dump_privatekey')
    @patch('azurectl.account.service.dump_certificate')
    @patch('azurectl.account.service.AzureAccount.get_management_url')
    def test_publishsettings_with_multiple_subscriptions_defaults_to_first(
        self,
        mock_mgmt_url,
        mock_dump_certificate,
        mock_dump_pkey
    ):
        account = AzureAccount(
            Config(
                region_name='East US 2',
                filename='../data/config.multiple_subscriptions_no_id'
            )
        )
        assert account.subscription_id() == 'first'

    @patch('azurectl.account.service.dump_privatekey')
    @patch('azurectl.account.service.dump_certificate')
    @patch('azurectl.account.service.AzureAccount.get_management_url')
    def test_config_specifies_subscription_in_publishsettings(
        self,
        mock_mgmt_url,
        mock_dump_certificate,
        mock_dump_pkey
    ):
        account = AzureAccount(
            Config(
                region_name='East US 2',
                filename='../data/config.multiple_subscriptions_set_id'
            )
        )
        assert account.subscription_id() == 'second'

    def test_publishsettings_invalid_cert(self):
        account_invalid = AzureAccount(
            Config(
                region_name='East US 2',
                filename='../data/config.invalid_publishsettings_cert'
            )
        )
        with raises(AzureSubscriptionPrivateKeyDecodeError):
            account_invalid.certificate_filename()

    def test_config_subscription_id_not_found_in_publishsettings(self):
        account_invalid = AzureAccount(
            Config(
                region_name='East US 2',
                filename='../data/config.missing_set_subscription_id'
            )
        )
        with raises(AzureSubscriptionIdNotFound):
            account_invalid.get_management_url()

    def test_config_subscription_id_missing(self):
        account_invalid = AzureAccount(
            Config(
                region_name='East US 2',
                filename='../data/config.set_subscription_id_missing_id'
            )
        )
        with raises(AzureSubscriptionIdNotFound):
            account_invalid.get_management_url()

    def test_config_without_publishsettings(self):
        account = AzureAccount(
            Config(
                region_name='East US 2',
                filename='../data/config.no_publishsettings'
            )
        )
        assert account.get_management_url() == 'test.url'
        assert account.certificate_filename() == '../data/pemfile'
        assert account.subscription_id() == 'id1234'

    @patch('azurectl.account.service.dump_privatekey')
    @patch('azurectl.account.service.dump_certificate')
    def test_config_create_cert_from_publishsettings(
        self, mock_dump_certificate, mock_dump_pkey
    ):
        mock_dump_pkey.return_value = b'abc'
        mock_dump_certificate.return_value = b'cert'
        assert self.account.certificate_filename() == 'tempfile'

    def test_config_must_have_management_url_or_publishsettings(self):
        account = AzureAccount(
            Config(
                filename='../data/config.publishsettings_undefined'
            )
        )
        with raises(AzureConfigVariableNotFound):
            account.get_management_url()

    def test_config_must_have_management_pem_file_or_publishsettings(self):
        account = AzureAccount(
            Config(
                filename='../data/config.publishsettings_undefined'
            )
        )
        with raises(AzureConfigVariableNotFound):
            account.certificate_filename()

    def test_storage_key(self):
        primary = namedtuple(
            'primary', 'primary'
        )
        keys = namedtuple(
            'storage_service_keys', 'storage_service_keys'
        )
        self.__mock_management_service(
            'get_storage_account_keys',
            keys(storage_service_keys=primary(primary='foo'))
        )
        assert self.account.storage_key() == 'foo'

    def test_storage_key_error(self):
        self.__mock_management_service(
            'get_storage_account_keys', None, side_effect=Exception
        )
        with raises(AzureServiceManagementError):
            self.account.storage_key()

    @patch('azurectl.account.service.ServiceManagementService')
    def test_get_management_service(self, mock_service):
        self.account.subscription_id = mock.Mock()
        self.account.certificate_filename = mock.Mock()
        self.account.get_management_url = mock.Mock()
        service = self.account.get_management_service()
        assert self.account._AzureAccount__service == service
        assert self.account.subscription_id.called
        assert self.account.certificate_filename.called
        assert self.account.get_management_url.called

    @patch('azurectl.account.service.ServiceManagementService.list_storage_accounts')
    def test_storage_names(self, mock_service):
        names = namedtuple(
            'service_name', 'service_name'
        )
        service_result = [names(service_name='foo')]
        self.__mock_management_service('list_storage_accounts', service_result)
        assert self.account.storage_names() == ['foo']

    def test_instance_types(self):
        # given
        names = namedtuple(
            'names',
            'name memory_in_mb cores max_data_disk_count \
             virtual_machine_resource_disk_size_in_mb'
        )
        service_result = [names(
            name='foo',
            memory_in_mb=1,
            cores=2,
            max_data_disk_count=3,
            virtual_machine_resource_disk_size_in_mb=4
        )]
        self.__mock_management_service('list_role_sizes', service_result)
        # when
        x = self.account.instance_types()
        # then
        assert self.account.instance_types() == [
            {'foo': {
                'cores': 2,
                'max_disk_count': 3,
                'disk_size': '4MB',
                'memory': '1MB'
            }}
        ]

    def test_locations(self):
        # given
        mock_location = mock.Mock(
            compute_capabilities={
                'virtual_machines_role_sizes': [],
                'web_worker_role_sizes': []
            },
            display_name='Mock Region',
            available_services=['Compute',
                    'Storage',
                    'PersistentVMRole',
                    'HighMemory']
        )
        mock_location.configure_mock(name='Mock Region')
        self.__mock_management_service('list_locations', [mock_location])
        # when
        result = self.account.locations()
        # then
        assert result == ['Mock Region']

    def test_filtered_locations(self):
        # given
        mock_location = mock.Mock(
            compute_capabilities={
                'virtual_machines_role_sizes': [],
                'web_worker_role_sizes': []
            },
            display_name='Mock Region',
            available_services=['Compute',
                    'Storage',
                    'PersistentVMRole',
                    'HighMemory']
        )
        mock_location.configure_mock(name='Mock Region')
        self.__mock_management_service('list_locations', [mock_location])
        self.account.certificate_filename = mock.Mock()
        # when
        result = self.account.locations('Compute')
        # then
        assert result == ['Mock Region']
        # when
        result = self.account.locations('foo')
        # then
        assert result == []

