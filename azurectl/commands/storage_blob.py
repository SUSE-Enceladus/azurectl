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
"""
Azure blobs describe data files living inside of a container managed by
an Azure storage account. Several operations in Azure requires those data
files to be accessaible from the same region and storage account compared
to the origin of the request. Thus blob operations to e.g copy data
files between regions and/or accounts are needed and handled in this
command.

usage: azurectl storage blob copy -h | --help
       azurectl storage blob copy --source-blob=<blob-name>
           [--destination-region=<region>]
           [--destination-storage-account=<storage-account-name>]
           [--destination-container=<storage-container-name>]
           [--destination-blob=<blob-name>]
       azurectl storage blob help

commands:
    copy
        copy data files between regions and storage accounts/containers
    help
        show manual page for storage blob command

options:
    --source-blob=<blob-name>
        Name of the blob to copy from
    --destination-region=<region>
        Azure region name where the copy will be created. If omitted, the
        source region will be used as the destination
    --destination-storage-account=<storage-account-name>
        Azure storage account name where the copy will be created.
        If omitted, the source account will be used as the destination.
        NOTE: the supplied storage-account must exist in the
        destination region
    --destination-container=<storage-container-name>
        Azure storage container name, in the destination storage account,
        where the copy will be contained.
        If omitted, the source container will be used as the destination.
        NOTE: the supplied storage-container must exist in the destination
        region and storage account
    --destination-blob=<blob-name>
        Name of the copied blob.
        If ommitted, the source name will be used for the copy.
        NOTE: if the source is copied inside of the same region, storage
        account and container, the destination blob name must be different
        from the source blob name
"""
# project
from base import CliTask
from azurectl.account.service import AzureAccount
from azurectl.utils.collector import DataCollector
from azurectl.utils.output import DataOutput
from azurectl.logger import log
from azurectl.help import Help


class StorageBlobTask(CliTask):
    """
        Process storage commands on blobs
    """
    def process(self):
        self.manual = Help()
        if self.__help():
            return

        self.result = DataCollector()
        self.out = DataOutput(
            self.result,
            self.global_args['--output-format'],
            self.global_args['--output-style']
        )

        self.load_config()

        self.account = AzureAccount(self.config)

        if self.command_args['copy']:
            self.__blob_copy()

    def __help(self):
        if self.command_args['help']:
            self.manual.show('azurectl::storage::blob')
        else:
            return False
        return self.manual

    def __blob_copy(self):
        # TODO: needs implementation
        pass
