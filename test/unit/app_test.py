from .test_helper import argv_kiwi_tests

import sys
import pytest
import mock
from azurectl.app import App


class TestApp:
    def test_app(self, monkeypatch):
        mock_app = mock.Mock()
        monkeypatch.setattr('azurectl.app.CliTask', mock_app)

        app = mock.Mock()
        app.cli.get_command = mock.Mock(
            return_value='action'
        )
        app.cli.get_servicename = mock.Mock(
            return_value='service'
        )
        task = mock.Mock()
        task_instance = mock.Mock(
            return_value=task
        )
        app.task.__dict__ = {
            'ServiceActionTask': task_instance
        }
        mock_app.return_value = app
        App()
        task.process.assert_called_once_with()
