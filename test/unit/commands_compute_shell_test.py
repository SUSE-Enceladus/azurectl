from .test_helper import argv_kiwi_tests

import sys
import mock
from collections import namedtuple
from mock import patch
import azurectl
from azurectl.account.service import AzureAccount
from azurectl.commands.compute_shell import ComputeShellTask
from azurectl.config.parser import Config


class TestComputeShellTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], '--config', '../data/config',
            'compute', 'shell'
        ]

        account = AzureAccount(
            Config(
                region_name='East US 2', filename='../data/config'
            )
        )
        account.get_management_service = mock.Mock()
        account.get_blob_service_host_base = mock.Mock(
            return_value='.blob.test.url'
        )
        account.storage_key = mock.Mock()

        azurectl.commands.compute_shell.AzureAccount = mock.Mock(
            return_value=account
        )

        self.task = ComputeShellTask()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    @patch('azurectl.commands.compute_shell.code.interact')
    def test_process_compute_shell(self, mock_interact):
        self.task.command_args = {}
        self.task.process()
        assert mock_interact.called
