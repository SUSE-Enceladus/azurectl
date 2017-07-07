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
"""
In order to make use of a disk image in Azure, a fixed-size virtual hard disk
(VHD) file must be uploaded to storage as a page blob.

usage: azurectl storage disk -h | --help
       azurectl storage disk upload --source=<file>
           [--blob-name=<blobname>]
           [--max-chunk-size=<size>]
           [--quiet]
       azurectl storage disk sas --blob-name=<blobname>
           [--start-datetime=<start>]
           [--expiry-datetime=<expiry>]
           [--permissions=<permissions>]
       azurectl storage disk delete --blob-name=<blobname>
       azurectl storage disk help

commands:
    delete
        delete disk image from the given container
    help
        show manual page for disk command
    sas
        generate a shared access signature URL allowing limited access to the
        specified disk image without an access key
    upload
        upload xz compressed disk image to the given container
        (will automatically skip zero'd blocks)

options:
    --blob-name=<blobname>
        name of the file in the storage pool
    --expiry-datetime=<expiry>
        Date (and optionally time) to cease access via a shared access
        signature. [default: 30 days from start]
        Example format: YYYY-MM-DDThh:mm:ssZ
    --max-chunk-size=<size>
        max chunk size in bytes for upload, default 4MB
    --permissions=<permissions>
        String of permitted actions on a storage element via shared access
        signature.
        r  Read
        w  Write
        d  Delete
        l  List
        [default: rl]
    --quiet
        suppress progress information on upload
    --source=<file>
        file to upload
    --start-datetime=<start>
        Date (and optionally time) to grant access via a shared access
        signature. [default: now]
        Example format: YYYY-MM-DDThh:mm:ssZ
"""
import datetime
from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler

# project
from .base import CliTask
from azurectl.account.service import AzureAccount
from azurectl.help import Help
from azurectl.logger import log
from azurectl.storage.storage import Storage
from azurectl.utils.collector import DataCollector
from azurectl.utils.output import DataOutput


class StorageDiskTask(CliTask):
    """
        Process disk commands
    """
    def process(self):
        self.manual = Help()
        if self.__help():
            return

        self.load_config()

        self.account = AzureAccount(self.config)

        container_name = self.account.storage_container()

        self.storage = Storage(
            self.account, container_name
        )

        # default to 1 minute ago (skew around 'now')
        if self.command_args['--start-datetime'] == 'now':
            start = datetime.datetime.utcnow() - datetime.timedelta(minutes=1)
        else:
            start = self.validate_date('--start-datetime')

        # default to 30 days from now
        if self.command_args['--expiry-datetime'] == '30 days from start':
            expiry = start + datetime.timedelta(days=30)
        else:
            expiry = self.validate_date('--expiry-datetime')

        self.validate_sas_permissions('--permissions')

        if self.command_args['upload']:
            self.__upload()
        elif self.command_args['delete']:
            self.__delete()
        elif self.command_args['sas']:
            self.__sas(
                container_name,
                start,
                expiry,
                self.command_args['--permissions']
            )

    def __help(self):
        if self.command_args['help']:
            self.manual.show('azurectl::storage::disk')
        else:
            return False
        return self.manual

    def __upload(self):
        if self.command_args['--quiet']:
            self.__upload_no_progress()
        else:
            self.__upload_with_progress()

    def __upload_no_progress(self):
        try:
            self.__process_upload()
        except (KeyboardInterrupt):
            raise SystemExit('azurectl aborted by keyboard interrupt')

    def __upload_with_progress(self):
        image = self.command_args['--source']
        progress = BackgroundScheduler(timezone=utc)
        progress.add_job(
            self.storage.print_upload_status, 'interval', seconds=3
        )
        progress.start()
        try:
            self.__process_upload()
            self.storage.print_upload_status()
            progress.shutdown()
        except (KeyboardInterrupt):
            progress.shutdown()
            raise SystemExit('azurectl aborted by keyboard interrupt')
        print()
        log.info('Uploaded %s', image)

    def __process_upload(self):
        self.storage.upload(

            self.command_args['--source'],
            self.command_args['--blob-name'],
            self.command_args['--max-chunk-size']
        )

    def __sas(self, container_name, start, expiry, permissions):
        result = DataCollector()
        out = DataOutput(
            result,
            self.global_args['--output-format'],
            self.global_args['--output-style']
        )

        result.add(
            self.command_args['--blob-name'] + ':sas_url',
            self.storage.disk_image_sas(
                container_name,
                self.command_args['--blob-name'],
                start,
                expiry,
                permissions
            )
        )
        out.display()

    def __delete(self):
        image = self.command_args['--blob-name']
        self.storage.delete(image)
        log.info('Deleted %s', image)
