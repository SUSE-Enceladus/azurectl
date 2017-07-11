from .test_helper import argv_kiwi_tests

import sys
import mock
from mock import patch
from azurectl.utils.output import DataOutput
from azurectl.instance.endpoint import Endpoint
from azurectl.help import Help
from azurectl.commands.compute_endpoint import ComputeEndpointTask
import azurectl


class TestComputeEndpointTask:
    def setup(self):
        # instantiate the command task
        sys.argv = [
            sys.argv[0], '--config', '../data/config',
            'compute', 'endpoint', 'help'
        ]
        self.task = ComputeEndpointTask()
        self.task.request_wait = mock.Mock()
        # mock out the Endpoint class the commands interface with
        azurectl.commands.compute_endpoint.Endpoint = mock.Mock()
        # mock out the help class
        azurectl.commands.compute_endpoint.Help = mock.Mock()
        # mock out the output class
        azurectl.commands.compute_endpoint.DataOutput = mock.Mock()
        # variables used in multiple tests
        self.cloud_service_name = 'mockcloudservice'
        self.endpoint_name = 'HTTPS'
        self.port = '443'
        self.instance_port = '10000'
        self.instance_name = 'mockcloudserviceinstance1'
        self.udp_endpoint_name = 'SNMP'
        self.udp_port = '161'
        self.idle_timeout = '10'

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def __init_command_args(self, overrides=None):
        '''
            Provide an empty set of command arguments to be customized in tests
        '''
        command_args = {
            'create': False,
            'update': False,
            'delete': False,
            'show': False,
            'list': False,
            'help': False,
            '--cloud-service-name': None,
            '--name': None,
            '--instance-name': None,
            '--port': None,
            '--instance-port': None,
            '--idle-timeout': None,
            '--tcp': False,
            '--udp': False,
            '--wait': True
        }
        if overrides:
            command_args.update(overrides)
        self.task.command_args = command_args

    def test_help(self):
        # given
        self.__init_command_args({
            'help': True
        })
        # when
        self.task.process()
        # then
        self.task.manual.show.assert_called_once_with(
            'azurectl::compute::endpoint'
        )

    def test_create_with_minimal_args(self):
        # given
        self.__init_command_args({
            'create': True,
            '--cloud-service-name': self.cloud_service_name,
            '--name': self.endpoint_name,
            '--port': self.port
        })
        # when
        self.task.process()
        # then
        self.task.endpoint.set_instance.assert_called_once_with(
            self.cloud_service_name,
            self.cloud_service_name
        )
        self.task.endpoint.create.assert_called_once_with(
            self.endpoint_name,
            self.port,
            self.port,
            'tcp',
            '4'
        )

    def test_create_with_instance_name(self):
        # given
        self.__init_command_args({
            'create': True,
            '--cloud-service-name': self.cloud_service_name,
            '--instance-name': self.instance_name,
            '--name': self.endpoint_name,
            '--port': self.port
        })
        # when
        self.task.process()
        # then
        self.task.endpoint.set_instance.assert_called_once_with(
            self.cloud_service_name,
            self.instance_name
        )
        self.task.endpoint.create.assert_called_once_with(
            self.endpoint_name,
            self.port,
            self.port,
            'tcp',
            '4'
        )

    def test_update_with_udp_arg(self):
        # given
        self.__init_command_args({
            'update': True,
            '--cloud-service-name': self.cloud_service_name,
            '--name': self.endpoint_name,
            '--port': self.port,
            '--udp': True
        })
        # when
        self.task.process()
        # then
        self.task.endpoint.set_instance.assert_called_once_with(
            self.cloud_service_name,
            self.cloud_service_name
        )
        self.task.endpoint.update.assert_called_once_with(
            self.endpoint_name,
            self.port,
            self.port,
            'udp',
            None
        )

    def test_update_no_protocol(self):
        # given
        self.__init_command_args({
            'update': True,
            '--cloud-service-name': self.cloud_service_name,
            '--name': self.endpoint_name,
            '--port': self.port
        })
        # when
        self.task.process()
        # then
        self.task.endpoint.set_instance.assert_called_once_with(
            self.cloud_service_name,
            self.cloud_service_name
        )
        self.task.endpoint.update.assert_called_once_with(
            self.endpoint_name,
            self.port,
            self.port,
            None,
            None
        )

    def test_update_endpoint(self):
        # given
        self.__init_command_args({
            'update': True,
            '--cloud-service-name': self.cloud_service_name,
            '--instance-name': self.instance_name,
            '--name': self.endpoint_name,
            '--port': self.port,
            '--idle-timeout': self.idle_timeout,
            '--tcp': True
        })
        # when
        self.task.process()
        # then
        self.task.endpoint.set_instance.assert_called_once_with(
            self.cloud_service_name,
            self.instance_name
        )
        self.task.endpoint.update.assert_called_once_with(
            self.endpoint_name,
            self.port,
            self.port,
            'tcp',
            self.idle_timeout
        )

    def test_create_udp_endpoint(self):
        # given
        self.__init_command_args({
            'create': True,
            '--cloud-service-name': self.cloud_service_name,
            '--name': self.udp_endpoint_name,
            '--port': self.udp_port,
            '--instance-port': self.instance_port,
            '--udp': True
        })
        # when
        self.task.process()
        # then
        self.task.endpoint.set_instance.assert_called_once_with(
            self.cloud_service_name,
            self.cloud_service_name
        )
        self.task.endpoint.create.assert_called_once_with(
            self.udp_endpoint_name,
            self.udp_port,
            self.instance_port,
            'udp',
            '4'
        )

    def test_create_with_timeout(self):
        # given
        self.__init_command_args({
            'create': True,
            '--cloud-service-name': self.cloud_service_name,
            '--name': self.endpoint_name,
            '--port': self.port,
            '--idle-timeout': self.idle_timeout
        })
        # when
        self.task.process()
        # then
        self.task.endpoint.set_instance.assert_called_once_with(
            self.cloud_service_name,
            self.cloud_service_name
        )
        self.task.endpoint.create.assert_called_once_with(
            self.endpoint_name,
            self.port,
            self.port,
            'tcp',
            self.idle_timeout
        )

    def test_show_with_minimal_args(self):
        # given
        self.__init_command_args({
            'show': True,
            '--cloud-service-name': self.cloud_service_name,
            '--name': self.endpoint_name
        })
        # when
        self.task.process()
        # then
        self.task.endpoint.set_instance.assert_called_once_with(
            self.cloud_service_name,
            self.cloud_service_name
        )
        self.task.endpoint.show.assert_called_once_with(self.endpoint_name)

    def test_show_with_instance_name(self):
        # given
        self.__init_command_args({
            'show': True,
            '--cloud-service-name': self.cloud_service_name,
            '--instance-name': self.instance_name,
            '--name': self.endpoint_name
        })
        # when
        self.task.process()
        # then
        self.task.endpoint.set_instance.assert_called_once_with(
            self.cloud_service_name,
            self.instance_name
        )
        self.task.endpoint.show.assert_called_once_with(self.endpoint_name)

    def test_delete_with_minimal_args(self):
        # given
        self.__init_command_args({
            'delete': True,
            '--cloud-service-name': self.cloud_service_name,
            '--name': self.endpoint_name
        })
        # when
        self.task.process()
        # then
        self.task.endpoint.set_instance.assert_called_once_with(
            self.cloud_service_name,
            self.cloud_service_name
        )
        self.task.endpoint.delete.assert_called_once_with(self.endpoint_name)

    def test_delete_with_instance_name(self):
        # given
        self.__init_command_args({
            'delete': True,
            '--cloud-service-name': self.cloud_service_name,
            '--instance-name': self.instance_name,
            '--name': self.endpoint_name
        })
        # when
        self.task.process()
        # then
        self.task.endpoint.set_instance.assert_called_once_with(
            self.cloud_service_name,
            self.instance_name
        )
        self.task.endpoint.delete.assert_called_once_with(self.endpoint_name)

    def test_list_with_minimal_args(self):
        # given
        self.__init_command_args({
            'list': True,
            '--cloud-service-name': self.cloud_service_name
        })
        # when
        self.task.process()
        # then
        self.task.endpoint.set_instance.assert_called_once_with(
            self.cloud_service_name,
            self.cloud_service_name
        )
        assert self.task.endpoint.list.called

    def test_list_with_instance_name(self):
        # given
        self.__init_command_args({
            'list': True,
            '--cloud-service-name': self.cloud_service_name,
            '--instance-name': self.instance_name
        })
        # when
        self.task.process()
        # then
        self.task.endpoint.set_instance.assert_called_once_with(
            self.cloud_service_name,
            self.instance_name
        )
        assert self.task.endpoint.list.called
