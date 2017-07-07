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
from textwrap import dedent
import os
import sys


# project
from azurectl.azurectl_exceptions import (
    AzureConfigAccountNotFound,
    AzureConfigRegionNotFound,
    AzureAccountDefaultSectionNotFound,
    AzureAccountLoadFailed,
    AzureConfigVariableNotFound,
    AzureConfigSectionNotFound,
    AzureConfigParseError,
    AzureConfigAccountFileNotFound,
    AzureConfigDefaultLinkError
)
from azurectl.config.file_path import ConfigFilePath


class Config(object):
    """
        Reading of config file attributes. Any instance holds state
        information about Azure account, region, storage and container
        references
    """
    PLATFORM = sys.platform[:3]

    def __init__(
        self,
        account_name=None,
        region_name=None,
        storage_account_name=None,
        storage_container_name=None,
        filename=None,
        platform=PLATFORM
    ):
        from azurectl.logger import log

        self.storage_container_name = storage_container_name
        self.storage_account_name = storage_account_name

        self.config_file = self.__lookup_config_file(
            platform, account_name, filename
        )

        self.config = ConfigParser()
        try:
            log.debug('Using configuration from %s', self.config_file)
            self.config.read(self.config_file)
        except Exception as e:
            raise AzureConfigParseError(
                'Could not parse config file: "%s"\n%s' %
                (self.config_file, e.message)
            )

        if not self.config.defaults():
            raise AzureAccountDefaultSectionNotFound(
                'Empty or undefined default section in configuration file %s' %
                self.config_file
            )

        self.account_name = self.__import_default_account()
        self.selected_region_name = region_name
        self.region_name = None

    def get_storage_account_name(self):
        storage_account_name = self.storage_account_name
        if not storage_account_name:
            storage_account_name = self.__get_region_option(
                'default_storage_account'
            )
        return storage_account_name

    def get_storage_container_name(self):
        storage_container_name = self.storage_container_name
        if not storage_container_name:
            storage_container_name = self.__get_region_option(
                'default_storage_container'
            )
        return storage_container_name

    def get_subscription_id(self):
        return self.__get_account_option('subscription_id')

    def get_publishsettings_file_name(self):
        return self.__get_account_option('publishsettings')

    def get_management_url(self):
        return self.__get_account_option('management_url')

    def get_management_pem_filename(self):
        return self.__get_account_option('management_pem_file')

    def get_region_name(self):
        if not self.region_name:
            try:
                self.region_name = self.__import_default_region(
                    self.selected_region_name
                ).replace('region:', '')
            except AzureConfigSectionNotFound:
                self.region_name = self.selected_region_name
        return self.region_name

    def get_account_name(self):
        return self.account_name.replace('account:', '')

    @classmethod
    def get_config_file(self, account_name=None, filename=None, platform=None):
        paths = ConfigFilePath(account_name, platform)
        if filename:
            return filename
        elif account_name:
            return paths.default_new_account_config()
        else:
            return paths.default_config()

    @classmethod
    def get_config_file_list(self):
        paths = ConfigFilePath()
        return [
            paths.default_config()
        ] + paths.account_config()

    @classmethod
    def set_default_config_file(self, account_name, platform=None):
        paths = ConfigFilePath(account_name, platform)
        account_config_file = paths.default_new_account_config()
        if not os.path.exists(account_config_file):
            raise AzureConfigAccountFileNotFound(
                'Account config file %s not found' % account_config_file
            )

        default_config_file = paths.default_config()
        if not default_config_file:
            default_config_file = paths.default_new_config()

        default_exists = os.path.exists(default_config_file)
        default_islink = os.path.islink(default_config_file)

        if default_exists and not default_islink:
            message = dedent('''
                Can not link %s as default account.

                A default account configuration file from a former
                azurectl version was found. Consider one of the following
                options to handle the config file: %s

                1. Delete the configuration file if no longer needed
                2. Move the configuration file with context information to
                   ~/.config/azurectl/config.<context>
            ''').strip()
            raise AzureConfigDefaultLinkError(
                message % (account_config_file, default_config_file)
            )

        if default_exists:
            os.remove(default_config_file)

        os.symlink(account_config_file, default_config_file)

    def __check_for_section(self, section):
        if section and not self.config.has_section(section):
            raise AzureConfigSectionNotFound(
                'Section %s not found in configuration file %s' %
                (section, self.config_file)
            )

    def __get_account_option(self, option):
        try:
            result = self.config.get(self.account_name, option)
        except Exception:
            raise AzureConfigVariableNotFound(
                '%s not defined for account %s in configuration file %s' %
                (option, self.account_name, self.config_file)
            )
        return result

    def __get_region_option(self, option):
        try:
            if not self.region_name:
                self.get_region_name()
            result = self.config.get('region:' + self.region_name, option)
        except Exception as e:
            message = '%s not found: %s' % (option, format(e))
            raise AzureConfigVariableNotFound(
                message
            )
        return result

    def __lookup_config_file(self, platform, account_name, filename):
        paths = ConfigFilePath(account_name, platform)
        if filename:
            # lookup a custom config file
            if not os.path.isfile(filename):
                raise AzureAccountLoadFailed(
                    'Could not find config file: %s' % filename
                )
        elif account_name:
            # lookup an account config file
            filename = paths.default_new_account_config()
            if not os.path.isfile(filename):
                raise AzureAccountLoadFailed(
                    'Could not find account config file: %s %s: %s' %
                    (
                        paths.account_config_file, 'in home directory',
                        paths.home_path
                    )
                )
        else:
            # lookup default config file
            filename = paths.default_config()
            if not filename:
                raise AzureAccountLoadFailed(
                    'could not find default configuration file %s %s: %s' %
                    (
                        ' or '.join(paths.config_files),
                        'in home directory',
                        paths.home_path
                    )
                )
        return filename

    def __import_default_region(self, region_name):
        defaults = self.config.defaults()
        if region_name:
            region_name = 'region:' + region_name
        else:
            try:
                region_name = defaults['default_region']
            except Exception:
                raise AzureConfigRegionNotFound(
                    'No region referenced in configuration file %s' %
                    self.config_file
                )
        self.__check_for_section(region_name)
        return region_name

    def __import_default_account(self):
        defaults = self.config.defaults()
        try:
            account_name = defaults['default_account']
        except Exception:
            raise AzureConfigAccountNotFound(
                'No account referenced in configuration file %s' %
                self.config_file
            )
        self.__check_for_section(account_name)
        return account_name
