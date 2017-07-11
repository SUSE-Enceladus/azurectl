from .test_helper import argv_kiwi_tests

import dateutil.parser
import sys
import mock
from mock import patch
import azurectl
from azurectl.commands.storage_share import StorageShareTask


class TestStorageShareTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], '--config', '../data/config',
            'storage', 'share', 'list'
        ]
        azurectl.commands.storage_share.AzureAccount.storage_names = mock.Mock(
            return_value=mock.Mock()
        )
        self.storage = mock.Mock()
        self.storage.upload = mock.Mock()
        azurectl.commands.storage_share.FileShare = mock.Mock(
            return_value=mock.Mock()
        )
        azurectl.commands.storage_share.Help = mock.Mock(
            return_value=mock.Mock()
        )
        self.task = StorageShareTask()
        self.__init_command_args()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def __init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['share'] = False
        self.task.command_args['create'] = False
        self.task.command_args['delete'] = False
        self.task.command_args['list'] = False
        self.task.command_args['--color'] = False
        self.task.command_args['--name'] = 'some-name'
        self.task.command_args['help'] = False

    @patch('azurectl.commands.storage_share.DataOutput')
    def test_process_storage_share_list(self, mock_out):
        self.__init_command_args()
        self.task.command_args['share'] = True
        self.task.command_args['list'] = True
        self.task.process()
        self.task.fileshare.list.assert_called_once_with()

    def test_process_storage_share_delete(self):
        self.__init_command_args()
        self.task.command_args['share'] = True
        self.task.command_args['delete'] = True
        self.task.process()
        self.task.fileshare.delete.assert_called_once_with(
            self.task.command_args['--name']
        )

    def test_process_storage_share_create(self):
        self.__init_command_args()
        self.task.command_args['share'] = True
        self.task.command_args['create'] = True
        self.task.process()
        self.task.fileshare.create.assert_called_once_with(
            self.task.command_args['--name']
        )

    def test_process_storage_share_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['share'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'azurectl::storage::share'
        )
