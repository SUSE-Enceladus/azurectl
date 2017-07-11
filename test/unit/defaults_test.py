from .test_helper import argv_kiwi_tests

from mock import patch
import mock
from azurectl.defaults import Defaults


class TestDefaults:
    def __set_account_type_docopts(self):
        self.account_type_docopts = {
            '--locally-redundant': False,
            '--zone-redundant': False,
            '--geo-redundant': False,
            '--read-access-geo-redundant': False
        }

    def __host_caching_docopts(self, selection=None):
        docopts = {
            '--no-cache': False,
            '--read-only-cache': False,
            '--read-write-cache': False
        }
        if selection:
            docopts[selection] = True
        return docopts

    def test_set_attribute(self):
        class X:
            def __init__(self):
                self.name = 'value'
        instance = X()
        Defaults.set_attribute(instance, 'name', 'foo')
        assert instance.name == 'foo'

    def test_get_attribute(self):
        class X:
            def __init__(self):
                self.name = 'value'
        instance = X()
        Defaults.get_attribute(instance, 'name')
        assert instance.name == 'value'

    def test_account_type_for_docopts(self):
        self.__set_account_type_docopts()
        self.account_type_docopts['--locally-redundant'] = True
        result = Defaults.account_type_for_docopts(self.account_type_docopts)
        assert result == 'Standard_LRS'

        self.__set_account_type_docopts()
        self.account_type_docopts['--zone-redundant'] = True
        result = Defaults.account_type_for_docopts(self.account_type_docopts)
        assert result == 'Standard_ZRS'

        self.__set_account_type_docopts()
        self.account_type_docopts['--geo-redundant'] = True
        result = Defaults.account_type_for_docopts(self.account_type_docopts)
        assert result == 'Standard_GRS'

        self.__set_account_type_docopts()
        self.account_type_docopts['--read-access-geo-redundant'] = True
        result = Defaults.account_type_for_docopts(self.account_type_docopts)
        assert result == 'Standard_RAGRS'

    def test_default_account_type_for_docopts(self):
        self.__set_account_type_docopts()
        result = Defaults.account_type_for_docopts(self.account_type_docopts)
        assert result == 'Standard_GRS'

    def test_docopt_for_account_type(self):
        result = Defaults.docopt_for_account_type('Standard_LRS')
        assert result == '--locally-redundant'

        result = Defaults.docopt_for_account_type('Standard_ZRS')
        assert result == '--zone-redundant'

        result = Defaults.docopt_for_account_type('Standard_GRS')
        assert result == '--geo-redundant'

        result = Defaults.docopt_for_account_type('Standard_RAGRS')
        assert result == '--read-access-geo-redundant'

    def test_host_caching_for_docopts(self):
        # No cache
        host_caching_docopts = self.__host_caching_docopts('--no-cache')
        assert Defaults.host_caching_for_docopts(host_caching_docopts) == 'None'
        # read-only cache
        host_caching_docopts = self.__host_caching_docopts('--read-only-cache')
        assert Defaults.host_caching_for_docopts(host_caching_docopts) == \
            'ReadOnly'

        # read-write cache
        host_caching_docopts = self.__host_caching_docopts('--read-write-cache')
        assert Defaults.host_caching_for_docopts(host_caching_docopts) == \
            'ReadWrite'

    def test_default_host_caching_for_docopts(self):
        host_caching_docopts = self.__host_caching_docopts()
        assert Defaults.host_caching_for_docopts(host_caching_docopts) == \
            'ReadOnly'
