import sys
import mock
from mock import patch
from nose.tools import *

import nose_helper

from azurectl.azurectl_exceptions import *
from azurectl.account_setup import AccountSetup

import azurectl


class TestAccountSetup:
    def setup(self):
        self.setup = AccountSetup('../data/config')
        self.orig_data = {'default': {
            'storage_account_name': 'bob',
            'storage_container_name': 'foo',
            'publishsettings': '../data/publishsettings'}
        }
        self.add_data = {
            'default': {
                'storage_account_name': 'bob',
                'storage_container_name': 'foo',
                'publishsettings': '../data/publishsettings'
            },
            'foo': {
                'storage_account_name': 'storage',
                'publishsettings': '../data/publishsettings',
                'storage_container_name': 'container'
            }
        }

    def test_list(self):
        assert self.setup.list() == self.orig_data

    @mock.patch('__builtin__.open')
    def test_add(self, mock_open):
        self.setup.add(
            {
                'name': 'foo',
                'publishsettings': '../data/publishsettings',
                'storage_account_name': 'storage',
                'storage_container_name': 'container'
            }
        )
        assert mock_open.called
        assert self.setup.list() == self.add_data

    @mock.patch('__builtin__.open')
    def test_remove(self, mock_open):
        self.setup.remove('default')
        assert mock_open.called
        assert self.setup.list() == {}

    @raises(AzureConfigWriteError)
    def test_write_raise(self):
        self.setup.filename = '/proc/xxx'
        self.setup.remove('default')

    @raises(AzureConfigParseError)
    def test_parse_raise(self):
        AccountSetup('../data/blob.xz')

    @raises(AzureConfigPublishSettingsError)
    def test_add_raise(self):
        self.setup.add(
            {
                'name': 'foo',
                'publishsettings': '../data/does-not-exist'
            }
        )
