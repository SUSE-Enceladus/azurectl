import sys
import mock
from collections import namedtuple
from mock import patch
from mock import call


from test_helper import *

from azurectl.account.service import AzureAccount
from azurectl.config.parser import Config
from azurectl.azurectl_exceptions import *
from azurectl.instance.reserved_ip import ReservedIp

import azurectl


class TestReservedIp:
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

        MyStruct = namedtuple(
            'MyStruct',
            'name address label state in_use service_name deployment_name \
            location'
        )

        self.list_ips = [MyStruct(
            name='some-name',
            address='1.2.3.4',
            label='',
            state='Created',
            in_use=True,
            service_name='foo',
            deployment_name='bar',
            location='Region'
        )]

        self.result_list = [{
            'name': 'some-name',
            'address': '1.2.3.4',
            'state': 'Created',
            'in_use': True,
            'cloud_service_name': 'foo',
            'instance_name': 'bar',
            'region': 'Region'
        }]

        MyResult = namedtuple(
            'MyResult',
            'request_id'
        )
        self.myrequest = MyResult(request_id=42)

        self.reserved_ip = ReservedIp(account)

    def test_list(self):
        self.service.list_reserved_ip_addresses.return_value = self.list_ips
        assert self.reserved_ip.list() == self.result_list

    @raises(AzureReservedIpListError)
    def test_list_raises_error(self):
        self.service.list_reserved_ip_addresses.side_effect = Exception
        self.reserved_ip.list()

    def test_show(self):
        mock_response = self.list_ips[0]
        self.service.get_reserved_ip_address.return_value = mock_response
        assert self.reserved_ip.show(mock_response.name) == self.result_list[0]

    @raises(AzureReservedIpShowError)
    def test_show_raises_error(self):
        mock_response = self.list_ips[0]
        self.service.get_reserved_ip_address.side_effect = Exception
        self.reserved_ip.show(mock_response.name)

    def test_create(self):
        self.service.create_reserved_ip_address.return_value = self.myrequest
        request_id = self.reserved_ip.create('some-name', 'East US 2')
        assert request_id == 42
        self.service.create_reserved_ip_address.assert_called_once_with(
            'some-name',
            location='East US 2'
        )

    @raises(AzureReservedIpCreateError)
    def test_create_raises_error(self):
        self.service.create_reserved_ip_address.side_effect = Exception
        self.reserved_ip.create('some-name', 'East US 2')

    def test_delete(self):
        self.service.delete_reserved_ip_address.return_value = self.myrequest
        request_id = self.reserved_ip.delete('some-name')
        assert request_id == 42
        self.service.delete_reserved_ip_address.assert_called_once_with(
            'some-name'
        )

    @raises(AzureReservedIpDeleteError)
    def test_delete_raises_error(self):
        self.service.delete_reserved_ip_address.side_effect = Exception
        self.reserved_ip.delete('some-name')
