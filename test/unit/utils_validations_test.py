from .test_helper import argv_kiwi_tests

import sys
import mock
from mock import patch
from pytest import raises
import azurectl
from azurectl.utils.validations import Validations

from azurectl.azurectl_exceptions import AzureInvalidCommand


class TestValidations:
    def setup(self):
        self.command_args = {
            '--arg-1': 'foo',
            '--arg-2': 'bar',
            '--arg-3': False,
            '--arg-4': None
        }

    def test_good_min_length(self):
        result = Validations.validate_min_length('foo', '1234567890', 10)
        assert result is True

    def test_bad_min_length(self):
        with raises(AzureInvalidCommand):
            Validations.validate_min_length('foo', '12345', 10)

    def test_good_max_length(self):
        result = Validations.validate_max_length('foo', '1234567890', 10)
        assert result is True

    def test_bad_max_length(self):
        with raises(AzureInvalidCommand):
            Validations.validate_max_length('foo', '1234567890', 5)

    def test_good_at_least_one_argument_is_set(self):
        result = Validations.validate_at_least_one_argument_is_set(
            self.command_args,
            ['--arg-1', '--arg-2']
        )
        assert result is True

    def test_bad_at_least_one_argument_is_set(self):
        with raises(AzureInvalidCommand):
            result = Validations.validate_at_least_one_argument_is_set(
                self.command_args, ['--arg-3', '--arg-4']
            )

    def test_none_at_least_one_argument_is_set(self):
        with raises(AzureInvalidCommand):
            result = Validations.validate_at_least_one_argument_is_set(
                self.command_args
            )
