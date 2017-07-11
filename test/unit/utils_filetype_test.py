from .test_helper import argv_kiwi_tests

from azurectl.utils.filetype import FileType


class TestFileType:
    def setup(self):
        self.filetype_xz = FileType('../data/blob.xz')
        self.filetype_not_xz = FileType('../data/id_test')

    def test_is_xz(self):
        assert self.filetype_xz.is_xz() is True

    def test_not_xz(self):
        assert self.filetype_not_xz.is_xz() is False

    def test_basename(self):
        assert self.filetype_xz.basename() == 'blob'
        assert self.filetype_not_xz.basename() == 'id_test'
