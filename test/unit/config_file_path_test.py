import mock

from mock import patch

from test_helper import *

from azurectl.azurectl_exceptions import *
from azurectl.config_file_path import ConfigFilePath

import os


class TestConfigFilePath:
    def setup(self):
        with patch.dict('os.environ', {'HOME': 'foo'}):
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
    def test_default_path(self, mock_isfile):
        mock_isfile.return_value = True
        assert self.paths.default_config() == \
            os.environ['HOME'] + '/' + self.paths.config_files[0]

    def test_default_new_account_config(self):
        assert self.paths.default_new_account_config() == \
            os.environ['HOME'] + '/.config/azurectl/bob.config'
