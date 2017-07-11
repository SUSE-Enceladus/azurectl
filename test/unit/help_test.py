from .test_helper import argv_kiwi_tests

import sys
from mock import patch
from azurectl.help import Help
from pytest import raises

from azurectl.azurectl_exceptions import AzureHelpNoCommandGiven


class TestHelp:
    def setup(self):
        self.help = Help()

    def test_show(self):
        with raises(AzureHelpNoCommandGiven):
            self.help.show(None)

    @patch('subprocess.call')
    def test_show_command(self, mock_process):
        self.help.show('foo')
        mock_process.assert_called_once_with('man foo', shell=True)
