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
import json
import os
from tempfile import NamedTemporaryFile

# project
from azurectl.logger import log


class DataOutput(object):
    """
        Output console data in style and format as needed
    """
    def __init__(self, data_collector, data_format='json', style='standard'):
        self.data = data_collector.get()
        self.data_format = data_format
        self.style = style
        self.color_json = self._which('pjson')

    def display(self):
        # Currently only one output format is implemented
        self._json()

    def _json(self):
        if self.style == 'color':
            if self.color_json:
                self._color_json()
            else:
                log.warning('pjson for color output not installed')
                log.warning('run: pip install pjson')
                self._standard_json()
        else:
            self._standard_json()

    def _standard_json(self):
        print(json.dumps(
            self.data, sort_keys=True, indent=2, separators=(',', ': ')
        ))

    def _color_json(self):
        out_file = NamedTemporaryFile()
        out_file.write(json.dumps(self.data, sort_keys=True))
        out_file.flush()
        pjson_cmd = ''.join(['cat ', out_file.name, '| pjson'])
        os.system(pjson_cmd)

    def _which(self, cmd):
        return any(
            os.access(os.path.join(path, cmd), os.X_OK)
            for path in os.environ["PATH"].split(os.pathsep)
        )
