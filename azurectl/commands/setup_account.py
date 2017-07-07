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
Configuration file setup for azurectl.

usage: azurectl setup account -h | --help
       azurectl setup account configure --name=<account_name> --publish-settings-file=<file>
           [--subscription-id=<subscriptionid>]
           [--region=<region_name> --storage-account-name=<storagename> --container-name=<containername> --create]
       azurectl setup account configure --name=<account_name> --management-pem-file=<file> --management-url=<url> --subscription-id=<subscriptionid>
           [--region=<region_name> --storage-account-name=<storagename> --container-name=<containername> --create]
       azurectl setup account region add --region=<region_name> --storage-account-name=<storagename> --container-name=<containername>
           [--name=<account_name>]
       azurectl setup account list
       azurectl setup account default --name=<account_name>
       azurectl setup account region default --region=<region_name>
           [--name=<account_name>]
       azurectl setup account remove --name=<account_name>
       azurectl setup account region help
       azurectl setup account help

commands:
    configure
        create new account config file
    default
        set the given account as default config
    help
        show manual page for account command
    list
        list configured account and region sections. Also list
        information about default config file
    region add
        add new region section to the config file. If specified
        the given account config file is used, otherwise the default
        config file
    region default
        set new default region in config file. If specified
        the given account config file is used, otherwise the default
        config file
    region help
        show manual page for account region subcommand
    remove
        remove specified account config file

options:
    --container-name=<containername>
        specify default container name used with the storage account
        in the selected region.
    --create
        process storage and container configuration and create the
        storage account and the container in Azure
    --management-pem-file=<file>
        path to the pem file associated with a management certificate enabled on
        this account
    --management-url=<url>
        URL of the management API where this account is available
    --name=<account_name>
        account name used for account config file lookup
    --publish-settings-file=<file>
        path to the Microsoft Azure account publish settings file
    --storage-account-name=<storagename>
        specify default storage account name in the selected region
    --subscription-id=<subscriptionid>
        subscription id, if more than one subscription is included in your
        publish settings file, or if a publish settings file is not used
    --region=<region_name>
        Name of the geographic region in Azure.
"""
import os

# project
from .base import CliTask
from azurectl.logger import log
from azurectl.help import Help
from azurectl.account.setup import AccountSetup
from azurectl.utils.collector import DataCollector
from azurectl.utils.output import DataOutput
from azurectl.config.parser import Config
from azurectl.storage.container import Container
from azurectl.storage.account import StorageAccount
from azurectl.account.service import AzureAccount
from azurectl.defaults import Defaults

from azurectl.azurectl_exceptions import (
    AzureAccountConfigurationError
)


class SetupAccountTask(CliTask):
    """
        Process setup config commands
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

        if self.command_args['list']:
            self.__list()
        elif self.command_args['default'] and not self.command_args['region']:
            self.__default()
        else:
            self.__load_account_setup(
                self.command_args['--name']
            )
            if self.command_args['remove']:
                self.__remove()
            elif self.command_args['configure']:
                self.__configure_account()
            elif self.command_args['region'] and self.command_args['add']:
                self.__region_add()
            elif self.command_args['region'] and self.command_args['default']:
                self.__set_region_default()

    def __help(self):
        if self.command_args['region'] and self.command_args['help']:
            self.manual.show('azurectl::setup::account::region')
        elif self.command_args['help']:
            self.manual.show('azurectl::setup::account')
        else:
            return False
        return self.manual

    def __load_account_setup(self, for_account=None):
        self.setup = AccountSetup(
            Config.get_config_file(account_name=for_account)
        )

    def __default(self):
        Config.set_default_config_file(
            account_name=self.command_args['--name']
        )
        log.info(
            'Account %s has been set as default configuration',
            self.command_args['--name']
        )

    def __check_account_existing_in_default_config(self):
        default_config = None
        try:
            default_config = Config()
        except Exception:
            # ignore exception thrown if no config file exists
            pass
        if default_config:
            account_section_name = 'account:' + self.command_args['--name']
            if default_config.config.has_section(account_section_name):
                raise AzureAccountConfigurationError(
                    'Account %s already configured in file %s' % (
                        self.command_args['--name'],
                        Config.get_config_file()
                    )
                )

    def __configure_account(self):
        self.__check_account_existing_in_default_config()
        self.setup.configure_account(
            self.command_args['--name'],
            self.command_args['--publish-settings-file'],
            self.command_args['--region'],
            self.command_args['--storage-account-name'],
            self.command_args['--container-name'],
            self.command_args['--subscription-id'],
            self.command_args['--management-pem-file'],
            self.command_args['--management-url']
        )
        self.setup.write()
        log.info(
            'Added account %s', self.command_args['--name']
        )
        if self.command_args['--create']:
            self.global_args['--account'] = self.command_args['--name']
            self.load_config()
            self.account = AzureAccount(self.config)
            self.__load_account_setup(
                self.command_args['--name']
            )

            try:
                storage_account_name = \
                    self.command_args['--storage-account-name']
                storage_account = StorageAccount(self.account)
                if not storage_account.exists(storage_account_name):
                    storage_account_request_id = storage_account.create(
                        name=storage_account_name,
                        description=self.command_args['--name'],
                        label=self.command_args['--storage-account-name'],
                        account_type=Defaults.account_type_for_docopts(
                            self.command_args
                        )
                    )
                    self.request_wait(storage_account_request_id)
                    log.info(
                        'Created %s storage account', storage_account_name
                    )
                else:
                    log.info(
                        'Storage account %s already exists',
                        storage_account_name
                    )

                container_name = self.command_args['--container-name']
                container = Container(self.account)
                if not container.exists(container_name):
                    container.create(container_name)
                    log.info(
                        'Created %s container', container_name
                    )
                else:
                    log.info(
                        'Container %s already exists', container_name
                    )
            except Exception as e:
                self.__remove()
                raise AzureAccountConfigurationError(
                    '%s: %s' % (type(e).__name__, format(e))
                )

    def __region_add(self):
        self.setup.add_region(
            self.command_args['--region'],
            self.command_args['--storage-account-name'],
            self.command_args['--container-name']
        )
        self.setup.write()
        log.info('Added region %s', self.command_args['--region'])

    def __set_region_default(self):
        if self.setup.set_default_region(self.command_args['--region']):
            self.setup.write()
            log.info(
                'Region %s is now set as default',
                self.command_args['--region'],
            )

    def __remove(self):
        self.setup.remove()
        log.info('Removed account config file %s', self.setup.filename)

    def __list(self):
        config_files = Config.get_config_file_list()
        default_config_file = config_files[0] or '<missing>'
        if os.path.islink(default_config_file):
            default_config_file = os.readlink(default_config_file)

        self.result.add(
            'default_config_file', default_config_file
        )

        for config_file in config_files:
            if config_file and not os.path.islink(config_file):
                setup = AccountSetup(config_file)
                account_info = setup.list()
                if account_info:
                    self.result.add(config_file, account_info)

        self.out.display()
