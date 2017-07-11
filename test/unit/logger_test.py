from .test_helper import argv_kiwi_tests

from mock import patch
from azurectl.logger import *
from collections import namedtuple


class TestLoggerSchedulerFilter:
    def setup(self):
        self.scheduler_filter = LoggerSchedulerFilter()

    def test_filter(self):
        MyRecord = namedtuple(
            'MyRecord',
            'name'
        )

        ignorables = [
            'apscheduler.scheduler',
            'apscheduler.executors.default'
        ]

        for ignorable in ignorables:
            record = MyRecord(name=ignorable)
            assert self.scheduler_filter.filter(record) is False


class TestInfoFilter:
    def setup(self):
        self.info_filter = InfoFilter()

    def test_filter(self):
        MyRecord = namedtuple(
            'MyRecord',
            'levelno'
        )
        record = MyRecord(levelno=0)
        assert self.info_filter.filter(record) == 0


class TestLogger:
    @patch('sys.stdout')
    def test_progress(self, mock_stdout):
        log.progress(50, 100, 'foo')
        mock_stdout.write.assert_called_once_with(
            '\rfoo: [####################                    ] 50%'
        )
        mock_stdout.flush.assert_called_once_with()
