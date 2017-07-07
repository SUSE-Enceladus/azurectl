# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import base64
import subprocess
from tempfile import NamedTemporaryFile

# project
from azurectl.azurectl_exceptions import (
    AzureCloudServiceAddressError,
    AzureCloudServiceOpenSSLError,
    AzureCloudServiceAddCertificateError,
    AzureCloudServiceCreateError,
    AzureCloudServiceDeleteError,
    AzureCloudServicePropertiesError
)
from azurectl.management.request_result import RequestResult


class CloudService(object):
    """
        Implements creation/deletion and management of cloud
        services required to run virtual machine instances
    """
    def __init__(self, account):
        self.account = account
        self.service = self.account.get_management_service()

    def get_pem_certificate(self, ssh_private_key_file):
        """
            create PEM certificate from given ssh private key file
        """
        openssl = subprocess.Popen(
            [
                'openssl', 'req', '-x509',
                '-key', ssh_private_key_file,
                '-days', '365',
                '-subj', '/C=US/ST=Denial/L=Denial/O=Dis/CN=www.azure.com',
                '-newkey', 'rsa:2048'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        pem_cert, openssl_error = openssl.communicate()
        if openssl.returncode != 0:
            raise AzureCloudServiceOpenSSLError(
                '%s' % openssl_error
            )
        return pem_cert

    def get_fingerprint(self, pem_cert):
        """
            create sha1 fingerprint from given pem base64 certificate
        """
        pem_cert_file = NamedTemporaryFile()
        pem_cert_file.write(pem_cert)
        pem_cert_file.flush()
        openssl = subprocess.Popen(
            [
                'openssl', 'x509', '-noout',
                '-in', pem_cert_file.name,
                '-fingerprint', '-sha1'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        fingerprint, openssl_error = openssl.communicate()
        if openssl.returncode != 0:
            raise AzureCloudServiceOpenSSLError(
                '%s' % openssl_error
            )
        fingerprint = fingerprint.split('=')[1]
        fingerprint = fingerprint.replace(':', '')
        return fingerprint.strip()

    def add_certificate(
        self, cloud_service_name, ssh_private_key_file
    ):
        """
            create Azure conform certificate from given ssh private
            key and add the CER formatted public pem file to the
            cloud service. The method returns the certificate
            fingerprint
        """
        pem_cert = self.get_pem_certificate(
            ssh_private_key_file
        )
        pem_cert_file = NamedTemporaryFile()
        pem_cert_file.write(pem_cert)
        pem_cert_file.flush()
        openssl = subprocess.Popen(
            [
                'openssl', 'pkcs12', '-export',
                '-inkey', ssh_private_key_file,
                '-in', pem_cert_file.name,
                '-passout', 'pass:'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        pfx_cert, openssl_error = openssl.communicate()
        if openssl.returncode != 0:
            raise AzureCloudServiceOpenSSLError(
                '%s' % openssl_error
            )
        try:
            add_cert_request = self.service.add_service_certificate(
                cloud_service_name, base64.b64encode(pfx_cert), 'pfx', ''
            )
        except Exception as e:
            raise AzureCloudServiceAddCertificateError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        # Wait for the certficate to be created
        request_result = RequestResult(add_cert_request.request_id)
        request_result.wait_for_request_completion(
            self.service
        )
        return self.get_fingerprint(pem_cert)

    def create(
        self, cloud_service_name, location,
        description='CloudService', label=None
    ):
        """
            create cloud service with specified name and return the
            request id
        """
        service_record = {
            'service_name': cloud_service_name,
            'label': cloud_service_name,
            'description': description,
            'location': location
        }
        if label:
            service_record['label'] = label

        if self.__cloud_service_exists(cloud_service_name):
            # indicate an existing cloud service by returning request id: 0
            return 0

        if self.__cloud_service_url_in_use(cloud_service_name):
            message = (
                'The cloud service name "%s" '
                'is already in use. '
                'Please choose a different name.'
            )
            raise AzureCloudServiceAddressError(message % cloud_service_name)

        try:
            result = self.service.create_hosted_service(**service_record)
            return (result.request_id)
        except Exception as e:
            raise AzureCloudServiceCreateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def delete(self, cloud_service_name, complete=False):
        """
            delete specified cloud service, if complete is set to true
            all OS/data disks and the source blobs for the disks will be
            deleted too
        """
        try:
            result = self.service.delete_hosted_service(
                cloud_service_name, complete
            )
            return (result.request_id)
        except Exception as e:
            raise AzureCloudServiceDeleteError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def get_properties(self, cloud_service_name, include_instance_info=True):
        """
            Retrieves system properties for the specified cloud
            service and its instances
        """
        try:
            properties = self.service.get_hosted_service_properties(
                service_name=cloud_service_name,
                embed_detail=include_instance_info
            )
            return self.__decorate_properties_for_results(properties)
        except Exception as e:
            raise AzureCloudServicePropertiesError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def __cloud_service_exists(self, cloud_service_name):
        try:
            return self.service.get_hosted_service_properties(
                cloud_service_name
            )
        except Exception:
            pass

    def __cloud_service_url_in_use(self, cloud_service_name):
        availability = self.service.check_hosted_service_name_availability(
            cloud_service_name
        )
        return not availability.result

    @classmethod
    def __decorate_deployment_for_results(self, deployment):
        return {
            'name': deployment.name,
            'deployment_slot': deployment.deployment_slot,
            'private_id': deployment.private_id,
            'status': deployment.status,
            'label': deployment.label,
            'url': deployment.url,
            'date_created': deployment.created_time,
            'date_last_modified': deployment.last_modified_time,
            'virtual_network_name': deployment.virtual_network_name
        }

    @classmethod
    def __decorate_virtual_ips_for_results(self, deployment):
        virtual_ips = deployment.virtual_ips or []
        result = []
        for virtual_ip in virtual_ips:
            result.append({
                'address': virtual_ip.address,
                'reserved_ip_name': virtual_ip.reserved_ip_name,
                'type': virtual_ip.type
            })
        return result

    @classmethod
    def __decorate_input_endpoints_for_result(self, deployment):
        endpoints = deployment.input_endpoint_list or []
        result = []
        for endpoint in endpoints:
            result.append({
                'role_name': endpoint.role_name,
                'virtual_ip': endpoint.vip,
                'port': endpoint.port
            })
        return result

    @classmethod
    def __decorate_instance_for_result(self, instance):
        return {
            'name': instance.role_name,
            'instance_name': instance.instance_name,
            'instance_status': instance.instance_status,
            'instance_size': instance.instance_size,
            'instance_state_details': instance.instance_state_details,
            'ip_address': instance.ip_address,
            'power_state': instance.power_state,
            'fqdn': instance.fqdn,
            'host_name': instance.host_name,
        }

    @classmethod
    def __decorate_instance_public_ips_for_result(self, instance):
        public_ips = instance.public_ips or []
        result = []
        for public_ip in public_ips:
            result.append({
                'name': public_ip.name,
                'address': public_ip.address
            })
        return result

    @classmethod
    def __decorate_instance_endpoints_for_result(self, instance):
        instance_endpoints = instance.instance_endpoints or []
        result = []
        for instance_endpoint in instance_endpoints:
            result.append({
                'name': instance_endpoint.name,
                'virtual_ip': instance_endpoint.vip,
                'public_port': instance_endpoint.public_port,
                'local_port': instance_endpoint.local_port,
                'protocol': instance_endpoint.protocol
            })
        return result

    @classmethod
    def __decorate_properties_for_results(self, properties):
        hosted_service_properties = properties.hosted_service_properties
        result = {
            'service_name': properties.service_name,
            'description': hosted_service_properties.description,
            'location': hosted_service_properties.location,
            'affinity_group': hosted_service_properties.affinity_group,
            'label': hosted_service_properties.label,
            'status': hosted_service_properties.status,
            'date_created': hosted_service_properties.date_created,
            'date_last_modified': hosted_service_properties.date_last_modified
        }
        result['deployments'] = []
        result['roles'] = []
        for deployment in properties.deployments:
            deployment_result = self.__decorate_deployment_for_results(
                deployment
            )
            deployment_result['virtual_ips'] = \
                self.__decorate_virtual_ips_for_results(deployment)
            deployment_result['input_endpoints'] = \
                self.__decorate_input_endpoints_for_result(deployment)

            for instance in deployment.role_instance_list:
                instance_result = self.__decorate_instance_for_result(instance)
                instance_result['public_ips'] = \
                    self.__decorate_instance_public_ips_for_result(instance)
                instance_result['instance_endpoints'] = \
                    self.__decorate_instance_endpoints_for_result(instance)
                result['roles'].append(instance_result)

            result['deployments'].append(deployment_result)
        return result
