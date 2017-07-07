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
usage: azurectl -h | --help
       azurectl [--output-format=<format>]
                [--output-style=<style>]
                [--debug]
           setup <command> [<args>...]
       azurectl [--config=<file> | --account=<name>]
                [--region=<name>]
                [--storage-account=<name>]
                [--storage-container=<name>]
                [--output-format=<format>]
                [--output-style=<style>]
                [--debug]
           compute <command> [<args>...]
        azurectl [--config=<file> | --account=<name>]
                [--region=<name>]
                [--storage-account=<name>]
                [--storage-container=<name>]
                [--output-format=<format>]
                [--output-style=<style>]
                [--debug]
          storage <command> [<args>...]
       azurectl -v | --version
       azurectl help

global options:
    --output-format=<format>
        output formats, supported are: json
    --output-style=<style>
        output styles, supported are: standard, color
    --debug
        increases message verbosity
    -v --version
        show program version
    help
        show manual page

global options for services: compute, storage
    --account=<name>
        account name. The given name value is used to select the configuration
        file of the form <name>.config from the configuration location
        ~/.config/azurectl.
    --config=<file>
        config file, default is: ~/.config/azurectl/config
    --region=<name>
        region name in config file, default is default_region
        from config file DEFAULT section
    --storage-account=<name>
        storage account name to use for operations. This will
        take precedence over the configured default_storage_account
        from the config file
    --storage-container=<name>
        storage container name to use for operations. This will
        take precedence over the configured default_storage_container
        from the config file
"""
import importlib
from docopt import docopt
import glob
import re
import os

# project
from .defaults import Defaults
from .azurectl_exceptions import (
    AzureUnknownServiceName,
    AzureCommandNotLoaded,
    AzureLoadCommandUndefined
)
from .version import __VERSION__


class Cli(object):
    """
        Commandline interface, global, servicename and command
        specific option handling
    """

    def __init__(self):
        self.all_args = docopt(
            __doc__,
            version='azurectl version ' + __VERSION__,
            options_first=True
        )
        self.loaded = False
        self.command_args = self.all_args['<args>']

    def show_help(self):
        return self.all_args['help']

    def get_servicename(self):
        if self.all_args['compute']:
            return 'compute'
        elif self.all_args['setup']:
            return 'setup'
        elif (self.all_args['storage'] and not self.all_args['compute']):
            return 'storage'
        else:
            raise AzureUnknownServiceName(
                'Unknown/Invalid Servicename'
            )

    def get_command(self):
        return self.all_args['<command>']

    def get_command_args(self):
        if not self.loaded:
            raise AzureCommandNotLoaded(
                '%s command not loaded' % self.get_command()
            )
        return self.__load_command_args()

    def get_global_args(self):
        result = {}
        for arg, value in self.all_args.items():
            if not arg == '<command>' and not arg == '<args>':
                result[arg] = value
        return result

    def load_command(self):
        if self.loaded:
            return self.loaded
        command = self.get_command()
        service = self.get_servicename()
        if not command:
            raise AzureLoadCommandUndefined(
                'No command specified for %s service' % service
            )
        command_source_file = Defaults.project_file(
            'commands/' + service + '_' + command + '.py'
        )
        if not os.path.exists(command_source_file):
            prefix = 'usage:'
            for service_command in self.__get_command_implementations(service):
                print('%s azurectl %s' % (prefix, service_command))
                prefix = '      '
            raise SystemExit
        self.loaded = importlib.import_module(
            'azurectl.commands.' + service + '_' + command
        )
        return self.loaded

    def __get_command_implementations(self, service):
        command_implementations = []
        glob_match = Defaults.project_file('/') + 'commands/*.py'
        for source_file in glob.iglob(glob_match):
            with open(source_file, 'r') as source:
                for line in source:
                    if re.search('usage: (.*)', line):
                        command_path = os.path.basename(
                            source_file
                        ).replace('.py', '').split('_')
                        if command_path[0] == service:
                            command_implementations.append(
                                ' '.join(command_path)
                            )
                        break
        return command_implementations

    def __load_command_args(self):
        argv = [self.get_servicename(), self.get_command()] + self.command_args
        return docopt(self.loaded.__doc__, argv=argv)
