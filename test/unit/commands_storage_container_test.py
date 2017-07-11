from .test_helper import argv_kiwi_tests

import dateutil.parser
import sys
import mock
from mock import patch
import datetime
import azurectl
from pytest import raises
from azurectl.commands.storage_container import StorageContainerTask

from azurectl.azurectl_exceptions import AzureInvalidCommand


class TestStorageContainerTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], '--config', '../data/config',
            'storage', 'container', 'list'
        ]
        azurectl.commands.storage_container.AzureAccount.storage_names = \
        mock.Mock(
            return_value=mock.Mock()
        )
        self.storage = mock.Mock()
        self.storage.upload = mock.Mock()
        azurectl.commands.storage_container.Container = mock.Mock(
            return_value=mock.Mock()
        )
        azurectl.commands.storage_container.Help = mock.Mock(
            return_value=mock.Mock()
        )
        self.task = StorageContainerTask()
        self.__init_command_args()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def __init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['container'] = False
        self.task.command_args['create'] = False
        self.task.command_args['delete'] = False
        self.task.command_args['list'] = False
        self.task.command_args['show'] = False
        self.task.command_args['sas'] = False
        self.task.command_args['--color'] = False
        self.task.command_args['--start-datetime'] = '2015-01-01'
        self.task.command_args['--expiry-datetime'] = '2015-12-31'
        self.task.command_args['--permissions'] = 'rl'
        self.task.command_args['--name'] = 'some-name'
        self.task.command_args['help'] = False

    def test_process_storage_container_delete(self):
        self.__init_command_args()
        self.task.command_args['container'] = True
        self.task.command_args['delete'] = True
        self.task.process()
        self.task.container.delete.assert_called_once_with(
            self.task.command_args['--name']
        )

    def test_process_storage_container_create(self):
        self.__init_command_args()
        self.task.command_args['container'] = True
        self.task.command_args['create'] = True
        self.task.process()
        self.task.container.create.assert_called_once_with(
            self.task.command_args['--name']
        )

    @patch('azurectl.commands.storage_container.DataOutput')
    def test_process_storage_container_show(self, mock_out):
        self.__init_command_args()
        self.task.command_args['container'] = True
        self.task.command_args['show'] = True
        self.task.process()
        self.task.container.content.assert_called_once_with(
            self.task.command_args['--name']
        )

    def test_start_date_validation(self):
        self.__init_command_args()
        self.task.command_args['--start-datetime'] = 'foo'
        with raises(AzureInvalidCommand):
            self.task.process()

    def test_end_date_validation(self):
        self.__init_command_args()
        self.task.command_args['--expiry-datetime'] = 'foo'
        with raises(AzureInvalidCommand):
            self.task.process()

    def test_permissions_validation(self):
        self.__init_command_args()
        self.task.command_args['--permissions'] = 'a'
        with raises(AzureInvalidCommand):
            self.task.process()

    @patch('azurectl.commands.storage_container.DataOutput')
    def test_process_storage_container_sas(self, mock_out):
        self.__init_command_args()
        self.task.command_args['container'] = True
        self.task.command_args['sas'] = True
        self.task.process()
        start = dateutil.parser.parse(
            self.task.command_args['--start-datetime']
        )
        expiry = dateutil.parser.parse(
            self.task.command_args['--expiry-datetime']
        )
        self.task.container.sas.assert_called_once_with(
            self.task.command_args['--name'], start, expiry, 'rl'
        )

    @patch('azurectl.commands.storage_container.DataOutput')
    def test_process_storage_container_sas_default_container(self, mock_out):
        self.__init_command_args()
        self.task.command_args['--name'] = None
        self.task.command_args['container'] = True
        self.task.command_args['sas'] = True
        self.task.process()
        start = dateutil.parser.parse(
            self.task.command_args['--start-datetime']
        )
        expiry = dateutil.parser.parse(
            self.task.command_args['--expiry-datetime']
        )
        self.task.container.sas.assert_called_once_with(
            self.task.account.storage_container(), start, expiry, 'rl'
        )

    @patch('azurectl.commands.storage_container.DataOutput')
    def test_process_storage_container_sas_now(self, mock_out):
        self.__init_command_args()
        self.task.command_args['--start-datetime'] = 'now'
        self.task.command_args['container'] = True
        self.task.command_args['sas'] = True
        self.task.process()
        expiry = dateutil.parser.parse(
            self.task.command_args['--expiry-datetime']
        )
        self.task.container.sas.assert_called_once_with(
            self.task.command_args['--name'], mock.ANY, expiry, 'rl'
        )

    @patch('azurectl.commands.storage_container.DataOutput')
    def test_process_storage_container_sas_expire(self, mock_out):
        self.__init_command_args()
        self.task.command_args['--expiry-datetime'] = '30 days from start'
        self.task.command_args['container'] = True
        self.task.command_args['sas'] = True
        self.task.process()
        start = dateutil.parser.parse(
            self.task.command_args['--start-datetime']
        )
        expiry = start + datetime.timedelta(days=30)
        self.task.container.sas.assert_called_once_with(
            self.task.command_args['--name'], start, expiry, 'rl'
        )

    @patch('azurectl.commands.storage_container.DataOutput')
    def test_process_storage_container_list(self, mock_out):
        self.__init_command_args()
        self.task.command_args['container'] = True
        self.task.command_args['list'] = True
        self.task.process()
        self.task.container.list.assert_called_once_with()

    @patch('azurectl.commands.storage_container.DataOutput')
    def test_process_storage_container_from_cfg_list(self, mock_out):
        self.__init_command_args()
        self.task.command_args['container'] = True
        self.task.command_args['list'] = True
        self.task.process()
        self.task.container.list.assert_called_once_with()

    def test_process_storage_container_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['container'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'azurectl::storage::container'
        )
