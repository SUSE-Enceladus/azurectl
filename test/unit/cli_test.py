import sys


from .test_helper import raises, argv_kiwi_tests

from azurectl.cli import Cli
from azurectl.azurectl_exceptions import *


class TestCli:
    def setup(self):
        self.help_global_args = {
            '--output-format': None,
            'help': False,
            '--region': None,
            '--storage-container': None,
            'compute': False,
            'setup': False,
            'storage': True,
            '-h': False,
            '--output-style': None,
            '--config': None,
            '--account': None,
            '--debug': False,
            '--version': False,
            '--help': False,
            '--storage-account': None
        }
        self.help_command_args = {
            '--expiry-datetime': '30 days from start',
            '--help': False,
            '--name': None,
            '--permissions': 'rl',
            '--start-datetime': 'now',
            '-h': False,
            'container': True,
            'create': False,
            'delete': False,
            'help': False,
            'list': True,
            'sas': False,
            'show': False,
            'storage': True
        }
        sys.argv = [
            sys.argv[0], 'storage', 'container', 'list'
        ]
        self.cli = Cli()
        self.loaded_command = self.cli.load_command()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def test_show_help(self):
        assert self.cli.show_help() is False

    def test_get_servicename(self):
        assert self.cli.get_servicename() == 'storage'

    def test_get_command(self):
        assert self.cli.get_command() == 'container'

    def test_get_command_args(self):
        assert self.cli.get_command_args() == self.help_command_args

    def test_get_global_args(self):
        assert self.cli.get_global_args() == self.help_global_args

    def test_load_command(self):
        assert self.cli.load_command() == self.loaded_command

    @raises(SystemExit)
    def test_load_command_unknown(self):
        self.cli.loaded = False
        self.cli.all_args['<command>'] = 'foo'
        self.cli.load_command()

    @raises(AzureLoadCommandUndefined)
    def test_load_command_undefined(self):
        self.cli.loaded = False
        self.cli.all_args['<command>'] = None
        self.cli.load_command()

    @raises(AzureCommandNotLoaded)
    def test_get_command_args_not_loaded(self):
        self.cli.loaded = False
        self.cli.get_command_args()

    @raises(AzureUnknownServiceName)
    def test_get_servicename_unknown(self):
        self.cli.all_args['compute'] = False
        self.cli.all_args['setup'] = False
        self.cli.all_args['storage'] = False
        self.cli.get_servicename()
