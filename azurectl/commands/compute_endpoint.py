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
An endpoint describes a rule forwarding either TCP or UDP traffic from a public
port on a cloud service to a private port on a virtual machine instance.
Endpoints are identified by a user-defined name.

usage: azurectl compute endpoint -h | --help
       azurectl compute endpoint create --cloud-service-name=<name> --name=<name> --port=<port>
           [--instance-name=<name>]
           [--instance-port=<port>]
           [--idle-timeout=<minutes>]
           [--udp]
           [--wait]
       azurectl compute endpoint list --cloud-service-name=<name>
           [--instance-name=<name>]
       azurectl compute endpoint show --cloud-service-name=<name> --name=<name>
           [--instance-name=<name>]
       azurectl compute endpoint update --cloud-service-name=<name> --name=<name>
           [--instance-name=<name>]
           [--port=<port>]
           [--instance-port=<port>]
           [--idle-timeout=<minutes>]
           [--udp | --tcp]
           [--wait]
       azurectl compute endpoint delete --cloud-service-name=<name> --name=<name>
           [--instance-name=<name>]
           [--wait]
       azurectl compute endpoint help

commands:
    create
        add a new endpoint
    delete
        remove an endpoint
    list
        list ports on the selected VM instance that are forwarded through its
        cloud service (endpoints)
    show
        list information about a single endpoint
    update
        update an existing endpoint

options:
    --cloud-service-name=<name>
        name of the cloud service where the virtual machine may be found
    --idle-timeout=<minutes>
        specifies the timeout for the TCP idle connection. The value can be set
        between 4 and 30 minutes. The default value is 4 minutes. Does not apply
        to UDP connections
    --instance-name=<name>
        name of the virtual machine instance. If no name is given the
        instance name is assumed to be the same as the cloud service name
    --instance-port=<port>
        port on the virtual machine to forward to the port on the
        cloud service. If no port is given, the instance port is assumed to be
        the same as the cloud service port
    --name=<name>
        name of the endpoint, usually the name of the protocol that is carried
    --port=<port>
        port to open on the cloud service
    --tcp
        select TCP as the transport protocol for the endpoint. (update only)
    --udp
        select UDP as the transport protocol for the endpoint. If not specified,
        the default transport protocol is TCP
    --wait
        wait for the request to succeed
"""
# project
from .base import CliTask
from azurectl.account.service import AzureAccount
from azurectl.utils.collector import DataCollector
from azurectl.utils.output import DataOutput
from azurectl.instance.endpoint import Endpoint
from azurectl.help import Help


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
        if self.command_args['update']:
            self.__update()
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
        request_id = self.endpoint.create(
            self.command_args['--name'],
            self.command_args['--port'],
            (
                self.command_args['--instance-port'] or
                self.command_args['--port']
            ),
            ('udp' if self.command_args['--udp'] else 'tcp'),
            (self.command_args['--idle-timeout'] or '4')
        )
        if self.command_args['--wait']:
            self.request_wait(request_id)
        self.result.add(
            'endpoint:' + self.command_args['--name'], request_id
        )
        self.out.display()

    def __update(self):
        if self.command_args['--udp']:
            protocol = 'udp'
        elif self.command_args['--tcp']:
            protocol = 'tcp'
        else:
            protocol = None

        request_id = self.endpoint.update(
            self.command_args['--name'],
            self.command_args['--port'],
            (
                self.command_args['--instance-port'] or
                self.command_args['--port']
            ),
            protocol,
            self.command_args['--idle-timeout']
        )
        if self.command_args['--wait']:
            self.request_wait(request_id)
        self.result.add(
            'endpoint:' + self.command_args['--name'], request_id
        )
        self.out.display()

    def __delete(self):
        request_id = self.endpoint.delete(
            self.command_args['--name'],
        )
        if self.command_args['--wait']:
            self.request_wait(request_id)
        self.result.add(
            'endpoint:' + self.command_args['--name'], request_id
        )
        self.out.display()
