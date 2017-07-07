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
Storage accounts are subdivided into containers, within which contents are
stored as binary blobs.

usage: azurectl storage container -h | --help
       azurectl storage container create --name=<containername>
       azurectl storage container sas
           [--name=<containername>]
           [--start-datetime=<start>]
           [--expiry-datetime=<expiry>]
           [--permissions=<permissions>]
       azurectl storage container list
       azurectl storage container show --name=<containername>
       azurectl storage container delete --name=<containername>
       azurectl storage container help

commands:
    create
        create container with the specified name
    delete
        delete container with the specified name
    help
        show manual page for container command
    list
        list container names for configured account
    sas
        generate a shared access signature URL allowing limited access to the
        specified container without an access key
    show
        show container content for configured account and container

options:
    --expiry-datetime=<expiry>
        Date (and optionally time) to cease access via a shared access
        signature. [default: 30 days from start]
        Example format: YYYY-MM-DDThh:mm:ssZ
    --name=<name>
        name of the container
    --permissions=<permissions>
        String of permitted actions on a storage element via shared access
        signature.
        r  Read
        w  Write
        d  Delete
        l  List
        [default: rl]
    --start-datetime=<start>
        Date (and optionally time) to grant access via a shared access
        signature. [default: now]
        Example format: YYYY-MM-DDThh:mm:ssZ
"""
import datetime

# project
from .base import CliTask
from azurectl.account.service import AzureAccount
from azurectl.utils.collector import DataCollector
from azurectl.utils.output import DataOutput
from azurectl.logger import log
from azurectl.storage.container import Container
from azurectl.help import Help


class StorageContainerTask(CliTask):
    """
        Process container commands
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

        # default to 1 minute ago (skew around 'now')
        if self.command_args['--start-datetime'] == 'now':
            start = datetime.datetime.utcnow() - datetime.timedelta(minutes=1)
        else:
            start = self.validate_date('--start-datetime')

        # default to 30 days from now
        if self.command_args['--expiry-datetime'] == '30 days from start':
            expiry = start + datetime.timedelta(days=30)
        else:
            expiry = self.validate_date('--expiry-datetime')

        self.validate_sas_permissions('--permissions')

        self.container = Container(self.account)

        if self.command_args['list']:
            self.__container_list()
        elif self.command_args['show']:
            self.__container_content()
        elif self.command_args['create']:
            self.__container_create()
        elif self.command_args['delete']:
            self.__container_delete()
        elif self.command_args['sas']:
            self.__container_sas(
                start, expiry, self.command_args['--permissions']
            )

    def __help(self):
        if self.command_args['help']:
            self.manual.show('azurectl::storage::container')
        else:
            return False
        return self.manual

    def __container_sas(self, start, expiry, permissions):
        if self.command_args['--name']:
            container_name = self.command_args['--name']
        else:
            container_name = self.account.storage_container()
        self.result.add(
            self.account.storage_name() + ':container_sas_url',
            self.container.sas(container_name, start, expiry, permissions)
        )
        self.out.display()

    def __container_content(self):
        container_name = self.command_args['--name']
        self.result.add(
            self.account.storage_name() + ':container_content',
            self.container.content(container_name)
        )
        self.out.display()

    def __container_list(self):
        self.result.add(
            self.account.storage_name() + ':containers',
            self.container.list()
        )
        self.out.display()

    def __container_create(self):
        container_name = self.command_args['--name']
        log.info('Request to create container %s', container_name)
        self.container.create(container_name)
        log.info('Created %s container', container_name)

    def __container_delete(self):
        container_name = self.command_args['--name']
        log.info('Request to delete container %s', container_name)
        self.container.delete(container_name)
        log.info('Deleted %s container', container_name)
