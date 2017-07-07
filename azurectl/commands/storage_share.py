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
Azure File storage provides file shares mountable on a virtual machine, through
the SMB protocol.

usage: azurectl storage share -h | --help
       azurectl storage share create --name=<sharename>
       azurectl storage share list
       azurectl storage share delete --name=<sharename>
       azurectl storage share help

commands:
    create
        create file share in the storage account
    delete
        delete share from the storage account
    help
        show manual page for share command
    list
        list share names

options:
    --name=<sharename>
        name of the files share
"""
# project
from .base import CliTask
from azurectl.account.service import AzureAccount
from azurectl.utils.collector import DataCollector
from azurectl.utils.output import DataOutput
from azurectl.logger import log
from azurectl.storage.fileshare import FileShare
from azurectl.help import Help


class StorageShareTask(CliTask):
    """
        Process file share commands
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

        self.fileshare = FileShare(self.account)

        if self.command_args['list']:
            self.__share_list()
        elif self.command_args['create']:
            self.__share_create()
        elif self.command_args['delete']:
            self.__share_delete()

    def __help(self):
        if self.command_args['help']:
            self.manual.show('azurectl::storage::share')
        else:
            return False
        return self.manual

    def __share_list(self):
        self.result.add('share_names', self.fileshare.list())
        self.out.display()

    def __share_create(self):
        share_name = self.command_args['--name']
        self.fileshare.create(share_name)
        log.info('Created Files Share %s', share_name)

    def __share_delete(self):
        share_name = self.command_args['--name']
        self.fileshare.delete(share_name)
        log.info('Deleted Files Share %s', share_name)
