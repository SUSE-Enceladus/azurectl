import sys
import mock
from mock import patch


from .test_helper import raises

from azurectl.account.service import AzureAccount
from azurectl.config.parser import Config
from azurectl.azurectl_exceptions import *
from azurectl.instance.cloud_service import CloudService

import azurectl

from collections import namedtuple


class TestCloudService:
    def setup(self):
        MyResult = namedtuple(
            'MyResult',
            'request_id'
        )
        self.myrequest = MyResult(request_id=42)
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
        MyPublicIP = namedtuple(
            'MyPublicIP',
            'name address'
        )
        self.public_ips = [MyPublicIP(
            name='name',
            address='address'
        )]
        MyInstanceEndPoint = namedtuple(
            'MyInstanceEndPoint',
            'name vip public_port local_port protocol'
        )
        self.instance_endpoints = [MyInstanceEndPoint(
            name='name',
            vip='vip',
            public_port='public_port',
            local_port='local_port',
            protocol='protocol'
        )]
        MyVirtualIP = namedtuple(
            'MyVirtualIP',
            'address reserved_ip_name type'
        )
        self.virtual_ips = [MyVirtualIP(
            address='address',
            reserved_ip_name='reserved_ip_name',
            type='type'
        )]
        MyInputEndpoint = namedtuple(
            'MyInputEndpoint',
            'role_name vip port'
        )
        self.input_endpoints = [MyInputEndpoint(
            role_name='role_name',
            vip='vip',
            port='port'
        )]
        MyInstance = namedtuple(
            'MyInstance',
            'role_name instance_name instance_status instance_size \
            instance_state_details ip_address power_state fqdn host_name \
            public_ips instance_endpoints'
        )
        self.instances = [MyInstance(
            role_name='role_name',
            instance_name='instance_name',
            instance_status='instance_status',
            instance_size='instance_size',
            instance_state_details='instance_state_details',
            ip_address='ip_address',
            power_state='power_state',
            fqdn='fqdn',
            host_name='host_name',
            public_ips=self.public_ips,
            instance_endpoints=self.instance_endpoints
        )]
        MyServiceProperties = namedtuple(
            'MyServiceProperties',
            'description location affinity_group label status \
             date_created date_last_modified'
        )
        self.hosted_service_properties = MyServiceProperties(
            description='description',
            location='location',
            affinity_group='affinity_group',
            label='label',
            status='status',
            date_created='date_created',
            date_last_modified='date_last_modified'
        )
        MyDeployment = namedtuple(
            'MyDeployment',
            'name deployment_slot private_id status label url created_time \
             last_modified_time virtual_network_name virtual_ips \
             input_endpoint_list role_instance_list'
        )
        self.deployments = [MyDeployment(
            name='name',
            deployment_slot='deployment_slot',
            private_id='private_id',
            status='status',
            label='label',
            url='url',
            created_time='created_time',
            last_modified_time='last_modified_time',
            virtual_network_name='virtual_network_name',
            virtual_ips=self.virtual_ips,
            input_endpoint_list=self.input_endpoints,
            role_instance_list=self.instances
        )]
        MyProperties = namedtuple(
            'MyProperties',
            'service_name hosted_service_properties deployments'
        )
        self.properties = MyProperties(
            service_name='service_name',
            hosted_service_properties=self.hosted_service_properties,
            deployments=self.deployments
        )
        account = AzureAccount(
            Config(
                region_name='East US 2', filename='../data/config'
            )
        )
        self.mgmt_service = mock.Mock()
        account.get_management_service = mock.Mock(
            return_value=self.mgmt_service
        )
        account.storage_key = mock.Mock()
        self.cloud_service = CloudService(account)

    @patch('azurectl.instance.cloud_service.CloudService.get_pem_certificate')
    @patch('azurectl.instance.cloud_service.CloudService.get_fingerprint')
    @patch('azurectl.instance.cloud_service.RequestResult')
    @patch('subprocess.Popen')
    @patch('base64.b64encode')
    def test_add_certificate(
        self, mock_base64, mock_popen, mock_request_result,
        mock_fingerprint, mock_getpem
    ):
        mock_openssl = mock.Mock()
        mock_openssl.communicate = mock.Mock(
            return_value=['pfx-data-stream', 'error']
        )
        mock_openssl.returncode = 0
        mock_popen.return_value = mock_openssl
        mock_getpem.return_value = b'pem-base64-stream'
        mock_base64.return_value = b'base64-pfx-stream'
        mock_fingerprint.return_value = 'finger-print'
        assert self.cloud_service.add_certificate(
            'cloud-service', 'ssh-private-key'
        ) == 'finger-print'
        mock_getpem.assert_called_once_with('ssh-private-key')
        mock_popen.assert_called_once_with(
            [
                'openssl', 'pkcs12', '-export',
                '-inkey', 'ssh-private-key',
                '-in', mock.ANY,
                '-passout', 'pass:'
            ],
            stderr=-1,
            stdout=-1
        )
        mock_base64.assert_called_once_with(
            'pfx-data-stream'
        )
        self.mgmt_service.add_service_certificate.assert_called_once_with(
            'cloud-service', b'base64-pfx-stream', 'pfx', ''
        )
        mock_fingerprint.assert_called_once_with(
            b'pem-base64-stream'
        )

    @patch('subprocess.Popen')
    def test_get_pem_certificate(self, mock_popen):
        mock_openssl = mock.Mock()
        mock_openssl.communicate = mock.Mock(
            return_value=['SHA1 Fingerprint=02:8F:82', 'error']
        )
        mock_openssl.returncode = 0
        mock_popen.return_value = mock_openssl
        self.cloud_service.get_pem_certificate('ssh-private-key')
        mock_popen.assert_called_once_with(
            [
                'openssl', 'req', '-x509', '-key', 'ssh-private-key',
                '-days', '365',
                '-subj', '/C=US/ST=Denial/L=Denial/O=Dis/CN=www.azure.com',
                '-newkey', 'rsa:2048'
            ],
            stderr=-1,
            stdout=-1
        )

    @patch('subprocess.Popen')
    def test_get_fingerprint(self, mock_popen):
        mock_openssl = mock.Mock()
        mock_openssl.communicate = mock.Mock(
            return_value=['SHA1 Fingerprint=02:8F:82', 'error']
        )
        mock_openssl.returncode = 0
        mock_popen.return_value = mock_openssl
        self.cloud_service.get_fingerprint(b'pem-base64-stream')
        mock_popen.assert_called_once_with(
            [
                'openssl', 'x509', '-noout', '-in', mock.ANY,
                '-fingerprint', '-sha1'
            ],
            stderr=-1,
            stdout=-1
        )

    @raises(AzureCloudServiceOpenSSLError)
    def test_get_fingerprint_raise_openssl_error(self):
        self.cloud_service.get_fingerprint(b'foo')

    @raises(AzureCloudServiceOpenSSLError)
    def test_get_pem_certificate_raise_openssl_error(self):
        self.cloud_service.get_pem_certificate('foo')

    @patch('azurectl.instance.cloud_service.CloudService.get_pem_certificate')
    @patch('subprocess.Popen')
    @raises(AzureCloudServiceOpenSSLError)
    def test_add_certificate_raise_openssl_error(self, mock_popen, mock_getpem):
        mock_openssl = mock.Mock()
        mock_openssl.communicate = mock.Mock(
            return_value=['cer-data-stream', 'error']
        )
        mock_openssl.returncode = 1
        mock_popen.return_value = mock_openssl
        mock_getpem.return_value = b'pem-base64-stream'
        self.cloud_service.add_certificate(
            'cloud-service', '../data/id_test'
        )

    @raises(AzureCloudServiceAddCertificateError)
    def test_add_certificate_raise_add_error(self):
        self.mgmt_service.add_service_certificate.side_effect = \
            AzureCloudServiceAddCertificateError
        self.cloud_service.add_certificate('cloud-service', '../data/id_test')

    def test_create(self):
        self.mgmt_service.check_hosted_service_name_availability.return_value \
            = mock.Mock(result=True)
        self.mgmt_service.get_hosted_service_properties.side_effect = \
            AzureError('does-not-exist')
        self.cloud_service.create(
            'cloud-service', 'West US', 'my-cloud', 'label'
        )
        self.mgmt_service.get_hosted_service_properties.assert_called_once_with(
            'cloud-service'
        )
        self.mgmt_service.create_hosted_service.assert_called_once_with(
            service_name='cloud-service',
            description='my-cloud',
            location='West US',
            label='label'
        )

    @raises(AzureCloudServicePropertiesError)
    def test_get_properties_error(self):
        self.mgmt_service.get_hosted_service_properties.side_effect = Exception
        self.cloud_service.get_properties('cloud-service')

    def test_get_properties(self):
        self.mgmt_service.get_hosted_service_properties.return_value = \
            self.properties
        assert self.cloud_service.get_properties('cloud-service') == {
            'status': 'status',
            'roles': [
                {
                    'ip_address': 'ip_address',
                    'instance_status': 'instance_status',
                    'instance_state_details': 'instance_state_details',
                    'name': 'role_name',
                    'instance_size': 'instance_size',
                    'fqdn': 'fqdn',
                    'instance_name': 'instance_name',
                    'public_ips': [
                        {
                            'name': 'name',
                            'address': 'address'
                        }
                    ],
                    'host_name': 'host_name',
                    'power_state': 'power_state',
                    'instance_endpoints': [
                        {
                            'protocol': 'protocol',
                            'local_port': 'local_port',
                            'public_port': 'public_port',
                            'name': 'name', 'virtual_ip': 'vip'
                        }
                    ]
                }
            ],
            'description': 'description',
            'affinity_group': 'affinity_group',
            'date_created': 'date_created',
            'service_name': 'service_name',
            'deployments': [
                {
                    'status': 'status',
                    'private_id': 'private_id',
                    'deployment_slot': 'deployment_slot',
                    'date_last_modified': 'last_modified_time',
                    'virtual_network_name': 'virtual_network_name',
                    'virtual_ips': [
                        {
                            'reserved_ip_name': 'reserved_ip_name',
                            'type': 'type',
                            'address': 'address'
                        }
                    ],
                    'name': 'name',
                    'url': 'url',
                    'label': 'label',
                    'date_created': 'created_time',
                    'input_endpoints': [
                        {
                            'role_name': 'role_name',
                            'virtual_ip': 'vip',
                            'port': 'port'
                        }
                    ]
                },
            ],
            'label': 'label',
            'date_last_modified': 'date_last_modified',
            'location': 'location'
        }

    @raises(AzureCloudServiceAddressError)
    def test_create_cloud_service_in_use(self):
        self.mgmt_service.check_hosted_service_name_availability.return_value \
            = mock.Mock(result=False)
        self.mgmt_service.get_hosted_service_properties.side_effect = \
            AzureError('does-not-exist')
        self.cloud_service.create(
            'cloud-service', 'West US', 'my-cloud', 'label'
        )

    def test_delete(self):
        self.mgmt_service.delete_hosted_service.return_value = self.myrequest
        request_id = self.cloud_service.delete('cloud-service')
        self.mgmt_service.delete_hosted_service.assert_called_once_with(
            'cloud-service', False
        )
        assert request_id == 42

    @raises(AzureCloudServiceCreateError)
    def test_create_service_error(self):
        self.mgmt_service.check_hosted_service_name_availability.return_value \
            = mock.Mock(result=True)
        self.mgmt_service.get_hosted_service_properties.side_effect = Exception
        self.mgmt_service.create_hosted_service.side_effect = \
            AzureCloudServiceCreateError
        self.cloud_service.create(
            'cloud-service', 'West US', 'my-cloud', 'label'
        )

    def test_create_service_exists(self):
        request_id = self.cloud_service.create(
            'cloud-service', 'region', 'my-cloud', 'label'
        )
        assert request_id == 0

    @raises(AzureCloudServiceDeleteError)
    def test_delete_service_error(self):
        self.mgmt_service.delete_hosted_service.side_effect = \
            AzureCloudServiceDeleteError
        self.cloud_service.delete('cloud-service')
