from .test_helper import argv_kiwi_tests

import os
import mock
from mock import patch
from azurectl.azurectl_exceptions import *
from azurectl.config.file_path import ConfigFilePath


class TestConfigFilePath:
    def setup(self):
        self.paths = ConfigFilePath(account_name='bob', platform='lin')

    def test_home_path_linux(self):
        with patch.dict('os.environ', {'HOME': 'foo'}):
            paths = ConfigFilePath(platform='lin')
            assert paths.default_new_config() == \
                os.environ['HOME'] + '/.config/azurectl/config'

    def test_home_path_win(self):
        with patch.dict('os.environ', {'HOMEPATH': 'foo'}):
            paths = ConfigFilePath(platform='win')
            assert paths.default_new_config() == \
                os.environ['HOMEPATH'] + '/.config/azurectl/config'
        with patch.dict('os.environ', {'UserProfile': 'foo'}):
            paths = ConfigFilePath(platform='win')
            assert paths.default_new_config() == \
                os.environ['UserProfile'] + '/.config/azurectl/config'

    @patch('os.path.isfile')
    def test_default_config(self, mock_isfile):
        mock_isfile.return_value = True
        assert self.paths.default_config() == \
            os.environ['HOME'] + '/' + self.paths.config_files[0]

    def test_default_new_account_config(self):
        assert self.paths.default_new_account_config() == \
            os.environ['HOME'] + '/.config/azurectl/bob.config'

    @patch('glob.iglob')
    def test_account_config(self, mock_glob):
        mock_glob.return_value = ['a', 'b', 'c']
        assert self.paths.account_config() == mock_glob.return_value
        mock_glob.assert_called_once_with(
            os.environ['HOME'] + '/.config/azurectl/*.config'
        )
