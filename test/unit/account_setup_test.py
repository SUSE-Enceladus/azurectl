from .test_helper import argv_kiwi_tests

import sys
import mock
from mock import patch
from mock import call
from pytest import raises
from azurectl.account.setup import AccountSetup
import azurectl

from azurectl.azurectl_exceptions import (
    AzureConfigParseError,
    AzureConfigAddAccountSectionError,
    AzureConfigAddRegionSectionError,
    AzureConfigPublishSettingsError,
    AzureConfigWriteError
)


class TestAccountSetup:
    def setup(self):
        self.setup = AccountSetup('../data/config')
        self.orig_data = {
            'account_region_map': {
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
            'account_region_map': {
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
            'account_region_map': {
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
            'account_region_map': {
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
            'account_region_map': {
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
            'account_region_map': {
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
        self.configure_data_for_mgmt_cert = {
            'account_region_map': {
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
                    'management_pem_file': '../data/pemfile',
                    'management_url': 'http://test.url',
                    'subscription_id': '1234',
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

    def test_configure_account_for_publishsettings(self):
        self.setup.configure_account(
            'xxx', '../data/publishsettings',
            'some-region', 'storage', 'container',
            '1234'
        )
        assert self.setup.list() == self.configure_data

    def test_configure_account_for_management_cert(self):
        self.setup.configure_account(
            'xxx', None, 'some-region', 'storage', 'container', '1234',
            '../data/pemfile', 'http://test.url'
        )
        assert self.setup.list() == self.configure_data_for_mgmt_cert

    def test_add_account_with_publishsettings(self):
        self.setup.add_account_with_publishsettings(
            'xxx', '../data/publishsettings', '1234'
        )
        assert self.setup.list() == self.add_account_data

    def test_add_region(self):
        self.setup.add_region(
            'some-region', 'storage', 'container'
        )
        assert self.setup.list() == self.add_region_data

    def test_add_first_account_as_default_with_publishsettings(self):
        setup = AccountSetup('../data/config.new')
        setup.add_account_with_publishsettings(
            'some-account', '../data/publishsettings', '1234'
        )
        assert setup.list()['account_region_map']['account'] == 'account:some-account'

    def test_add_first_account_as_default_with_mgmt_cert(self):
        setup = AccountSetup('../data/config.new')
        setup.add_account_with_management_cert(
            'some-account', '../data/pemfile', 'http://test.url', 'id1234'
        )
        assert setup.list()['account_region_map']['account'] == 'account:some-account'

    def test_add_first_region_as_default(self):
        setup = AccountSetup('../data/config.new')
        setup.add_region(
            'earth', 'storage', 'container'
        )
        assert setup.list()['account_region_map']['region'] == 'region:earth'

    @patch('builtins.open')
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
        assert self.setup.list()['account_region_map']['account'] == 'account:foo'
        assert self.setup.set_default_account('foofoo') is False

    def test_set_default_region(self):
        self.setup.set_default_region('West US 1')
        assert self.setup.list()['account_region_map']['region'] == 'region:West US 1'
        assert self.setup.set_default_region('foofoo') is False

    @patch('os.remove')
    @patch('azurectl.config.parser.Config.get_config_file')
    @patch('os.path.islink')
    @patch('os.path.exists')
    @patch('os.readlink')
    def test_remove(
        self, mock_readlink, mock_exists, mock_islink,
        mock_default_config, mock_remove
    ):
        mock_default_config.return_value = 'default-config'
        mock_readlink.return_value = 'link-target'
        mock_islink.return_value = True
        mock_exists.return_value = False
        self.setup.remove()
        assert mock_remove.call_args_list == [
            call('../data/config'),
            call('default-config')
        ]

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

    @patch('builtins.open')
    def test_write_raise(self, mock_open):
        mock_open.side_effect = AzureConfigWriteError
        self.setup.filename = '/some-config'
        with raises(AzureConfigWriteError):
            self.setup.write()

    def test_parse_raise(self):
        with raises(AzureConfigParseError):
            AccountSetup('../data/blob.xz')

    def test_add_raise_publish_settings_error(self):
        with raises(AzureConfigPublishSettingsError):
            self.setup.add_account_with_publishsettings(
                'xxx', '../data/does-not-exist'
            )

    def test_add_account_with_publishsettings_raise(self):
        with raises(AzureConfigAddAccountSectionError):
            self.setup.add_account_with_publishsettings(
                'bob', '../data/publishsettings'
            )

    def test_add_account_with_management_cert_raise(self):
        with raises(AzureConfigAddAccountSectionError):
            self.setup.add_account_with_management_cert(
                'bob', '../data/pemfile', 'http://test.url', 'id1234'
            )

    def test_add_region_raise(self):
        with raises(AzureConfigAddRegionSectionError):
            self.setup.add_region(
                'East US 2', 'some-region', 'storage'
            )
