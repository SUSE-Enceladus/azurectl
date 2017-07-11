from .test_helper import argv_kiwi_tests

import sys
import mock
from mock import patch
import azurectl
from pytest import raises
from azurectl.commands.setup_account import SetupAccountTask

from azurectl.azurectl_exceptions import AzureAccountConfigurationError


class TestSetupAccountTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], 'setup', 'account', 'list'
        ]
        self.setup = mock.Mock()
        azurectl.commands.setup_account.AccountSetup = mock.Mock(
            return_value=self.setup
        )
        azurectl.commands.setup_account.Help = mock.Mock(
            return_value=mock.Mock()
        )
        self.task = SetupAccountTask()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def __init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['--color'] = False
        self.task.command_args['--create'] = False
        self.task.command_args['--name'] = 'some-name'
        self.task.command_args['--publish-settings-file'] = 'file'
        self.task.command_args['--storage-account-name'] = 'storage-name'
        self.task.command_args['--container-name'] = 'container-name'
        self.task.command_args['--subscription-id'] = None
        self.task.command_args['--management-pem-file'] = None
        self.task.command_args['--management-url'] = None
        self.task.command_args['--region'] = 'region'
        self.task.command_args['default'] = False
        self.task.command_args['list'] = False
        self.task.command_args['add'] = False
        self.task.command_args['configure'] = False
        self.task.command_args['region'] = False
        self.task.command_args['remove'] = False
        self.task.command_args['help'] = False

    @patch('azurectl.commands.setup_account.Config.set_default_config_file')
    @patch('azurectl.logger.log')
    def test_process_setup_account_default(self, mock_log, mock_set_default):
        self.__init_command_args()
        self.task.command_args['default'] = True
        self.task.process()
        mock_set_default.assert_called_once_with(account_name='some-name')

    @patch('azurectl.commands.setup_account.Config.get_config_file_list')
    @patch('azurectl.commands.setup_account.AccountSetup')
    @patch('azurectl.commands.setup_account.DataOutput.display')
    @patch('azurectl.logger.log')
    @patch('os.path.islink')
    def test_process_setup_account_list(
        self, mock_islink, mock_log, mock_display,
        mock_account_setup, mock_config_files
    ):
        mock_islink.return_value = False
        mock_config_files.return_value = ['a']
        setup = mock.Mock()
        mock_account_setup.return_value = setup
        self.__init_command_args()
        self.task.command_args['list'] = True
        self.task.process()
        mock_account_setup.assert_called_once_with('a')
        setup.list.assert_called_once_with()

    @patch('azurectl.commands.setup_account.Config.get_config_file_list')
    @patch('azurectl.commands.setup_account.DataCollector')
    @patch('azurectl.commands.setup_account.DataOutput.display')
    @patch('azurectl.logger.log')
    @patch('os.path.islink')
    @patch('os.readlink')
    def test_process_setup_account_list_linked_default(
        self, mock_readlink, mock_islink, mock_log, mock_display,
        mock_data_collector, mock_config_files
    ):
        mock_readlink.return_value = 'link-target'
        mock_islink.return_value = True
        mock_config_files.return_value = ['a']
        result = mock.Mock()
        mock_data_collector.return_value = result
        self.__init_command_args()
        self.task.command_args['list'] = True
        self.task.process()
        result.add.assert_called_once_with(
            'default_config_file', 'link-target'
        )

    def test_process_setup_region_add(self):
        self.__init_command_args()
        self.task.command_args['add'] = True
        self.task.command_args['region'] = True
        self.task.process()
        self.task.setup.add_region.assert_called_once_with(
            self.task.command_args['--region'],
            self.task.command_args['--storage-account-name'],
            self.task.command_args['--container-name']
        )

    def test_process_setup_configure_account(self):
        self.__init_command_args()
        self.task.command_args['configure'] = True
        self.task.process()
        self.task.setup.configure_account.assert_called_once_with(
            self.task.command_args['--name'],
            self.task.command_args['--publish-settings-file'],
            self.task.command_args['--region'],
            self.task.command_args['--storage-account-name'],
            self.task.command_args['--container-name'],
            self.task.command_args['--subscription-id'],
            self.task.command_args['--management-pem-file'],
            self.task.command_args['--management-url']
        )

    @patch('azurectl.commands.setup_account.Config')
    def test_process_setup_configure_account_existing(self, mock_config):
        self.__init_command_args()
        self.task.command_args['configure'] = True
        default_config = mock.Mock()
        default_config.config.has_section = mock.Mock(
            return_value=True
        )
        mock_config.return_value = default_config
        with raises(AzureAccountConfigurationError):
            self.task.process()

    @patch('azurectl.commands.setup_account.Config')
    def test_process_setup_configure_account_no_default_exists(
        self, mock_config
    ):
        mock_config.side_effect = Exception
        self.__init_command_args()
        self.task.command_args['configure'] = True
        self.task.process()
        self.task.setup.configure_account.assert_called_once_with(
            self.task.command_args['--name'],
            self.task.command_args['--publish-settings-file'],
            self.task.command_args['--region'],
            self.task.command_args['--storage-account-name'],
            self.task.command_args['--container-name'],
            self.task.command_args['--subscription-id'],
            self.task.command_args['--management-pem-file'],
            self.task.command_args['--management-url']
        )

    @patch('azurectl.commands.setup_account.AzureAccount')
    @patch('azurectl.commands.setup_account.Config')
    @patch('azurectl.commands.setup_account.StorageAccount')
    @patch('azurectl.commands.setup_account.Container')
    def test_process_setup_configure_and_create_account_failed(
        self, mock_container, mock_storage, mock_config, mock_account_azure
    ):
        self.__init_command_args()
        self.task.command_args['configure'] = True
        self.task.command_args['--create'] = True
        mock_config.return_value = None
        storage_account = mock.Mock()
        storage_account.exists.return_value = False
        storage_account.create.side_effect = Exception
        mock_storage.return_value = storage_account
        self.task.load_config = mock.Mock()
        self.task.config = mock.Mock()
        with raises(AzureAccountConfigurationError):
            self.task.process()

    @patch('azurectl.commands.setup_account.AzureAccount')
    @patch('azurectl.commands.setup_account.Config')
    @patch('azurectl.commands.setup_account.StorageAccount')
    @patch('azurectl.commands.setup_account.Container')
    def test_process_setup_configure_and_create_account(
        self, mock_container, mock_storage, mock_config, mock_account_azure
    ):
        self.__init_command_args()
        self.task.command_args['configure'] = True
        self.task.command_args['--create'] = True
        mock_config.return_value = None
        storage_account = mock.Mock()
        storage_account.exists.return_value = False
        storage_account.create.return_value = 42
        mock_storage.return_value = storage_account
        container = mock.Mock()
        container.exists.return_value = False
        mock_container.return_value = container
        self.task.load_config = mock.Mock()
        self.task.request_wait = mock.Mock()
        self.task.config = mock.Mock()

        self.task.process()
        self.task.setup.configure_account.assert_called_once_with(
            self.task.command_args['--name'],
            self.task.command_args['--publish-settings-file'],
            self.task.command_args['--region'],
            self.task.command_args['--storage-account-name'],
            self.task.command_args['--container-name'],
            self.task.command_args['--subscription-id'],
            self.task.command_args['--management-pem-file'],
            self.task.command_args['--management-url']
        )
        storage_account.create.assert_called_once_with(
            account_type='Standard_GRS',
            description='some-name',
            label='storage-name',
            name='storage-name'
        )
        self.task.request_wait.assert_called_once_with(42)
        container.create.assert_called_once_with('container-name')

    @patch('azurectl.commands.setup_account.AzureAccount')
    @patch('azurectl.commands.setup_account.Config')
    @patch('azurectl.commands.setup_account.StorageAccount')
    @patch('azurectl.commands.setup_account.Container')
    def test_process_setup_configure_and_create_account_existing(
        self, mock_container, mock_storage, mock_config, mock_account_azure
    ):
        self.__init_command_args()
        self.task.command_args['configure'] = True
        self.task.command_args['--create'] = True
        mock_config.return_value = None
        storage_account = mock.Mock()
        storage_account.exists.return_value = True
        mock_storage.return_value = storage_account
        container = mock.Mock()
        container.exists.return_value = True
        mock_container.return_value = container
        self.task.load_config = mock.Mock()
        self.task.config = mock.Mock()

        self.task.process()
        self.task.setup.configure_account.assert_called_once_with(
            self.task.command_args['--name'],
            self.task.command_args['--publish-settings-file'],
            self.task.command_args['--region'],
            self.task.command_args['--storage-account-name'],
            self.task.command_args['--container-name'],
            self.task.command_args['--subscription-id'],
            self.task.command_args['--management-pem-file'],
            self.task.command_args['--management-url']
        )

    def test_process_setup_account_remove(self):
        self.__init_command_args()
        self.task.command_args['remove'] = True
        self.task.process()
        self.task.setup.remove.assert_called_once_with()

    def test_process_setup_default_region(self):
        self.__init_command_args()
        self.task.command_args['default'] = True
        self.task.command_args['region'] = True
        self.task.process()
        self.task.setup.set_default_region.assert_called_once_with(
            self.task.command_args['--region']
        )

    def test_process_setup_account_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'azurectl::setup::account'
        )

    def test_process_setup_account_region_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['region'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'azurectl::setup::account::region'
        )
