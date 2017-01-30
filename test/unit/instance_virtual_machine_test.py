import sys
import mock
from mock import patch


from test_helper import *

from azurectl.account.service import AzureAccount
from azurectl.config.parser import Config
from azurectl.azurectl_exceptions import *
from azurectl.instance.virtual_machine import VirtualMachine

from azure.servicemanagement import OSVirtualHardDisk

import azurectl

from collections import namedtuple


class TestVirtualMachine:
    def setup(self):
        MyStruct = namedtuple(
            'MyStruct',
            'name label os category description location \
             affinity_group media_link'
        )
        self.list_os_images = [MyStruct(
            name='some-name',
            label='bob',
            os='linux',
            category='cloud',
            description='nice',
            location='here',
            affinity_group='ok',
            media_link='url'
        )]
        account = AzureAccount(
            Config(
                region_name='East US 2', filename='../data/config'
            )
        )
        self.service = mock.Mock()
        account.get_management_service = mock.Mock(return_value=self.service)
        account.get_blob_service_host_base = mock.Mock(
            return_value='test.url'
        )
        account.storage_key = mock.Mock()
        self.account = account
        self.vm = VirtualMachine(account)
        self.system_config = self.vm.create_linux_configuration(
            'some-user', 'some-host'
        )

    def test_create_network_configuration(self):
        endpoint = self.vm.create_network_endpoint('SSH', 22, 22, 'TCP')
        config = self.vm.create_network_configuration([endpoint])
        assert config.input_endpoints[0].name == 'SSH'

    def test_create_network_endpoint(self):
        endpoint = self.vm.create_network_endpoint('SSH', 22, 22, 'TCP')
        assert endpoint.name == 'SSH'

    def test_create_linux_configuration(self):
        config = self.vm.create_linux_configuration(
            'user', 'instance-name', True, 'password',
            'custom-data', 'fingerprint'
        )
        assert config.user_name == 'user'

    @patch('azurectl.instance.virtual_machine.OSVirtualHardDisk')
    def test_create_instance_initial_deployment(self, mock_os_disk):
        self.service.get_deployment_by_name.side_effect = Exception(
            '<Code>ResourceNotFound</Code><Message>No deployments were found'
        )
        request_result = mock.Mock()
        storage_properties = mock.MagicMock()
        storage_properties.storage_service_properties.location = 'region'
        self.service.get_storage_account_properties.return_value = \
            storage_properties

        service_properties = mock.MagicMock()
        service_properties.hosted_service_properties.location = 'region'
        self.service.get_hosted_service_properties.return_value = \
            service_properties

        image_locations = mock.MagicMock()
        image_locations.location = 'region'
        self.service.get_os_image.return_value = image_locations

        os_disk = OSVirtualHardDisk('foo', 'foo')
        mock_os_disk.return_value = os_disk
        endpoint = self.vm.create_network_endpoint('SSH', 22, 22, 'TCP')
        network_config = self.vm.create_network_configuration([endpoint])
        result = self.vm.create_instance(
            cloud_service_name='cloud-service',
            disk_name='foo.vhd',
            system_config=self.system_config,
            network_config=network_config,
            label='some-label',
            reserved_ip_name='test_reserved_ip_name'
        )
        mock_os_disk.assert_called_once_with(
            'foo.vhd',
            'https://bob.blob.test.url/foo/cloud-service_instance_some-host_image_foo.vhd'
        )
        self.service.create_virtual_machine_deployment.assert_called_once_with(
            deployment_slot='production',
            role_size='Small',
            deployment_name='cloud-service',
            service_name='cloud-service',
            os_virtual_hard_disk=os_disk,
            label='some-label',
            system_config=self.system_config,
            reserved_ip_name='test_reserved_ip_name',
            role_name=self.system_config.host_name,
            network_config=network_config,
            provision_guest_agent=True
        )
        assert result['instance_name'] == 'some-host'

    @patch('azurectl.instance.virtual_machine.OSVirtualHardDisk')
    def test_create_instance_add_role(self, mock_os_disk):
        storage_properties = mock.MagicMock()
        storage_properties.storage_service_properties.location = 'region'
        self.service.get_storage_account_properties.return_value = \
            storage_properties

        service_properties = mock.MagicMock()
        service_properties.hosted_service_properties.location = 'region'
        self.service.get_hosted_service_properties.return_value = \
            service_properties

        image_locations = mock.MagicMock()
        image_locations.location = 'region'
        self.service.get_os_image.return_value = image_locations

        os_disk = OSVirtualHardDisk('foo', 'foo')
        mock_os_disk.return_value = os_disk
        endpoint = self.vm.create_network_endpoint('SSH', 22, 22, 'TCP')
        network_config = self.vm.create_network_configuration([endpoint])
        result = self.vm.create_instance(
            cloud_service_name='cloud-service',
            disk_name='foo.vhd',
            system_config=self.system_config,
            network_config=network_config
        )
        mock_os_disk.assert_called_once_with(
            'foo.vhd',
            'https://bob.blob.test.url/foo/cloud-service_instance_some-host_image_foo.vhd'
        )
        self.service.add_role.assert_called_once_with(
            role_size='Small',
            deployment_name='cloud-service',
            service_name='cloud-service',
            os_virtual_hard_disk=os_disk,
            system_config=self.system_config,
            role_name=self.system_config.host_name,
            network_config=network_config,
            provision_guest_agent=True
        )
        assert result['instance_name'] == 'some-host'

    def test_reboot_instance(self):
        result = self.vm.reboot_instance(
            cloud_service_name='cloud-service',
            instance_name='instance-name'
        )
        self.service.reboot_role_instance.assert_called_once_with(
            'cloud-service', 'cloud-service', 'instance-name'
        )

    def test_shutdown_instance(self):
        result = self.vm.shutdown_instance(
            cloud_service_name='cloud-service',
            instance_name='instance-name',
            deallocate_resources=True
        )
        self.service.shutdown_role.assert_called_once_with(
            'cloud-service', 'cloud-service',
            'instance-name', 'StoppedDeallocated'
        )

    @raises(AzureVmCreateError)
    def test_create_instance_add_role_raises_on_label(self):
        storage_properties = mock.MagicMock()
        storage_properties.storage_service_properties.location = 'region'
        self.service.get_storage_account_properties.return_value = \
            storage_properties

        service_properties = mock.MagicMock()
        service_properties.hosted_service_properties.location = 'region'
        self.service.get_hosted_service_properties.return_value = \
            service_properties

        image_locations = mock.MagicMock()
        image_locations.location = 'region'
        self.service.get_os_image.return_value = image_locations

        result = self.vm.create_instance(
            cloud_service_name='cloud-service',
            disk_name='foo.vhd',
            system_config=self.system_config,
            label='some-label'
        )

    @raises(AzureVmCreateError)
    def test_create_instance_add_role_raises_on_reserved_ip(self):
        storage_properties = mock.MagicMock()
        storage_properties.storage_service_properties.location = 'region'
        self.service.get_storage_account_properties.return_value = \
            storage_properties

        service_properties = mock.MagicMock()
        service_properties.hosted_service_properties.location = 'region'
        self.service.get_hosted_service_properties.return_value = \
            service_properties

        image_locations = mock.MagicMock()
        image_locations.location = 'region'
        self.service.get_os_image.return_value = image_locations

        result = self.vm.create_instance(
            cloud_service_name='cloud-service',
            disk_name='foo.vhd',
            system_config=self.system_config,
            reserved_ip_name='test_reserved_ip_name'
        )

    @raises(AzureVmCreateError)
    def test_create_instance_raise_vm_create_error(self):
        self.service.get_deployment_by_name.side_effect = Exception(
            '<Code>ResourceNotFound</Code><Message>No deployments were found'
        )
        storage_properties = mock.MagicMock()
        storage_properties.storage_service_properties.location = 'region'
        self.service.get_storage_account_properties.return_value = \
            storage_properties

        service_properties = mock.MagicMock()
        service_properties.hosted_service_properties.location = 'region'
        self.service.get_hosted_service_properties.return_value = \
            service_properties

        image_locations = mock.MagicMock()
        image_locations.location = 'region'
        self.service.get_os_image.return_value = image_locations

        self.service.create_virtual_machine_deployment.side_effect = \
            AzureVmCreateError
        result = self.vm.create_instance(
            'cloud-service', 'foo.vhd', self.system_config
        )

    @raises(AzureVmCreateError)
    def test_create_instance_raise_get_deployment_error(self):
        self.service.get_deployment_by_name.side_effect = Exception
        storage_properties = mock.MagicMock()
        storage_properties.storage_service_properties.location = 'region'
        self.service.get_storage_account_properties.return_value = \
            storage_properties

        service_properties = mock.MagicMock()
        service_properties.hosted_service_properties.location = 'region'
        self.service.get_hosted_service_properties.return_value = \
            service_properties

        image_locations = mock.MagicMock()
        image_locations.location = 'region'
        self.service.get_os_image.return_value = image_locations
        result = self.vm.create_instance(
            'cloud-service', 'foo.vhd', self.system_config
        )

    def test_delete_instance(self):
        self.vm.delete_instance('cloud-service', 'foo')
        self.service.delete_deployment.assert_called_once_with(
            'cloud-service', 'foo'
        )

    @raises(AzureStorageNotReachableByCloudServiceError)
    def test_create_instance_raise_storage_not_reachable_error(self):
        storage_properties = mock.MagicMock()
        storage_properties.storage_service_properties.location = 'regionA'
        self.service.get_storage_account_properties.return_value = \
            storage_properties

        service_properties = mock.MagicMock()
        service_properties.hosted_service_properties.location = 'regionB'
        self.service.get_hosted_service_properties.return_value = \
            service_properties

        result = self.vm.create_instance(
            'foo', 'some-region', 'foo.vhd', self.system_config
        )

    @raises(AzureImageNotReachableByCloudServiceError)
    def test_create_instance_raise_image_not_reachable_error(self):
        storage_properties = mock.MagicMock()
        storage_properties.storage_service_properties.location = 'regionA'
        self.service.get_storage_account_properties.return_value = \
            storage_properties

        service_properties = mock.MagicMock()
        service_properties.hosted_service_properties.location = 'regionA'
        self.service.get_hosted_service_properties.return_value = \
            service_properties

        image_locations = mock.MagicMock()
        image_locations.location = 'regionB'
        self.service.get_os_image.return_value = image_locations

        result = self.vm.create_instance(
            'foo', 'some-region', 'foo.vhd', self.system_config
        )

    @raises(AzureImageNotReachableByCloudServiceError)
    def test_create_instance_raise_image_not_existing(self):
        storage_properties = mock.MagicMock()
        storage_properties.storage_service_properties.location = 'regionA'
        self.service.get_storage_account_properties.return_value = \
            storage_properties

        service_properties = mock.MagicMock()
        service_properties.hosted_service_properties.location = 'regionA'
        self.service.get_hosted_service_properties.return_value = \
            service_properties
        self.service.get_os_image.side_effect = Exception
        result = self.vm.create_instance(
            'foo', 'some-region', 'foo.vhd', self.system_config
        )

    @raises(AzureCustomDataTooLargeError)
    def test_validates_custom_data_length(self):
        self.vm._VirtualMachine__max_custom_data_len = mock.Mock(return_value=3)
        self.vm.create_linux_configuration(custom_data='foo')

        self.vm._VirtualMachine__max_custom_data_len = mock.Mock(return_value=0)
        self.vm.create_linux_configuration(custom_data='foo')

    @raises(AzureVmDeleteError)
    def test_delete_instance_raise_vm_delete_error(self):
        self.service.delete_deployment.side_effect = AzureVmDeleteError
        self.vm.delete_instance('cloud-service', 'foo')

    @raises(AzureVmRebootError)
    def test_reboot_instance_raise_vm_reboot_error(self):
        self.service.reboot_role_instance.side_effect = AzureVmRebootError
        self.vm.reboot_instance('cloud-service', 'foo')

    @raises(AzureVmShutdownError)
    def test_shutdown_instance_raise_vm_shutdown_error(self):
        self.service.shutdown_role.side_effect = AzureVmShutdownError
        self.vm.shutdown_instance('cloud-service', 'foo')
