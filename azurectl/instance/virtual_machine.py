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
from azure.servicemanagement import ConfigurationSetInputEndpoint
from azure.servicemanagement import ConfigurationSet
from azure.servicemanagement import PublicKey
from azure.servicemanagement import LinuxConfigurationSet
from azure.servicemanagement import OSVirtualHardDisk
from azure.storage.blob.baseblobservice import BaseBlobService

# project
from azurectl.azurectl_exceptions import (
    AzureCustomDataTooLargeError,
    AzureVmCreateError,
    AzureVmDeleteError,
    AzureVmRebootError,
    AzureVmShutdownError,
    AzureVmStartError,
    AzureStorageNotReachableByCloudServiceError,
    AzureImageNotReachableByCloudServiceError
)


class VirtualMachine(object):
    """
        Implements creation/deletion and management of virtual
        machine instances from a given image name
    """
    def __init__(self, account):
        self.account = account
        self.service = self.account.get_management_service()

    def create_linux_configuration(
        self, username='azureuser', instance_name=None,
        disable_ssh_password_authentication=True,
        password=None, custom_data=None, fingerprint=''
    ):
        """
            create a linux configuration
        """
        self.__validate_custom_data_length(custom_data)
        # The given instance name is used as the host name in linux
        linux_config = LinuxConfigurationSet(
            instance_name, username, password,
            disable_ssh_password_authentication,
            custom_data
        )
        if fingerprint:
            ssh_key_file = '/home/' + username + '/.ssh/authorized_keys'
            ssh_pub_key = PublicKey(
                fingerprint, ssh_key_file
            )
            linux_config.ssh.public_keys = [ssh_pub_key]
        return linux_config

    def create_network_configuration(self, network_endpoints):
        """
            create a network configuration
        """
        network_config = ConfigurationSet()
        for endpoint in network_endpoints:
            network_config.input_endpoints.input_endpoints.append(endpoint)
        network_config.configuration_set_type = 'NetworkConfiguration'
        return network_config

    def create_network_endpoint(
        self, name, public_port, local_port, protocol
    ):
        """
            create a network service endpoint
        """
        return ConfigurationSetInputEndpoint(
            name, protocol, public_port, local_port
        )

    def create_instance(
        self, cloud_service_name, disk_name, system_config,
        network_config=None, label=None, group='production',
        machine_size='Small', reserved_ip_name=None
    ):
        """
            create a virtual disk image instance
        """
        if not self.__storage_reachable_by_cloud_service(cloud_service_name):
            message = [
                'The cloud service "%s" and the storage account "%s"',
                'are not in the same region, cannot launch an instance.'
            ]
            raise AzureStorageNotReachableByCloudServiceError(
                ' '.join(message) % (
                    cloud_service_name, self.account.storage_name()
                )
            )

        if not self.__image_reachable_by_cloud_service(
            cloud_service_name, disk_name
        ):
            message = [
                'The selected image "%s" is not available',
                'in the region of the selected cloud service "%s",',
                'cannot launch instance'
            ]
            raise AzureImageNotReachableByCloudServiceError(
                ' '.join(message) % (
                    disk_name, cloud_service_name
                )
            )

        deployment_exists = self.__get_deployment(
            cloud_service_name
        )

        if label and deployment_exists:
            message = [
                'A deployment of the name: %s already exists.',
                'Assignment of a label can only happen for the',
                'initial deployment.'
            ]
            raise AzureVmCreateError(
                ' '.join(message) % cloud_service_name
            )

        if reserved_ip_name and deployment_exists:
            message = [
                'A deployment of the name: %s already exists.',
                'Assignment of a reserved IP name can only happen for the',
                'initial deployment.'
            ]
            raise AzureVmCreateError(
                ' '.join(message) % cloud_service_name
            )

        storage = BaseBlobService(
            self.account.storage_name(),
            self.account.storage_key(),
            endpoint_suffix=self.account.get_blob_service_host_base()
        )
        media_link = storage.make_blob_url(
            self.account.storage_container(), ''.join(
                [
                    cloud_service_name,
                    '_instance_', system_config.host_name,
                    '_image_', disk_name
                ]
            )
        )
        instance_disk = OSVirtualHardDisk(disk_name, media_link)
        instance_record = {
            'deployment_name': cloud_service_name,
            'network_config': network_config,
            'role_name': system_config.host_name,
            'role_size': machine_size,
            'service_name': cloud_service_name,
            'system_config': system_config,
            'os_virtual_hard_disk': instance_disk,
            'provision_guest_agent': True
        }
        if network_config:
            instance_record['network_config'] = network_config

        try:
            if deployment_exists:
                result = self.service.add_role(
                    **instance_record
                )
            else:
                instance_record['deployment_slot'] = group
                if reserved_ip_name:
                    instance_record['reserved_ip_name'] = reserved_ip_name
                if label:
                    instance_record['label'] = label
                else:
                    instance_record['label'] = cloud_service_name
                result = self.service.create_virtual_machine_deployment(
                    **instance_record
                )
            return {
                'request_id': format(result.request_id),
                'cloud_service_name': cloud_service_name,
                'instance_name': system_config.host_name
            }
        except Exception as e:
            raise AzureVmCreateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def delete_instance(
        self, cloud_service_name, instance_name
    ):
        """
            delete a virtual disk image instance
        """
        try:
            result = self.service.delete_role(
                cloud_service_name, cloud_service_name, instance_name, True
            )
            return(format(result.request_id))
        except Exception as e:
            raise AzureVmDeleteError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def shutdown_instance(
        self, cloud_service_name, instance_name, deallocate_resources=False
    ):
        """
            Shuts down the specified virtual disk image instance
            If deallocate_resources is set to true the machine shuts down
            and releases the compute resources. You are not billed for
            the compute resources that this Virtual Machine uses in this case.
            If a static Virtual Network IP address is assigned to the
            Virtual Machine, it is reserved.
        """
        post_shutdown_action = 'Stopped'
        if deallocate_resources:
            post_shutdown_action = 'StoppedDeallocated'
        try:
            result = self.service.shutdown_role(
                cloud_service_name, cloud_service_name,
                instance_name, post_shutdown_action
            )
            return(format(result.request_id))
        except Exception as e:
            raise AzureVmShutdownError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def start_instance(
        self, cloud_service_name, instance_name
    ):
        """
            Start the specified virtual disk image instance.
        """
        try:
            result = self.service.start_role(
                cloud_service_name, cloud_service_name,
                instance_name
            )
            return(format(result.request_id))
        except Exception as e:
            raise AzureVmStartError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def reboot_instance(
        self, cloud_service_name, instance_name
    ):
        """
            Requests reboot of a virtual disk image instance
        """
        try:
            result = self.service.reboot_role_instance(
                cloud_service_name, cloud_service_name, instance_name
            )
            return(format(result.request_id))
        except Exception as e:
            raise AzureVmRebootError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def instance_status(
        self, cloud_service_name, instance_name=None
    ):
        """
            Request instance status. An instance can be in different
            states like Initializing, Running, Stopped. This method
            returns the current state name.
        """
        instance_state = 'Undefined'
        if not instance_name:
            instance_name = cloud_service_name
        try:
            properties = self.service.get_hosted_service_properties(
                service_name=cloud_service_name,
                embed_detail=True
            )
            for deployment in properties.deployments:
                for instance in deployment.role_instance_list:
                    if instance.instance_name == instance_name:
                        instance_state = instance.instance_status
        except Exception:
            # if the properties can't be requested due to an error
            # the default state value set to Undefined will be returned
            pass

        return instance_state

    def __validate_custom_data_length(self, custom_data):
        if (custom_data and (len(custom_data) > self.__max_custom_data_len())):
            raise AzureCustomDataTooLargeError(
                "The custom data specified is too large. Custom Data must" +
                "be less than %d bytes" % self.__max_custom_data_len()
            )
        return True

    def __get_deployment(self, cloud_service_name):
        """
            check if the virtual machine deployment already exists.
            Any other than a ResourceNotFound error will be treated
            as an exception to stop processing
        """
        try:
            return self.service.get_deployment_by_name(
                service_name=cloud_service_name,
                deployment_name=cloud_service_name
            )
        except Exception as e:
            if 'ResourceNotFound' in format(e):
                return None

            raise AzureVmCreateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def __cloud_service_location(self, cloud_service_name):
        return self.service.get_hosted_service_properties(
            cloud_service_name
        ).hosted_service_properties.location

    def __storage_location(self):
        return self.service.get_storage_account_properties(
            self.account.storage_name()
        ).storage_service_properties.location

    def __image_locations(self, disk_name):
        try:
            image_properties = self.service.get_os_image(disk_name)
            return image_properties.location.split(';')
        except Exception:
            # if image does not exist return without an exception.
            pass

    def __storage_reachable_by_cloud_service(self, cloud_service_name):
        service_location = self.__cloud_service_location(
            cloud_service_name
        )
        storage_location = self.__storage_location()
        if service_location == storage_location:
            return True
        else:
            return False

    def __image_reachable_by_cloud_service(self, cloud_service_name, disk_name):
        service_location = self.__cloud_service_location(
            cloud_service_name
        )
        image_locations = self.__image_locations(disk_name)
        if not image_locations:
            return False
        if service_location in image_locations:
            return True
        else:
            return False

    def __max_custom_data_len(self):
        """
            Custom Data is limited to 64K
            https://msdn.microsoft.com/library/azure/jj157186.aspx
        """
        return 65536
