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
from configparser import ConfigParser
import os

# project
from azurectl.config.parser import Config
from azurectl.azurectl_exceptions import (
    AzureConfigParseError,
    AzureConfigAddAccountSectionError,
    AzureConfigAddRegionSectionError,
    AzureConfigPublishSettingsError,
    AzureConfigWriteError
)
from azurectl.logger import log


class AccountSetup(object):
    """
        Implements setup methods to configure, list, add and delete
        account configurations in the configuration file
    """
    def __init__(self, filename):
        self.config = ConfigParser()
        self.filename = filename
        try:
            if os.path.isfile(filename):
                self.config.read(filename)
        except Exception as e:
            raise AzureConfigParseError(
                'Could not parse config file: %s: %s' %
                (filename, format(e))
            )

    def list(self):
        """
            list account sections
        """
        accounts = {}
        accounts['account_region_map'] = {
            'account': self.__get_default_account() or '<missing>',
            'region': self.__get_default_region() or '<missing>'
        }
        accounts['accounts'] = {}
        accounts['regions'] = {}
        for section in self.config.sections():
            options = {}
            for option in self.config.options(section):
                if option == 'default_account' or option == 'default_region':
                    continue
                options[option] = self.config.get(
                    section, option
                )
            if section.startswith('region:'):
                accounts['regions'][section] = options
            else:
                accounts['accounts'][section] = options
        return accounts

    def remove(self):
        """
            remove account configuration file
        """
        default_config_file = Config.get_config_file()
        os.remove(self.filename)
        if default_config_file and os.path.islink(default_config_file):
            link_target = os.readlink(default_config_file)
            if not os.path.exists(link_target):
                # account configuration was also configured as default account
                # remove the now broken default config symlink too
                os.remove(default_config_file)

    def remove_account(self, name):
        """
            remove specified account section
        """
        name = 'account:' + name
        if name == self.__get_default_account():
            log.info('Section %s is the default account section', name)
            log.info('Please setup a new default prior to removing')
            return False
        if not self.config.remove_section(name):
            log.info('Section %s does not exist', name)
            return False
        return True

    def remove_region(self, name):
        """
            remove specified region section
        """
        name = 'region:' + name
        if name == self.__get_default_region():
            log.info('Section %s is the default region section', name)
            log.info('Please setup a new default prior to removing')
            return False
        if not self.config.remove_section(name):
            log.info('Section %s does not exist', name)
            return False
        return True

    def configure_account(
        self,
        account_name,
        publish_settings=None,
        region_name=None,
        default_storage_account=None,
        default_storage_container=None,
        subscription_id=None,
        management_pem_file=None,
        management_url=None
    ):
        if publish_settings:
            self.add_account_with_publishsettings(
                account_name, publish_settings, subscription_id
            )
        elif management_pem_file and management_url and subscription_id:
            self.add_account_with_management_cert(
                account_name,
                management_pem_file,
                management_url,
                subscription_id
            )
        if region_name:
            self.add_region(
                region_name,
                default_storage_account,
                default_storage_container
            )

    def add_account_with_management_cert(
        self,
        section_name,
        management_pem_file,
        management_url,
        subscription_id
    ):
        """
            add new account section
        """
        section_name = 'account:' + section_name
        try:
            self.config.add_section(section_name)
        except Exception as e:
            raise AzureConfigAddAccountSectionError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        self.config.set(
            section_name, 'management_pem_file', management_pem_file
        )
        self.config.set(
            section_name, 'management_url', management_url
        )
        self.config.set(
            section_name, 'subscription_id', subscription_id
        )
        defaults = self.config.defaults()
        if 'default_account' not in defaults:
            defaults['default_account'] = section_name

    def add_account_with_publishsettings(
        self,
        section_name,
        publish_settings,
        subscription_id=None
    ):
        """
            add new account section
        """
        section_name = 'account:' + section_name
        self.__validate_publish_settings_file(
            publish_settings
        )
        try:
            self.config.add_section(section_name)
        except Exception as e:
            raise AzureConfigAddAccountSectionError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        self.config.set(
            section_name, 'publishsettings', publish_settings
        )
        if subscription_id:
            self.config.set(
                section_name, 'subscription_id', subscription_id
            )
        defaults = self.config.defaults()
        if 'default_account' not in defaults:
            defaults['default_account'] = section_name

    def add_region(
        self,
        section_name,
        default_storage_account,
        default_storage_container
    ):
        """
            add new region section
        """
        section_name = 'region:' + section_name
        try:
            self.config.add_section(section_name)
        except Exception as e:
            raise AzureConfigAddRegionSectionError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        self.config.set(
            section_name, 'default_storage_account', default_storage_account
        )
        self.config.set(
            section_name, 'default_storage_container', default_storage_container
        )
        defaults = self.config.defaults()
        if 'default_region' not in defaults:
            defaults['default_region'] = section_name

    def set_default_account(self, section_name):
        section_name = 'account:' + section_name
        if section_name not in self.config.sections():
            log.info('Section %s does not exist', section_name)
            return False
        self.config.defaults()['default_account'] = section_name
        return True

    def set_default_region(self, section_name):
        section_name = 'region:' + section_name
        if section_name not in self.config.sections():
            log.info('Section %s does not exist', section_name)
            return False
        self.config.defaults()['default_region'] = section_name
        return True

    def write(self):
        """
            write out config data to file
        """
        try:
            config_dir = os.path.dirname(self.filename)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            config_handle = open(self.filename, 'w')
            self.config.write(config_handle)
            config_handle.close()
        except Exception as e:
            raise AzureConfigWriteError(
                'Could not write config file: %s: %s' %
                (type(e).__name__, format(e))
            )

    def __get_default_account(self):
        defaults = self.config.defaults()
        if 'default_account' in defaults:
            return defaults['default_account']

    def __get_default_region(self):
        defaults = self.config.defaults()
        if 'default_region' in defaults:
            return defaults['default_region']

    def __validate_publish_settings_file(self, filename):
        """
            validate given publish settings file for
            + existence
        """
        if not os.path.isfile(filename):
            raise AzureConfigPublishSettingsError(
                'No such Publish Settings file: %s' % filename
            )
