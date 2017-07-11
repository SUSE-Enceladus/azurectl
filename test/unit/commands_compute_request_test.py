from .test_helper import argv_kiwi_tests

import sys
import mock
from mock import patch
import azurectl
from azurectl.commands.compute_request import ComputeRequestTask


class TestComputeRequestTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], '--config', '../data/config',
            'compute', 'request', 'status', '--id', '1234'
        ]
        self.task = ComputeRequestTask()
        azurectl.commands.compute_request.RequestResult = mock.Mock(
            return_value=mock.Mock()
        )
        azurectl.commands.compute_request.Help = mock.Mock(
            return_value=mock.Mock()
        )
        azurectl.commands.compute_request.AzureAccount = mock.Mock(
            return_value=mock.Mock()
        )
        self.__init_command_args()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def __init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['status'] = False
        self.task.command_args['wait'] = False
        self.task.command_args['--id'] = '1234'
        self.task.command_args['help'] = False

    def test_process_compute_request_wait(self):
        self.__init_command_args()
        self.task.command_args['wait'] = True
        self.task.request_wait = mock.Mock()
        self.task.process()
        self.task.request_wait.assert_called_once_with(
            self.task.command_args['--id']
        )

    @patch('azurectl.commands.compute_request.DataOutput')
    def test_process_compute_request_status(self, mock_out):
        self.__init_command_args()
        self.task.command_args['status'] = True
        self.task.request_status = mock.Mock()
        self.task.process()
        self.task.request_status.assert_called_once_with(
            self.task.command_args['--id']
        )

    def test_process_compute_request_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'azurectl::compute::request'
        )
