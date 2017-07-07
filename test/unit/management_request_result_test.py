import sys
import mock
from mock import patch


from .test_helper import raises

from azurectl.azurectl_exceptions import *
from azurectl.management.request_result import RequestResult

import azurectl

from collections import namedtuple


class TestRequestResult:
    def setup(self):
        self.request_result = RequestResult(42)
        self.service = mock.Mock()

    @patch('azurectl.management.request_result.time.sleep')
    def test_status(self, mock_time):
        self.request_result.status(self.service)
        self.service.get_operation_status.assert_called_once_with(42)

    @patch('azurectl.management.request_result.time.sleep')
    @raises(AzureRequestTimeout)
    def test_wait_for_request_completion_timeout(self, mock_time):
        MyStatus = namedtuple(
            'MyStatus',
            'status'
        )
        status = MyStatus(status='InProgress')
        self.service.get_operation_status.return_value = status
        self.request_result.wait_for_request_completion(self.service)
        self.service.get_operation_status.assert_called_once_with(42)

    @patch('azurectl.management.request_result.time.sleep')
    @raises(AzureRequestError)
    def test_wait_for_request_completion_error(self, mock_time):
        MyStatus = namedtuple(
            'MyStatus',
            'status error'
        )
        MyError = namedtuple(
            'MyError',
            'message code'
        )
        status = MyStatus(
            status='Failed', error=MyError(message='foo', code=1)
        )
        self.service.get_operation_status.return_value = status
        self.request_result.wait_for_request_completion(self.service)
        self.service.get_operation_status.assert_called_once_with(42)

    @raises(AzureRequestStatusError)
    @patch('azurectl.management.request_result.time.sleep')
    def test_status_error(self, mock_time):
        self.service.get_operation_status.side_effect = AzureRequestStatusError
        self.request_result.status(self.service)
