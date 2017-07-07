# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import subprocess
import lzma

# project
from azurectl.azurectl_exceptions import AzureXZError


class XZ(object):
    """
        Implements decompression of lzma compressed files
    """
    LZMA_STREAM_BUFFER_SIZE = 8192

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lzma_stream.close()

    def __init__(self, lzma_stream, buffer_size=LZMA_STREAM_BUFFER_SIZE):
        self.lzma_stream = lzma_stream
        self.buffer_size = int(buffer_size)
        self.lzma = lzma.LZMADecompressor()

    def read(self, size):
        if self.lzma.eof:
            return None
        chunks = self.lzma.decompress(
            self.lzma.unused_data + self.lzma_stream.read(self.buffer_size)
        )
        bytes_uncompressed = len(chunks)
        while not self.lzma.eof and bytes_uncompressed < size:
            # Because the max_length parameter was added to the decompress()
            # method with python 3.5 for the first time and we have to stay
            # compatible with 3.4 the given size argument to this method can
            # only be treated as a minimum size constraint which has to be
            # valid but can not be used as exact value unless the buffer_size
            # is set to 1
            chunks += self.lzma.decompress(
                self.lzma.unused_data + self.lzma_stream.read(self.buffer_size)
            )
            bytes_uncompressed = len(chunks)
        if self.lzma.eof:
            # there is one superfluous newline with the last chunk
            chunks = chunks[:-1]

        return chunks.decode()

    @classmethod
    def close(self):
        self.lzma_stream.close()

    @classmethod
    def open(self, file_name, buffer_size=LZMA_STREAM_BUFFER_SIZE):
        self.lzma_stream = open(file_name, 'rb')
        return XZ(self.lzma_stream, buffer_size)

    @classmethod
    def uncompressed_size(self, file_name):
        xz_info = subprocess.Popen(
            ['xz', '--robot', '--list', file_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        output, error = xz_info.communicate()
        if xz_info.returncode != 0:
            raise AzureXZError('%s' % error)
        total = output.decode().strip().split('\n').pop()
        return int(total.split()[4])
