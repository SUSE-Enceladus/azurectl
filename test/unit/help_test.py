import sys

from mock import patch

from .test_helper import raises

from azurectl.help import Help
from azurectl.azurectl_exceptions import *


class TestHelp:
    def setup(self):
        self.help = Help()

    @raises(AzureHelpNoCommandGiven)
    def test_show(self):
        self.help.show(None)

    @patch('subprocess.call')
    def test_show_command(self, mock_process):
        self.help.show('foo')
        mock_process.assert_called_once_with('man foo', shell=True)
