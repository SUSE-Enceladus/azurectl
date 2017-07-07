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
from azure.storage.blob.baseblobservice import BaseBlobService
from azure.storage.sharedaccesssignature import SharedAccessSignature

# project
from azurectl.azurectl_exceptions import (
    AzureCannotInit,
    AzureContainerListError,
    AzureContainerListContentError,
    AzureContainerCreateError,
    AzureContainerDeleteError
)

ISO8061_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


class Container(object):
    """
        Information from Azure storage containers
    """
    def __init__(
        self,
        account=None,
        account_name=None,
        key=None,
        blob_service_host_base=None
    ):
        if account:
            self.account_name = account.storage_name()
            self.account_key = account.storage_key()
            self.blob_service_host_base = account.get_blob_service_host_base()
        elif (account_name and key and blob_service_host_base):
            self.account_name = account_name
            self.account_key = key
            self.blob_service_host_base = blob_service_host_base
        else:
            raise AzureCannotInit('''
                Either an account, or account_name, key, and service host base
                are required.
            ''')

    def list(self):
        result = []
        blob_service = BaseBlobService(
            self.account_name,
            self.account_key,
            endpoint_suffix=self.blob_service_host_base
        )
        try:
            for container in blob_service.list_containers():
                result.append(format(container.name))
        except Exception as e:
            raise AzureContainerListError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        return result

    def exists(self, container):
        blob_service = BaseBlobService(
            self.account_name,
            self.account_key,
            endpoint_suffix=self.blob_service_host_base
        )
        try:
            blob_service.get_container_properties(container)
            return True
        except Exception:
            return False

    def create(self, container):
        blob_service = BaseBlobService(
            self.account_name,
            self.account_key,
            endpoint_suffix=self.blob_service_host_base
        )
        try:
            blob_service.create_container(
                container_name=container,
                fail_on_exist=True
            )
        except Exception as e:
            raise AzureContainerCreateError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        return True

    def delete(self, container):
        blob_service = BaseBlobService(
            self.account_name,
            self.account_key,
            endpoint_suffix=self.blob_service_host_base
        )
        try:
            blob_service.delete_container(
                container_name=container,
                fail_not_exist=True
            )
        except Exception as e:
            raise AzureContainerDeleteError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        return True

    def content(self, container):
        result = {container: []}
        blob_service = BaseBlobService(
            self.account_name,
            self.account_key,
            endpoint_suffix=self.blob_service_host_base
        )
        try:
            for blob in blob_service.list_blobs(container):
                result[container].append(format(blob.name))
            return result
        except Exception as e:
            raise AzureContainerListContentError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def sas(self, container, start, expiry, permissions):
        sas = SharedAccessSignature(
            self.account_name, self.account_key
        )
        signed_query = sas.generate_container(
            container_name=container,
            permission=permissions,
            expiry=expiry.strftime(ISO8061_FORMAT),
            start=start.strftime(ISO8061_FORMAT)
        )
        return 'https://{0}.blob.core.windows.net/{1}?{2}'.format(
            self.account_name, container, signed_query
        )
