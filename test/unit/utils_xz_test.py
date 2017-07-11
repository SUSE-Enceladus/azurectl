from .test_helper import argv_kiwi_tests

from mock import patch
import mock

from azurectl.utils.xz import XZ


class TestXZ:
    def setup(self):
        self.xz = XZ.open('../data/blob.xz')

    def teardown(self):
        self.xz.close()

    def test_read(self):
        assert self.xz.read(128) == 'foo'

    def test_read_chunks(self):
        with XZ.open('../data/blob.more.xz', buffer_size=1) as xz:
            chunk = xz.read(8)
            assert chunk == 'Some dat'
            chunk = xz.read(8)
            assert chunk == 'a so tha'
            chunk = xz.read(8)
            assert chunk == 't we can'
            chunk = xz.read(8)
            assert chunk == ' read it'
            chunk = xz.read(8)
            assert chunk == ' as mult'
            chunk = xz.read(8)
            assert chunk == 'iple chu'
            chunk = xz.read(8)
            assert chunk == 'nks'
            chunk = xz.read(8)
            assert chunk is None

    def test_uncompressed_size(self):
        assert XZ.uncompressed_size('../data/blob.xz') == 4
