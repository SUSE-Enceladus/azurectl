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
       azurectl [--config=<file>]
                [--output-format=<format>]
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
       azurectl -v | --version
       azurectl help

global options:
    --account=<name>
        account template name. The given name is used as config file
        template: ~/.config/azurectl/<name>.config.
    --config=<file>
        config file, default is: ~/.config/azurectl/config
    --output-format=<format>
        output formats, supported are: json
    --output-style=<style>
        output styles, supported are: standard, color
    --region=<name>
        region name in config file, default is default_region
        from config file DEFAULT section
    --storage-account=<name>
        storage account name in config file. The account name must be
        part of the storage_accounts setup of the associated region
        in the configuration file
    --storage-container=<name>
        storage container name in the config file. The container name
        must be part of the storage_containers setup of the associated
        region in the configuration file
    -v --version
        show program version
    help
        show manual page
"""
import importlib
from docopt import docopt

# project
from azurectl_exceptions import (
    AzureUnknownServiceName,
    AzureCommandNotLoaded,
    AzureLoadCommandUndefined,
    AzureUnknownCommand
)
from version import __VERSION__


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
        for arg, value in self.all_args.iteritems():
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
        try:
            loaded = importlib.import_module(
                'azurectl.' + service + '_' + command + '_task'
            )
        except Exception as e:
            raise AzureUnknownCommand(
                'Loading command %s for %s service failed with: %s: %s' %
                (command, service, type(e).__name__, format(e))
            )
        self.loaded = loaded
        return self.loaded

    def __load_command_args(self):
        argv = [self.get_servicename(), self.get_command()] + self.command_args
        return docopt(self.loaded.__doc__, argv=argv)
