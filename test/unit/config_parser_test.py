import mock

from mock import patch

from .test_helper import raises

from azurectl.azurectl_exceptions import *
from azurectl.config.parser import Config

import os


class TestConfig:
    def setup(self):
        self.config = Config(
            region_name='East US 2', filename='../data/config'
        )

    def test_get_account_name(self):
        assert self.config.get_account_name() == 'bob'

    def test_get_region_name(self):
        assert self.config.get_region_name() == 'East US 2'

    def test_get_storage_account_name(self):
        assert self.config.get_storage_account_name() == 'bob'

    def test_get_storage_container_name(self):
        assert self.config.get_storage_container_name() == 'foo'

    @patch('os.path.isfile')
    def test_get_config_file(self, mock_isfile):
        mock_isfile.return_value = True
        with patch.dict('os.environ', {'HOME': 'foo'}):
            assert Config.get_config_file(
                account_name='bob', platform='lin'
            ) == 'foo/.config/azurectl/bob.config'
        with patch.dict('os.environ', {'HOME': 'foo'}):
            assert Config.get_config_file(
                filename='bob', platform='lin'
            ) == 'bob'
        with patch.dict('os.environ', {'HOME': 'foo'}):
            assert Config.get_config_file(
                platform='lin'
            ) == 'foo/.config/azurectl/config'

    @patch('azurectl.config.parser.ConfigFilePath')
    def test_get_config_file_list(self, mock_config_path):
        paths = mock.Mock()
        paths.default_config.return_value = 'a'
        paths.account_config.return_value = ['b', 'c']
        mock_config_path.return_value = paths
        assert Config.get_config_file_list() == ['a', 'b', 'c']
        paths.default_config.assert_called_once_with()
        paths.account_config.assert_called_once_with()

    @patch('azurectl.config.parser.ConfigFilePath')
    @patch('os.remove')
    @patch('os.symlink')
    @patch('os.path.exists')
    @patch('os.path.islink')
    def test_set_default_config_file(
        self, mock_islink, mock_exists, mock_symlink, mock_remove,
        mock_config_path
    ):
        paths = mock.Mock()
        paths.default_new_account_config.return_value = 'account-config'
        paths.default_config.return_value = None
        paths.default_new_config.return_value = 'default-config'
        mock_config_path.return_value = paths
        mock_exists.return_value = True
        mock_islink.return_value = True
        Config.set_default_config_file('account-name')
        mock_config_path.assert_called_once_with('account-name', None)
        mock_remove.assert_called_once_with('default-config')
        mock_symlink.assert_called_once_with(
            'account-config', 'default-config'
        )

    @patch('azurectl.config.parser.ConfigFilePath')
    @patch('os.path.exists')
    @raises(AzureConfigAccountFileNotFound)
    def test_set_default_config_file_acount_config_does_not_exist(
        self, mock_exists, mock_config_path
    ):
        paths = mock.Mock()
        paths.default_new_account_config.return_value = 'account-config'
        mock_config_path.return_value = paths
        mock_exists.return_value = False
        Config.set_default_config_file('account-name')

    @patch('azurectl.config.parser.ConfigFilePath')
    @patch('os.path.exists')
    @patch('os.path.islink')
    @raises(AzureConfigDefaultLinkError)
    def test_set_default_config_file_exists_as_file(
        self, mock_islink, mock_exists, mock_config_path
    ):
        paths = mock.Mock()
        paths.default_new_account_config.return_value = 'account-config'
        paths.default_config.return_value = 'default-config'
        mock_config_path.return_value = paths
        mock_exists.return_value = True
        mock_islink.return_value = False
        Config.set_default_config_file('account-name')

    @raises(AzureConfigVariableNotFound)
    def test_get_subscription_id_missing(self):
        assert self.config.get_subscription_id()

    @raises(AzureConfigVariableNotFound)
    def test_get_publishsettings_file_name_missing(self):
        config = Config(
            region_name='East US 2',
            filename='../data/config.missing_region_data'
        )
        config.get_storage_account_name()

    def test_get_publishsettings_file_name(self):
        assert self.config.get_publishsettings_file_name() == \
            '../data/publishsettings'

    @raises(AzureConfigSectionNotFound)
    def test_account_section_not_found(self):
        Config(filename='../data/config.invalid_account')

    @raises(AzureConfigVariableNotFound)
    def test_region_section_not_found(self):
        Config(
            filename='../data/config.invalid_region'
        ).get_storage_account_name()

    @raises(AzureConfigVariableNotFound)
    def test_region_not_present(self):
        Config(
            filename='../data/config.no_region'
        ).get_storage_account_name()

    def test_get_region_name_with_region_arg_but_no_config(self):
        expected = 'Foo Test Region'
        result = Config(
            region_name=expected,
            filename='../data/config.no_region'
        ).get_region_name()
        assert result == expected

    @raises(AzureConfigAccountNotFound)
    def test_account_not_present(self):
        Config(filename='../data/config.no_account')

    @raises(AzureConfigParseError)
    def test_parse_error(self):
        Config(filename='../data/config_parse_error')

    @raises(AzureAccountLoadFailed)
    @patch('os.path.isfile')
    def test_config_account_name_not_found(self, mock_isfile):
        mock_isfile.return_value = False
        Config(
            account_name='account-name'
        )

    @raises(AzureAccountLoadFailed)
    @patch('os.path.isfile')
    def test_config_file_not_found(self, mock_isfile):
        mock_isfile.return_value = False
        Config(filename="does-not-exist")

    @raises(AzureAccountLoadFailed)
    @patch('os.path.isfile')
    def test_default_config_file_not_found(self, mock_isfile):
        mock_isfile.return_value = False
        Config()

    @raises(AzureAccountDefaultSectionNotFound)
    def test_no_default_section_in_config(self):
        Config(
            region_name='East US 2', filename='../data/config.no_default'
        )
