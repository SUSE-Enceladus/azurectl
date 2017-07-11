from .test_helper import argv_kiwi_tests

import sys
import mock
from mock import patch
import azurectl
from pytest import raises
from azurectl.commands.storage_account import StorageAccountTask

from azurectl.azurectl_exceptions import AzureInvalidCommand


class TestStorageAccountTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], '--config', '../data/config',
            'storage', 'account', 'list'
        ]
        self.task = StorageAccountTask()
        self.task.request_wait = mock.Mock()
        azurectl.commands.storage_account.StorageAccount = mock.Mock(
            return_value=mock.Mock()
        )
        azurectl.commands.storage_account.AzureAccount = mock.Mock(
            return_value=mock.Mock()
        )
        azurectl.commands.storage_account.Help = mock.Mock(
            return_value=mock.Mock()
        )

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def __init_command_args(self):
        self.task.command_args = {
            'create': False,
            'delete': False,
            'help': False,
            'list': False,
            'show': False,
            'update': False,
            'regions': False,
            '--name': None,
            '--description': None,
            '--label': None,
            '--locally-redundant': None,
            '--zone-redundant': None,
            '--geo-redundant': None,
            '--read-access-geo-redundant': None,
            '--new-primary-key': None,
            '--new-secondary-key': None,
            '--wait': True
        }

    def test_process_storage_account_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'azurectl::storage::account'
        )

    @patch('azurectl.commands.storage_account.DataOutput')
    def test_process_storage_account_list(self, mock_out):
        self.__init_command_args()
        self.task.command_args['list'] = True
        self.task.process()
        self.task.storage_account.list.assert_called_once_with()

    @patch('azurectl.commands.storage_account.DataOutput')
    def test_process_storage_account_show(self, mock_out):
        self.__init_command_args()
        self.task.command_args['show'] = True
        self.task.command_args['--name'] = 'test'
        self.task.process()
        self.task.storage_account.show.assert_called_once_with(
            self.task.command_args['--name']
        )

    @patch('azurectl.commands.storage_account.DataOutput')
    def test_process_storage_account_create(self, mock_out):
        self.__init_command_args()
        self.task.command_args['create'] = True
        self.task.command_args['--name'] = 'testname'
        self.task.command_args['--label'] = 'test-label'
        self.task.command_args['--description'] = 'test-description'
        self.task.command_args['--locally-redundant'] = True
        self.task.process()
        self.task.storage_account.create.assert_called_once_with(
            'testname',
            'test-description',
            'test-label',
            'Standard_LRS'
        )

    @patch('azurectl.commands.storage_account.DataOutput')
    def test_process_storage_account_update(self, mock_out):
        self.__init_command_args()
        self.task.command_args['update'] = True
        self.task.command_args['--name'] = 'testname'
        self.task.command_args['--label'] = 'test-label'
        self.task.command_args['--description'] = 'test-description'
        self.task.command_args['--locally-redundant'] = True
        self.task.process()
        self.task.storage_account.update.assert_called_once_with(
            'testname',
            'test-description',
            'test-label',
            'Standard_LRS',
            None,
            None
        )

    @patch('azurectl.commands.storage_account.DataOutput')
    def test_process_storage_account_delete(self, mock_out):
        self.__init_command_args()
        self.task.command_args['delete'] = True
        self.task.command_args['--name'] = 'test'
        self.task.process()
        self.task.storage_account.delete.assert_called_once_with(
            self.task.command_args['--name']
        )

    def test_storage_account_command_invalid_caps(self):
        self.__init_command_args()
        self.task.command_args['--name'] = 'CAPSAREINVALID'
        with raises(AzureInvalidCommand):
            self.task.validate_account_name()

    def test_storage_account_command_invalid_punctuation(self):
        self.__init_command_args()
        self.task.command_args['--name'] = 'punctuation-is.bad'
        with raises(AzureInvalidCommand):
            self.task.validate_account_name()

    @patch('azurectl.commands.storage_account.DataOutput')
    def test_process_storage_account_regions(self, mock_out):
        self.__init_command_args()
        self.task.command_args['regions'] = True
        self.task.process()
        self.task.account.locations.assert_called_once_with('Storage')
