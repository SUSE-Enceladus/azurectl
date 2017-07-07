import sys
import mock
import random
from collections import namedtuple
from datetime import datetime
from mock import patch
from .test_helper import raises
# mocks
from azure.servicemanagement.models import (
    PersistentVMRole,
    ConfigurationSets,
    ConfigurationSet,
    ConfigurationSetInputEndpoint,
    DataVirtualHardDisks,
    OSVirtualHardDisk,

)
# project
from azurectl.account.service import AzureAccount
from azurectl.azurectl_exceptions import *
from azurectl.config.parser import Config
from azurectl.instance.endpoint import Endpoint
import azurectl


class TestEndpoint:
    def setup(self):
        # construct an account
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
        # now that that's done, instantiate an Endpoint with the account
        self.endpoint = Endpoint(account)
        # asynchronous API operations return a request object
        self.my_request = mock.Mock(request_id=42)
        # variables used in multiple tests
        self.cloud_service_name = 'mockcloudservice'
        self.instance_name = 'mockcloudserviceinstance1'
        self.endpoint_name = 'HTTPS'
        self.port = '443'
        self.idle_timeout = 10
        self.protocol = 'tcp'
        self.udp_endpoint_name = 'SNMP'
        self.udp_port = '131'
        self.instance_port = '10000'
        self.udp_protocol = 'udp'
        # identify the instance for the Endpoint to work on
        self.endpoint.set_instance(self.cloud_service_name, self.instance_name)
        # mock out the get_role function of service
        self.service.get_role = mock.Mock(return_value = self.mock_role())

    def mock_role(self, has_endpoint=True):
        role = PersistentVMRole()
        role.role_name = self.instance_name
        network_config = ConfigurationSet()
        if has_endpoint:
            endpoint = ConfigurationSetInputEndpoint(
                name=self.endpoint_name,
                protocol='tcp',
                port=self.port,
                local_port=self.port,
                idle_timeout_in_minutes=self.idle_timeout
            )
            network_config.input_endpoints.input_endpoints.append(endpoint)
        else:
            # Azure sets endpoints list to None if all
            # endpoints are deleted.
            network_config.input_endpoints = None
        role.configuration_sets.configuration_sets.append(network_config)
        return role

    def create_expected_endpoint_output(self):
        return {
            'idle-timeout': '%d minutes' % self.idle_timeout,
            'instance-port': self.port,
            'name': self.endpoint_name,
            'port': self.port,
            'protocol': self.protocol
        }

    def test_create(self):
        # given
        self.service.update_role.return_value = self.my_request
        mock_role = self.mock_role(has_endpoint=False)
        self.service.get_role = mock.Mock(return_value=mock_role)
        endpoint_len = 0
        # when
        result = self.endpoint.create(
            self.udp_endpoint_name,
            self.udp_port,
            self.instance_port,
            self.udp_protocol,
            self.idle_timeout
        )
        result_endpoint_length = len(
            mock_role.configuration_sets[0].input_endpoints
        )
        new_endpoint = mock_role.configuration_sets[0].input_endpoints[-1]
        # then
        assert result_endpoint_length == endpoint_len + 1
        assert new_endpoint.name == self.udp_endpoint_name
        assert new_endpoint.port == self.udp_port
        assert new_endpoint.local_port == self.instance_port
        assert new_endpoint.protocol == self.udp_protocol
        self.service.update_role.assert_called_once_with(
            self.cloud_service_name,
            self.cloud_service_name,
            self.instance_name,
            os_virtual_hard_disk=mock_role.os_virtual_hard_disk,
            network_config=mock_role.configuration_sets[0],
            availability_set_name=mock_role.availability_set_name,
            data_virtual_hard_disks=mock_role.data_virtual_hard_disks
        )
        assert result == self.my_request.request_id

    # then
    @raises(AzureEndpointCreateError)
    def test_create_upstream_exception(self):
        # given
        self.service.update_role.side_effect = Exception
        # when
        result = self.endpoint.create(
            self.endpoint_name,
            self.port,
            self.instance_port,
            self.protocol,
            self.idle_timeout
        )

    def test_update(self):
        # given
        self.service.update_role.return_value = self.my_request
        mock_role = self.mock_role()
        self.service.get_role = mock.Mock(return_value=mock_role)
        # when
        result = self.endpoint.update(
            self.endpoint_name,
            self.udp_port,
            self.instance_port,
            self.udp_protocol,
            self.idle_timeout
        )
        new_endpoint = mock_role.configuration_sets[0].input_endpoints[0]
        # then
        assert new_endpoint.name == self.endpoint_name
        assert new_endpoint.port == self.udp_port
        assert new_endpoint.local_port == self.instance_port
        assert new_endpoint.protocol == self.udp_protocol
        self.service.update_role.assert_called_once_with(
            self.cloud_service_name,
            self.cloud_service_name,
            self.instance_name,
            os_virtual_hard_disk=mock_role.os_virtual_hard_disk,
            network_config=mock_role.configuration_sets[0],
            availability_set_name=mock_role.availability_set_name,
            data_virtual_hard_disks=mock_role.data_virtual_hard_disks
        )
        assert result == self.my_request.request_id

    # then
    @raises(AzureEndpointUpdateError)
    def test_update_upstream_exception(self):
        # given
        self.service.update_role.side_effect = Exception
        # when
        result = self.endpoint.update(
            self.udp_endpoint_name,
            self.port,
            self.instance_port,
            self.protocol,
            self.idle_timeout
        )

    @raises(AzureEndpointUpdateError)
    def test_update_endpoint_no_endpoints(self):
        # given
        mock_role = self.mock_role(has_endpoint=False)
        self.service.get_role = mock.Mock(return_value=mock_role)
        self.service.update_role.return_value = self.my_request

        # when
        self.endpoint.update(
            self.udp_endpoint_name,
            self.port,
            self.instance_port,
            self.udp_protocol,
            self.idle_timeout
        )

    def test_show(self):
        # given
        expected = self.create_expected_endpoint_output()
        # when
        result = self.endpoint.show(self.endpoint_name)
        # then
        assert result == expected

    # then
    @raises(AzureEndpointShowError)
    def test_show_upstream_exception(self):
        # given
        self.service.get_role.side_effect = Exception
        # when
        self.endpoint.show(self.endpoint_name)

    # then
    @raises(AzureEndpointShowError)
    def test_show_not_found(self):
        # given
        self.service.get_role = mock.Mock(
            return_value=self.mock_role(has_endpoint=False)
        )
        # when
        self.endpoint.show(self.endpoint_name)

    def test_list(self):
        # given
        expected = [
            self.create_expected_endpoint_output()
        ]
        # when
        result = self.endpoint.list()
        # then
        assert result == expected

    def test_list_no_endpoints(self):
        # given
        self.endpoint.delete(self.endpoint_name)
        expected = []
        # when
        result = self.endpoint.list()
        # then
        assert result == expected

    # then
    @raises(AzureEndpointListError)
    def test_list_upstream_exceptions(self):
        # given
        self.service.get_role.side_effect = Exception
        # when
        self.endpoint.list()

    def test_delete(self):
        # given
        mock_role = self.mock_role()
        self.service.get_role = mock.Mock(return_value=mock_role)
        self.service.update_role.return_value = self.my_request
        # when
        result = self.endpoint.delete(self.endpoint_name)
        # then
        assert result == self.my_request.request_id
        self.service.update_role.assert_called_once_with(
            self.cloud_service_name,
            self.cloud_service_name,
            self.instance_name,
            os_virtual_hard_disk=mock_role.os_virtual_hard_disk,
            network_config=mock_role.configuration_sets[0],
            availability_set_name=mock_role.availability_set_name,
            data_virtual_hard_disks=mock_role.data_virtual_hard_disks
        )

    # then
    @raises(AzureEndpointDeleteError)
    def test_delete_with_upstream_exception(self):
        # given
        self.service.update_role.side_effect = Exception
        # when
        self.endpoint.delete(self.endpoint_name)

    @raises(AzureEndpointDeleteError)
    def test_delete_endpoint_no_endpoints(self):
        # given
        mock_role = self.mock_role(has_endpoint=False)
        self.service.get_role = mock.Mock(return_value=mock_role)
        self.service.update_role.return_value = self.my_request

        # when
        self.endpoint.delete('foo')

    @raises(AzureEndpointDeleteError)
    def test_delete_endpoint_not_found(self):
        # given
        mock_role = self.mock_role()
        self.service.get_role = mock.Mock(return_value=mock_role)
        self.service.update_role.return_value = self.my_request

        self.endpoint.delete('foo')
