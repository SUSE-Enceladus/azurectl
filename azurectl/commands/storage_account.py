# Copyright (c) 2016 SUSE.  All rights reserved.
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
Azure Storage accounts provide access and ownership of all storage-related
services, using a unique set of keys that are distinct from management
authorization methods.

usage: azurectl storage account -h | --help
       azurectl storage account create --name=<accountname>
           [--description=<description>]
           [--label=<label>]
           [--locally-redundant|--zone-redundant|--geo-redundant|--read-access-geo-redundant]
           [--wait]
       azurectl storage account list
       azurectl storage account regions
       azurectl storage account show --name=<accountname>
       azurectl storage account update --name=<accountname>
           [--description=<description>]
           [--label=<label>]
           [--locally-redundant|--zone-redundant|--geo-redundant|--read-access-geo-redundant]
           [--new-primary-key]
           [--new-secondary-key]
           [--wait]
       azurectl storage account delete --name=<accountname>
           [--wait]
       azurectl storage account help

commands:
    create
        add a new storage account
    delete
        destroy an existing storage account and all its containers and stored
        items
        Note: deletion will fail if there are leases on any stored resources
    help
        show manual page for storage account command
    list
        list all storage accounts
    regions
        list regions where a storage account can be created with the current
        subscription
    show
        list all available details for the named storage account
    update
        change the description, label, or backup strategy for an existing
        storage account, or regenerate keys for that account. Attributes not
        included in the the command will not be changed.

options:
    --description=<description>
        A description for the storage account. May be up to 1024 characters in
        length.
    --geo-redundant
        Data is replicated to a secondary region; first data is replicated like
        locally-redundant storage, then replicated again like locally-redunant
        storage in an additonal region. (6 total copies)
        Note: if no backup strategy is selected, this is the default.
    --label=<label>
        A user-friendly version of 'name'. The label may be up to 100 characters
        in length.
    --locally-redundant
        Data is replicated three times, but only within the region where your
        storage account resides. (3 total copies)
    --name=<accountname>
        Name of the storage account to access/create. Must be between 3 and 24
        characters in length, consisting of only numbers and lowercase letters.
    --new-primary-key
        Generate a new primary key for storage access, disabling access through
        the existing primary key.
    --new-secondary-key
        Generate a new secondary key for storage access, disabling access
        through the existing secondary key.
    --zone-redundant
        Data is replicated across two or three facilities in one or two regions,
        but is only available for block blobs; no other storage types will
        be available on an account, and you cannot change from zone-redundant to
        another backup strategy. (3 total copies)
    --read-access-geo-redundant
        Like geo-redundant storage, except that in the event of an outage in
        your primary storage region, data may be read from the backup region.
        (6 total copies)
    --wait
        wait for the request to succeed
"""
import string

# project
from .base import CliTask
from azurectl.account.service import AzureAccount
from azurectl.utils.collector import DataCollector
from azurectl.utils.output import DataOutput
from azurectl.defaults import Defaults
from azurectl.azurectl_exceptions import AzureInvalidCommand
from azurectl.storage.account import StorageAccount
from azurectl.help import Help


class StorageAccountTask(CliTask):
    """
        Process commands on storage accounts
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
        self.storage_account = StorageAccount(self.account)

        if self.command_args['--name']:
            self.validate_account_name()
        if self.command_args['--description']:
            self.validate_description()
        if self.command_args['--label']:
            self.validate_label()

        if self.command_args['create']:
            self.__create()
        elif self.command_args['update']:
            self.__update()
        elif self.command_args['show']:
            self.__show()
        elif self.command_args['list']:
            self.__list()
        elif self.command_args['delete']:
            self.__delete()
        elif self.command_args['regions']:
            self.__list_locations()
        self.out.display()

    # argument validation
    def validate_account_name(self, cmd_arg='--name'):
        valid_chars = set(string.ascii_lowercase + string.digits)
        if (set(self.command_args[cmd_arg]) - valid_chars):
            raise AzureInvalidCommand(
                '%s contains invalid characters. ' % cmd_arg +
                'Only lowercase letters and digits are allowed.')
        self.validate_min_length(cmd_arg, 3)
        self.validate_max_length(cmd_arg, 24)

    def validate_description(self, cmd_arg='--description'):
        self.validate_max_length(cmd_arg, 1024)

    def validate_label(self, cmd_arg='--label'):
        self.validate_max_length(cmd_arg, 100)

    # tasks
    def __help(self):
        if self.command_args['help']:
            self.manual.show('azurectl::storage::account')
        else:
            return False
        return self.manual

    def __create(self):
        request_id = self.storage_account.create(
            self.command_args['--name'],
            self.command_args['--description'],
            self.command_args['--label'],
            Defaults.account_type_for_docopts(self.command_args)
        )
        if self.command_args['--wait']:
            self.request_wait(request_id)
        self.result.add(
            'storage_account:' + self.command_args['--name'],
            request_id
        )

    def __update(self):
        request_id = self.storage_account.update(
            self.command_args['--name'],
            self.command_args['--description'],
            self.command_args['--label'],
            Defaults.account_type_for_docopts(self.command_args, False),
            self.command_args['--new-primary-key'],
            self.command_args['--new-secondary-key']
        )
        if self.command_args['--wait']:
            self.request_wait(request_id)
        self.result.add(
            'storage_account:' + self.command_args['--name'],
            request_id
        )

    def __show(self):
        self.result.add(
            'storage_account:' + self.command_args['--name'],
            self.storage_account.show(self.command_args['--name'])
        )

    def __list(self):
        self.result.add('storage_accounts', self.storage_account.list())

    def __delete(self):
        request_id = self.storage_account.delete(
            self.command_args['--name']
        )
        if self.command_args['--wait']:
            self.request_wait(request_id)
        self.result.add(
            'storage_account:' + self.command_args['--name'],
            request_id
        )

    def __list_locations(self):
        self.result.add('regions', self.account.locations('Storage'))
