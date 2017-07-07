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
import os
import re
import subprocess


class FileType(object):
    """
        map file magic information to type methods
    """
    def __init__(self, file_name):
        self.file_name = file_name
        file_info = subprocess.Popen(
            ['file', file_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.filetype = file_info.communicate()[0].decode()

    def is_xz(self):
        if re.match('.*: XZ compressed', self.filetype):
            return True
        return False

    def basename(self):
        name = os.path.basename(self.file_name)
        if self.is_xz():
            name = re.sub('\.(xz|lzma)$', '', name)
            name = re.sub('\.(tgz|tlz)$', '.tar', name)
        return name
