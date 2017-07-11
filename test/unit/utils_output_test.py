from .test_helper import argv_kiwi_tests

import sys
from mock import patch
import mock
from azurectl.utils.output import DataOutput
from azurectl.utils.collector import DataCollector
import json


class TestDataOutput:
    def setup(self):
        collector = DataCollector()
        collector.add('some-name', 'some-data')
        self.expected_out = json.dumps(
            collector.get(), sort_keys=True, indent=2, separators=(',', ': ')
        )
        self.out = DataOutput(collector)

    @patch('sys.stdout')
    def test_display(self, mock_stdout):
        self.out.display()
        mock_stdout.write.assert_any_call(self.expected_out)

    @patch('sys.stdout')
    @patch('os.system')
    @patch('azurectl.utils.output.NamedTemporaryFile')
    def test_display_color(self, mock_temp, mock_system, mock_stdout):
        tempfile = mock.Mock()
        tempfile.name = 'tempfile'
        mock_temp.return_value = tempfile
        self.out.style = 'color'
        self.out.color_json = True
        self.out.display()
        mock_system.assert_called_once_with(
            'cat tempfile| pjson'
        )

    @patch('sys.stdout')
    @patch('azurectl.logger.log.warning')
    def test_display_color_no_pjson(self, mock_warn, mock_stdout):
        self.out.style = 'color'
        self.out.color_json = False
        self.out.display()
        mock_warn.assert_any_call(
            'pjson for color output not installed'
        )
        mock_warn.assert_any_call(
            'run: pip install pjson'
        )
