from .test_helper import argv_kiwi_tests

import sys
import mock
from mock import patch
import logging
import azurectl
from azurectl.commands.base import CliTask
from azure.servicemanagement.models import Operation
from pytest import raises

class TestCliTask:
    def teardown(self):
        sys.argv = argv_kiwi_tests

    @patch('azurectl.commands.base.Help.show')
    def test_show_help(self, help_show):
        sys.argv = [
            sys.argv[0], 'help'
        ]
        with raises(SystemExit):
            CliTask()

    @patch('azurectl.commands.base.Cli.show_help')
    @patch('azurectl.logger.log.setLevel')
    def test_cli_init(self, mock_loglevel, mock_show_help):
        sys.argv = [
            sys.argv[0],
            '--debug',
            '--region', 'region',
            '--config', 'config',
            'storage', 'container', 'list'
        ]
        mock_show_help.return_value = False
        task = CliTask()
        mock_loglevel.assert_called_once_with(logging.DEBUG)

    @patch('azurectl.commands.base.Validations.validate_min_length')
    def test_validate_min_length(self, mock_validation):
        sys.argv = [
            sys.argv[0],
            'setup', 'account', 'region', 'default', '--name', 'test-name0',
            '--region', 'some-region'
        ]
        task = CliTask()
        task.validate_min_length('--name', 5)
        mock_validation.assert_called_once_with('--name', 'test-name0', 5)

    @patch('azurectl.commands.base.Validations.validate_max_length')
    def test_validate_max_length(self, mock_validation):
        sys.argv = [
            sys.argv[0],
            'setup', 'account', 'region', 'default', '--name', 'test-name0',
            '--region', 'some-region'
        ]
        task = CliTask()
        task.validate_max_length('--name', 10)
        mock_validation.assert_called_once_with('--name', 'test-name0', 10)

    @patch('azurectl.commands.base.Cli.show_help')
    @patch('azurectl.commands.base.Config')
    @patch('azurectl.logger.log.setLevel')
    def test_load_config(
        self, mock_loglevel, mock_config, mock_show_help
    ):
        sys.argv = [
            sys.argv[0],
            '--debug',
            '--region', 'region',
            '--config', 'config',
            'storage', 'container', 'list'
        ]
        mock_show_help.return_value = False
        task = CliTask()
        task.load_config()
        mock_config.assert_called_once_with(
            None, 'region', None, None, 'config'
        )
        mock_loglevel.assert_called_once_with(logging.DEBUG)

    @patch('azurectl.commands.base.RequestResult')
    def test_request_wait(self, mock_request):
        sys.argv = [sys.argv[0], 'compute', 'vm', 'types']
        task = CliTask()
        request = mock.Mock()
        service = mock.Mock()

        mock_request.return_value = request

        account = mock.Mock()
        account.get_management_service = mock.Mock(
            return_value=service
        )
        task.account = account
        task.request_wait(42)
        mock_request.assert_called_once_with(42)
        request.wait_for_request_completion.assert_called_once_with(
            service
        )

    @patch('azurectl.commands.base.RequestResult')
    def test_request_status(self, mock_request):
        sys.argv = [sys.argv[0], 'compute', 'vm', 'types']
        task = CliTask()
        request = mock.Mock()
        operation = Operation()
        operation.status = 'Failed'
        operation.error.message = 'Unable to get vm types.'
        request.status.return_value = operation
        mock_request.return_value = request
        task.account = mock.Mock()
        status = task.request_status(42)
        assert status['result'] == 'Failed'
        assert status['message'] == 'Unable to get vm types.'
        mock_request.assert_called_once_with(42)
