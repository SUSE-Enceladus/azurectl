from .test_helper import argv_kiwi_tests

import sys
import mock
from mock import patch
from mock import call
from pytest import raises
from azurectl.storage.page_blob import PageBlob
import azurectl

from azurectl.azurectl_exceptions import (
    AzurePageBlobAlignmentViolation,
    AzurePageBlobSetupError,
    AzurePageBlobUpdateError,
    AzurePageBlobZeroPageError
)


class TestPageBlob:
    def setup(self):
        self.data_stream = mock.MagicMock()
        self.blob_service = mock.Mock()
        self.blob_service.MAX_CHUNK_GET_SIZE = 4096

        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)

        self.page_blob = PageBlob(
            self.blob_service, 'blob-name', 'container-name', 1024
        )

        self.blob_service.create_blob.assert_called_once_with(
            'container-name', 'blob-name', 1024
        )

    def test_iterator(self):
        assert self.page_blob.__iter__() == self.page_blob

    def test_create_blob_raises(self):
        self.blob_service.create_blob.side_effect = Exception
        with raises(AzurePageBlobSetupError):
            PageBlob(self.blob_service, 'blob-name', 'container-name', 1024)

    def test_page_alignment_invalid(self):
        with raises(AzurePageBlobAlignmentViolation):
            PageBlob(self.blob_service, 'blob-name', 'container-name', 12)

    @patch('builtins.open')
    def test_zero_page_read_failed(self, mock_open):
        mock_open.side_effect = Exception
        with raises(AzurePageBlobZeroPageError):
            self.page_blob.next(self.data_stream)

    @patch('builtins.open')
    def test_zero_page_for_max_chunk_size(self, mock_open):
        self.page_blob.rest_bytes = self.blob_service.MAX_CHUNK_GET_SIZE
        mock_open.return_value = self.context_manager_mock
        self.page_blob.next(self.data_stream)
        self.file_mock.read.assert_called_once_with(
            self.blob_service.MAX_CHUNK_GET_SIZE
        )

    @patch('builtins.open')
    def test_zero_page_for_chunk(self, mock_open):
        self.page_blob.rest_bytes = 42
        mock_open.return_value = self.context_manager_mock
        self.page_blob.next(self.data_stream)
        self.file_mock.read.assert_called_once_with(42)

    def test_update_page(self):
        self.data_stream.read.return_value = 'some-data'
        self.page_blob.next(self.data_stream)
        self.blob_service.update_page.assert_called_once_with(
            'container-name', 'blob-name', 'some-data', 0, 8
        )

    def test_update_page_max_retries_reached(self):
        self.blob_service.update_page.side_effect = Exception
        with raises(AzurePageBlobUpdateError):
            self.page_blob.next(self.data_stream)

    def test_update_page_retried_two_times(self):
        retries = [True, False, False]

        def side_effect(container, blob, data, start, end):
            if not retries.pop():
                raise Exception

        self.blob_service.update_page.side_effect = side_effect
        self.page_blob.next(self.data_stream)
        assert len(self.blob_service.update_page.call_args_list) == 3

    def test_next_page_update_no_data(self):
        self.data_stream.read.return_value = None
        with raises(StopIteration):
            self.page_blob.next(self.data_stream)
