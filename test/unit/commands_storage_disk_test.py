from .test_helper import argv_kiwi_tests

import datetime
import dateutil.parser
import sys
import mock
from mock import patch
from pytest import raises
import azurectl
from azurectl.commands.storage_disk import StorageDiskTask

from azurectl.azurectl_exceptions import AzureInvalidCommand


class TestStorageDiskTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], '--config', '../data/config',
            '--storage-container', 'foo',
            'storage', 'disk', 'upload',
            '--source', 'blob',
            '--blob-name', 'name'
        ]
        azurectl.commands.storage_disk.AzureAccount.storage_names = mock.Mock(
            return_value=mock.Mock()
        )
        self.storage = mock.Mock()
        self.storage.upload = mock.Mock()
        azurectl.commands.storage_disk.Storage = mock.Mock(
            return_value=self.storage
        )
        azurectl.commands.storage_disk.Help = mock.Mock(
            return_value=mock.Mock()
        )
        self.task = StorageDiskTask()
        self.__init_command_args()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def __init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['disk'] = False
        self.task.command_args['delete'] = False
        self.task.command_args['upload'] = False
        self.task.command_args['sas'] = False
        self.task.command_args['--color'] = False
        self.task.command_args['--source'] = 'some-file'
        self.task.command_args['--max-chunk-size'] = 1024
        self.task.command_args['--quiet'] = False
        self.task.command_args['--blob-name'] = 'some-name'
        self.task.command_args['--start-datetime'] = '2015-01-01'
        self.task.command_args['--expiry-datetime'] = '2015-12-31'
        self.task.command_args['--permissions'] = 'rl'
        self.task.command_args['help'] = False

    @patch('azurectl.commands.storage_disk.BackgroundScheduler')
    def test_process_storage_disk_upload(self, mock_job):
        self.__init_command_args()
        self.task.command_args['disk'] = True
        self.task.command_args['upload'] = True
        self.task.process()
        self.task.storage.upload.assert_called_once_with(
            'some-file', self.task.command_args['--blob-name'], 1024
        )

    @patch('azurectl.commands.storage_disk.BackgroundScheduler')
    def test_process_storage_disk_upload_interrupted(self, mock_job):
        self.__init_command_args()
        self.task.command_args['disk'] = True
        self.task.command_args['upload'] = True
        self.storage.upload.side_effect = KeyboardInterrupt
        with raises(SystemExit):
            self.task.process()

    @patch('azurectl.commands.storage_disk.BackgroundScheduler')
    def test_process_storage_disk_upload_quiet_interrupted(self, mock_job):
        self.__init_command_args()
        self.task.command_args['disk'] = True
        self.task.command_args['upload'] = True
        self.task.command_args['--quiet'] = True
        self.storage.upload.side_effect = KeyboardInterrupt
        with raises(SystemExit):
            self.task.process()

    def test_process_storage_disk_delete(self):
        self.__init_command_args()
        self.task.command_args['disk'] = True
        self.task.command_args['delete'] = True
        self.task.process()
        self.task.storage.delete.assert_called_once_with(
            self.task.command_args['--blob-name']
        )

    def test_with_storage_container_arg(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['--storage-container'] = 'foo'
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'azurectl::storage::disk'
        )

    def test_process_storage_disk_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'azurectl::storage::disk'
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

    @patch('azurectl.commands.storage_disk.DataOutput')
    def test_process_storage_disk_sas(self, mock_out):
        self.__init_command_args()
        self.task.command_args['sas'] = True
        self.task.process()
        start = dateutil.parser.parse(
            self.task.command_args['--start-datetime']
        )
        expiry = dateutil.parser.parse(
            self.task.command_args['--expiry-datetime']
        )
        self.task.storage.disk_image_sas.assert_called_once_with(
            'foo', self.task.command_args['--blob-name'], start, expiry, 'rl'
        )

    @patch('azurectl.commands.storage_disk.DataOutput')
    def test_process_storage_disk_sas_now(self, mock_out):
        self.__init_command_args()
        self.task.command_args['--start-datetime'] = 'now'
        self.task.command_args['sas'] = True
        self.task.process()
        expiry = dateutil.parser.parse(
            self.task.command_args['--expiry-datetime']
        )
        self.task.storage.disk_image_sas.assert_called_once_with(
            'foo', self.task.command_args['--blob-name'], mock.ANY, expiry, 'rl'
        )

    @patch('azurectl.commands.storage_disk.DataOutput')
    def test_process_storage_disk_sas_expire(self, mock_out):
        self.__init_command_args()
        self.task.command_args['--expiry-datetime'] = '30 days from start'
        self.task.command_args['sas'] = True
        self.task.process()
        start = dateutil.parser.parse(
            self.task.command_args['--start-datetime']
        )
        expiry = start + datetime.timedelta(days=30)
        self.task.storage.disk_image_sas.assert_called_once_with(
            'foo', self.task.command_args['--blob-name'], start, expiry, 'rl'
        )
