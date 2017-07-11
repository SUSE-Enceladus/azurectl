from .test_helper import argv_kiwi_tests

import sys
from azurectl.utils.collector import DataCollector


class TestDataCollector:
    def setup(self):
        self.collector = DataCollector()

    def test_get(self):
        assert self.collector.get() == {}

    def test_add(self):
        self.collector.add('some-name', 'some-data')
        assert self.collector.get() == {'some-name': 'some-data'}
