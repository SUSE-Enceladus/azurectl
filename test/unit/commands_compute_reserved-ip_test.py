from .test_helper import argv_kiwi_tests

import sys
import mock
from mock import patch
import azurectl
import importlib


class TestComputeReservedIpTask:
    def setup(self):
        reserverd_ip = importlib.import_module(
            'azurectl.commands.compute_reserved-ip'
        )
        sys.argv = [
            sys.argv[0], '--config', '../data/config',
            'compute', 'reserved-ip', 'list'
        ]
        self.task = reserverd_ip.ComputeReservedIpTask()
        self.task.request_wait = mock.Mock()
        reserverd_ip.ReservedIp = mock.Mock(
            return_value=mock.Mock()
        )
        reserverd_ip.Help = mock.Mock(
            return_value=mock.Mock()
        )

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def __init_command_args(self):
        self.task.command_args = {
            'list': False,
            'show': False,
            'create': False,
            'delete': False,
            'associate': False,
            'disassociate': False,
            'help': False,
            '--name': None,
            '--cloud-service-name': None,
            '--wait': True
        }

    def test_process_compute_reserved_ip_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'azurectl::compute::reserved_ip'
        )

    @patch('azurectl.commands.compute_reserved-ip.DataOutput')
    def test_process_compute_reserved_ip_list(self, mock_out):
        self.__init_command_args()
        self.task.command_args['list'] = True
        self.task.process()
        self.task.reserved_ip.list.assert_called_once_with()

    @patch('azurectl.commands.compute_reserved-ip.DataOutput')
    def test_process_compute_reserved_ip_show(self, mock_out):
        self.__init_command_args()
        self.task.command_args['show'] = True
        self.task.command_args['--name'] = 'test'
        self.task.process()
        self.task.reserved_ip.show.assert_called_once_with(
            self.task.command_args['--name']
        )

    @patch('azurectl.commands.compute_reserved-ip.DataOutput')
    def test_process_compute_reserved_ip_create(self, mock_out):
        self.__init_command_args()
        self.task.command_args['create'] = True
        self.task.command_args['--name'] = 'test'
        self.task.process()
        self.task.reserved_ip.create.assert_called_once_with(
            self.task.command_args['--name'],
            self.task.config.get_region_name()
        )

    @patch('azurectl.commands.compute_reserved-ip.DataOutput')
    def test_process_compute_reserved_ip_delete(self, mock_out):
        self.__init_command_args()
        self.task.command_args['delete'] = True
        self.task.command_args['--name'] = 'test'
        self.task.process()
        self.task.reserved_ip.delete.assert_called_once_with(
            self.task.command_args['--name']
        )

    @patch('azurectl.commands.compute_reserved-ip.DataOutput')
    def test_process_compute_reserved_ip_associate(self, mock_out):
        self.__init_command_args()
        self.task.command_args['associate'] = True
        self.task.command_args['--name'] = 'test'
        self.task.command_args['--cloud-service-name'] = 'some-cloud-service'
        self.task.process()
        self.task.reserved_ip.associate.assert_called_once_with(
            'test', 'some-cloud-service'
        )

    @patch('azurectl.commands.compute_reserved-ip.DataOutput')
    def test_process_compute_reserved_ip_disassociate(self, mock_out):
        self.__init_command_args()
        self.task.command_args['disassociate'] = True
        self.task.command_args['--name'] = 'test'
        self.task.command_args['--cloud-service-name'] = 'some-cloud-service'
        self.task.process()
        self.task.reserved_ip.disassociate.assert_called_once_with(
            'test', 'some-cloud-service'
        )
