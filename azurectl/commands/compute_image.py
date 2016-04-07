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
usage: azurectl compute image -h | --help
       azurectl compute image list
       azurectl compute image show --name=<imagename>
       azurectl compute image create --name=<imagename> --blob=<blobname>
           [--label=<imagelabel>]
       azurectl compute image delete --name=<imagename>
           [--delete-disk]
       azurectl compute image replicate --name=<imagename> --regions=<regionlist> --offer=<offer> --sku=<sku> --image-version=<version>
           [--wait]
           [--quiet]
       azurectl compute image replication-status --name=<imagename>
       azurectl compute image unreplicate --name=<imagename>
       azurectl compute image update --name=<imagename>
           [--description=<description>]
           [--eula=<eula>]
           [--image-family=<image_family>]
           [--icon-uri=<icon_uri>]
           [--label=<label>]
           [--language=<language>]
           [--privacy-uri=<privacy_uri>]
           [--published-date=<date>]
           [--small-icon-uri=<small_icon_uri>]
       azurectl compute image publish --name=<imagename>
           [--private]
           [--msdn]
       azurectl compute image help

commands:
    list
        list available os images for configured account
    show
        list information about a single image
    create
        create OS image from VHD disk stored on blob storage container
    delete
        delete OS image from VM image repository
    replicate
        replicate registered VM image to specified regions
    replication-status
        show which regions an image is replicated to, and the status of
        replication, as a percentage of the image data being replicated
    unreplicate
        unreplicate registered VM image from specified regions
    update
        update OS image meta data
    publish
        publish registered VM image
    help
        show manual page for image command

options:
    --delete-disk
        on deletion of the image also delete the associated VHD disk
    --label=<imagelabel>
        image label on create, defaults to name if not set
    --name=<imagename>
        image name on create
    --blob=<blobname>
        filename of disk image as it is stored on the blob storage
    --regions=<regionlist>
        comma separated list of region names. If the region name 'all'
        is provided, azurectl will replicate to all regions that are
        valid for your subscription
    --offer=<offer>
        name of the offer
    --sku=<sku>
        name of the sku
    --image-version=<version>
        semantic version of the image
    --wait
        wait until replication is complete to end execution
    --quiet
        suppress progress information during replication
    --private
        restrict publish scope to be private
    --msdn
        restrict publish scope to the Microsoft Developer Network
"""
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc

# project
from ..logger import log
from base import CliTask
from ..account.service import AzureAccount
from ..utils.collector import DataCollector
from ..utils.output import DataOutput
from ..image import Image
from ..help import Help


class ComputeImageTask(CliTask):
    """
        Process image commands
    """
    def process(self):
        self.manual = Help()
        if self.__help():
            return

        self.result = DataCollector()
        self.out = DataOutput(
            self.result,
            self.global_args['--output-format'],
            self.global_args['--output-style']
        )

        self.load_config()

        self.account = AzureAccount(self.config)

        self.image = Image(self.account)
        if self.command_args['list']:
            self.__list()
        if self.command_args['show']:
            self.__show()
        elif self.command_args['create']:
            self.__create()
        elif self.command_args['delete']:
            self.__delete()
        elif self.command_args['replicate']:
            self.__replicate()
        elif self.command_args['replication-status']:
            self.__replication_status(self.command_args['--name'])
        elif self.command_args['unreplicate']:
            self.__unreplicate()
        elif self.command_args['publish']:
            self.__publish()
        elif self.command_args['update']:
            self.__update()

    def __help(self):
        if self.command_args['help']:
            self.manual.show('azurectl::compute::image')
        else:
            return False
        return self.manual

    def __create(self):
        self.result.add(
            'image:' + self.command_args['--name'],
            self.image.create(
                self.command_args['--name'],
                self.command_args['--blob'],
                self.command_args['--label'],
                self.account.storage_container()
            )
        )
        self.out.display()

    def __delete(self):
        self.result.add(
            'image:' + self.command_args['--name'],
            self.image.delete(
                self.command_args['--name'],
                self.command_args['--delete-disk'],
            )
        )
        self.out.display()

    def __list(self):
        self.result.add('images', self.image.list())
        self.out.display()

    def __show(self):
        self.result.add('image', self.image.show(self.command_args['--name']))
        self.out.display()

    def __replicate(self):
        image_name = self.command_args['--name']
        self.result.add(
            'replicate:' +
            self.command_args['--name'] + ':' + self.command_args['--regions'],
            self.image.replicate(
                image_name,
                self.command_args['--regions'].split(','),
                self.command_args['--offer'],
                self.command_args['--sku'],
                self.command_args['--image-version']
            )
        )
        if not self.command_args['--quiet']:
            self.out.display()
        if self.command_args['--wait']:
            if not self.command_args['--quiet']:
                progress = BackgroundScheduler(timezone=utc)
                progress.add_job(
                    lambda: self.image.print_replication_status(image_name),
                    'interval',
                    minutes=5
                )
            progress.start()
            try:
                self.image.wait_for_replication_completion(image_name)
                self.image.print_replication_status(image_name)
            except KeyboardInterrupt:
                raise SystemExit('azurectl aborted by keyboard interrupt')
            finally:
                progress.shutdown()
        if not self.command_args['--quiet']:
            print
            log.info('Replicated %s', image_name)

    def __replication_status(self, image_name):
        self.result.add(
            'replication-status:' + image_name,
            self.image.replication_status(image_name)
        )
        self.out.display()

    def __unreplicate(self):
        self.result.add(
            'unreplicate:' + self.command_args['--name'],
            self.image.unreplicate(
                self.command_args['--name']
            )
        )
        self.out.display()

    def __publish(self):
        scope = 'public'
        if self.command_args['--private']:
            scope = 'private'
        elif self.command_args['--msdn']:
            scope = 'msdn'
        self.result.add(
            'publish:' + self.command_args['--name'],
            self.image.publish(
                self.command_args['--name'],
                scope
            )
        )
        self.out.display()

    def __update(self):
        log.info(
            'Updating image metadata for: %s', self.command_args['--name']
        )
        update_elements = {
            'description':
                self.command_args['--description'],
            'eula':
                self.command_args['--eula'],
            'image_family':
                self.command_args['--image-family'],
            'icon_uri':
                self.command_args['--icon-uri'],
            'label':
                self.command_args['--label'],
            'language':
                self.command_args['--language'],
            'privacy_uri':
                self.command_args['--privacy-uri'],
            'published_date':
                self.command_args['--published-date'],
            'small_icon_uri':
                self.command_args['--small-icon-uri']
        }
        for name, value in update_elements.iteritems():
            if value is not None:
                log.info('--> %s = %s', name, value)
        self.image.update(
            self.command_args['--name'], update_elements
        )
