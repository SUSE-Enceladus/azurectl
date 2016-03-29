import sys
import mock
from mock import patch
from test_helper import *

from azurectl.azurectl_exceptions import (
    AzureConfigParseError,
    AzureConfigAddAccountSectionError,
    AzureConfigAddRegionSectionError,
    AzureConfigPublishSettingsError,
    AzureConfigWriteError
)
from azurectl.account_setup import AccountSetup

import azurectl


class TestAccountSetup:
    def setup(self):
        self.setup = AccountSetup('../data/config')
        self.orig_data = {
            'DEFAULT': {
                'account': 'account:bob',
                'region': 'region:East US 2'
            },
            'accounts': {
                'account:bob': {
                    'publishsettings': '../data/publishsettings'
                },
                'account:foo': {
                    'publishsettings': '../data/publishsettings'
                }
            },
            'regions': {
                'region:East US 2': {
                    'default_storage_container': 'foo',
                    'default_storage_account': 'bob'
                },
                'region:West US 1': {
                    'default_storage_container': 'bar',
                    'default_storage_account': 'joe'
                }
            }
        }
        self.delete_account_data = {
            'DEFAULT': {
                'account': 'account:bob',
                'region': 'region:East US 2'
            },
            'accounts': {
                'account:bob': {
                    'publishsettings': '../data/publishsettings'
                }
            },
            'regions': {
                'region:East US 2': {
                    'default_storage_account': 'bob',
                    'default_storage_container': 'foo'
                },
                'region:West US 1': {
                    'default_storage_container': 'bar',
                    'default_storage_account': 'joe'
                }
            }
        }
        self.delete_region_data = {
            'DEFAULT': {
                'account': 'account:bob',
                'region': 'region:East US 2'
            },
            'accounts': {
                'account:bob': {
                    'publishsettings': '../data/publishsettings'
                },
                'account:foo': {
                    'publishsettings': '../data/publishsettings'
                }
            },
            'regions': {
                'region:East US 2': {
                    'default_storage_account': 'bob',
                    'default_storage_container': 'foo'
                }
            }
        }
        self.add_account_data = {
            'DEFAULT': {
                'account': 'account:bob',
                'region': 'region:East US 2'
            },
            'accounts': {
                'account:bob': {
                    'publishsettings': '../data/publishsettings'
                },
                'account:foo': {
                    'publishsettings': '../data/publishsettings'
                },
                'account:xxx': {
                    'subscription_id': '1234',
                    'publishsettings': '../data/publishsettings'
                }
            },
            'regions': {
                'region:East US 2': {
                    'default_storage_account': 'bob',
                    'default_storage_container': 'foo'
                },
                'region:West US 1': {
                    'default_storage_container': 'bar',
                    'default_storage_account': 'joe'
                }
            }
        }
        self.add_region_data = {
            'DEFAULT': {
                'account': 'account:bob',
                'region': 'region:East US 2'
            },
            'accounts': {
                'account:bob': {
                    'publishsettings': '../data/publishsettings'
                },
                'account:foo': {
                    'publishsettings': '../data/publishsettings'
                }
            },
            'regions': {
                'region:East US 2': {
                    'default_storage_account': 'bob',
                    'default_storage_container': 'foo'
                },
                'region:West US 1': {
                    'default_storage_container': 'bar',
                    'default_storage_account': 'joe'
                },
                'region:some-region': {
                    'default_storage_account': 'storage',
                    'default_storage_container': 'container'
                }
            }
        }
        self.configure_data = {
            'DEFAULT': {
                'account': 'account:bob',
                'region': 'region:East US 2'
            },
            'accounts': {
                'account:bob': {
                    'publishsettings': '../data/publishsettings'
                },
                'account:foo': {
                    'publishsettings': '../data/publishsettings'
                },
                'account:xxx': {
                    'subscription_id': '1234',
                    'publishsettings': '../data/publishsettings'
                }
            },
            'regions': {
                'region:East US 2': {
                    'default_storage_account': 'bob',
                    'default_storage_container': 'foo'
                },
                'region:West US 1': {
                    'default_storage_container': 'bar',
                    'default_storage_account': 'joe'
                },
                'region:some-region': {
                    'default_storage_account': 'storage',
                    'default_storage_container': 'container'
                }
            }
        }

    def test_list(self):
        assert self.setup.list() == self.orig_data

    def test_configure_account_and_region(self):
        self.setup.configure_account_and_region(
            'xxx', '../data/publishsettings',
            'some-region', 'storage', 'container',
            '1234'
        )
        assert self.setup.list() == self.configure_data

    def test_add_account(self):
        self.setup.add_account(
            'xxx', '../data/publishsettings', '1234'
        )
        assert self.setup.list() == self.add_account_data

    def test_add_region(self):
        self.setup.add_region(
            'some-region', 'storage', 'container'
        )
        assert self.setup.list() == self.add_region_data

    def test_add_first_account_as_default(self):
        setup = AccountSetup('../data/config.new')
        setup.add_account(
            'some-account', '../data/publishsettings', '1234'
        )
        assert setup.list()['DEFAULT']['account'] == 'account:some-account'

    def test_add_first_region_as_default(self):
        setup = AccountSetup('../data/config.new')
        setup.add_region(
            'earth', 'storage', 'container'
        )
        assert setup.list()['DEFAULT']['region'] == 'region:earth'

    @patch('__builtin__.open')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_add_creates_dir(self, mock_makedirs, mock_exists, mock_open):
        mock_exists.return_value = False
        self.setup.write()
        assert mock_open.called
        assert mock_exists.called
        assert mock_makedirs.called

    def test_set_default_account(self):
        self.setup.set_default_account('foo')
        assert self.setup.list()['DEFAULT']['account'] == 'account:foo'
        assert self.setup.set_default_account('foofoo') is False

    def test_set_default_region(self):
        self.setup.set_default_region('West US 1')
        assert self.setup.list()['DEFAULT']['region'] == 'region:West US 1'
        assert self.setup.set_default_region('foofoo') is False

    @patch('os.remove')
    def test_remove(self, mock_remove):
        self.setup.remove()
        mock_remove.assert_called_once_with('../data/config')

    def test_remove_account(self):
        self.setup.remove_account('foo')
        assert self.setup.list() == self.delete_account_data

    def test_remove_region(self):
        self.setup.remove_region('West US 1')
        assert self.setup.list() == self.delete_region_data

    def test_remove_default_account(self):
        assert self.setup.remove_account('bob') is False

    def test_remove_default_region(self):
        assert self.setup.remove_region('East US 2') is False

    def test_remove_section_does_not_exist(self):
        assert self.setup.remove_account('foofoo') is False
        assert self.setup.remove_region('foofoo') is False

    @raises(AzureConfigWriteError)
    @patch('__builtin__.open')
    def test_write_raise(self, mock_open):
        mock_open.side_effect = AzureConfigWriteError
        self.setup.filename = '/some-config'
        self.setup.write()

    @raises(AzureConfigParseError)
    def test_parse_raise(self):
        AccountSetup('../data/blob.xz')

    @raises(AzureConfigPublishSettingsError)
    def test_add_raise_publish_settings_error(self):
        self.setup.add_account(
            'xxx', '../data/does-not-exist'
        )

    @raises(AzureConfigAddAccountSectionError)
    def test_add_account_raise(self):
        self.setup.add_account(
            'bob', '../data/publishsettings'
        )

    @raises(AzureConfigAddRegionSectionError)
    def test_add_region_raise(self):
        self.setup.add_region(
            'East US 2', 'some-region', 'storage'
        )
