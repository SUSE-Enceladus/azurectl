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
usage: azurectl compute endpoint -h | --help
       azurectl compute endpoint list --cloud-service-name=<name>
           [--instance-name=<name>]
       azurectl compute endpoint show --cloud-service-name=<name> --name=<name>
           [--instance-name=<name>]
       azurectl compute endpoint create --cloud-service-name=<name> --name=<name> --port=<port>
           [--instance-name=<name>]
           [--instance-port=<port>]
           [--idle-timeout=<minutes>]
           [--udp]
       azurectl compute endpoint delete --cloud-service-name=<name> --name=<name>
       azurectl compute endpoint help

commands:
    list
        list ports on the selected VM instance that are forwarded through its
        cloud service (endpoints)
    show
        list information about a single endpoint
    create
        add a new endpoint
    delete
        remove an endpoint

options:
    --cloud-service-name=<name>
        name of the cloud service where the virtual machine may be found
    --instance-name=<name>
        name of the virtual machine instance. If no name is given the
        instance name is assumed to be the same as the cloud service name
    --name=<name>
        name of the endpoint, usually the name of the protocol that is carried
    --port=<port>
        port to open on the cloud service
    --instance-port=<port>
        port on the virtual machine to forward to the port on the
        cloud service. If no port is given, the instance port is assumed to be
        the same as the cloud service port
    --idle-timeout=<minutes>
        specifies the timeout for the TCP idle connection. The value can be set
        between 4 and 30 minutes. The default value is 4 minutes. Does not apply
        to UDP connections
    --udp
        select UDP as the transport protocol for the endpoint. If not specified,
        the default transport protocol is TCP
"""
# project
from cli_task import CliTask
from azure_account import AzureAccount
from data_collector import DataCollector
from data_output import DataOutput
from endpoint import Endpoint
from help import Help


class ComputeEndpointTask(CliTask):
    """
        Process image commands
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
        self.endpoint = Endpoint(self.account)
        self.endpoint.set_instance(
            self.command_args['--cloud-service-name'],
            (
                self.command_args['--instance-name'] or
                self.command_args['--cloud-service-name']
            )
        )

        if self.command_args['list']:
            self.__list()
        if self.command_args['show']:
            self.__show()
        if self.command_args['create']:
            self.__create()
        if self.command_args['delete']:
            self.__delete()

    def __help(self):
        if self.command_args['help']:
            self.manual.show('azurectl::compute::endpoint')
        else:
            return False
        return self.manual

    def __list(self):
        self.result.add('endpoints', self.endpoint.list())
        self.out.display()

    def __show(self):
        self.result.add(
            'endpoint',
            self.endpoint.show(self.command_args['--name'])
        )
        self.out.display()

    def __create(self):
        self.result.add(
            'endpoint:' + self.command_args['--name'],
            self.endpoint.create(
                self.command_args['--name'],
                self.command_args['--port'],
                (
                    self.command_args['--instance-port'] or
                    self.command_args['--port']
                ),
                ('udp' if self.command_args['--udp'] else 'tcp'),
                (self.command_args['--idle-timeout'] or '4')
            )
        )
        self.out.display()

    def __delete(self):
        self.result.add(
            'endpoint:' + self.command_args['--name'],
            self.endpoint.delete(
                self.command_args['--name'],
            )
        )
        self.out.display()
