# Copyright (c) 2016 SUSE.  All rights reserved.
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
from azure.common import AzureMissingResourceHttpError
from azure.storage.blob.pageblobservice import PageBlobService
from datetime import datetime
from builtins import bytes
from uuid import uuid4

# project
from azurectl.defaults import Defaults
from azurectl.storage.storage import Storage

from azurectl.azurectl_exceptions import (
    AzureDataDiskAttachError,
    AzureDataDiskCreateError,
    AzureDataDiskShowError,
    AzureDataDiskDeleteError,
    AzureDataDiskNoAvailableLun
)


class DataDisk(object):
    """
        Implements virtual machine data disk (non-root/boot disk) management.
    """
    def __init__(self, account):
        self.account = account
        self.service = account.get_management_service()
        self.data_disk_name = None

    def create(self, identifier, disk_size_in_gb, label=None):
        """
            Create new data disk
        """
        footer = self.__generate_vhd_footer(disk_size_in_gb)
        disk_name = self.__generate_filename(identifier)
        size_in_bytes = int(disk_size_in_gb) * 1073741824 + 512
        try:
            storage = Storage(
                self.account, self.account.storage_container()
            )
            storage.upload_empty_image(size_in_bytes, footer, disk_name)
        except Exception as e:
            raise AzureDataDiskCreateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

        disk_url = self.__data_disk_url(disk_name)
        args = {
            'media_link': disk_url,
            'name': self.__strip_platform_extension(disk_name),
            'has_operating_system': False,
            'os': 'Linux'
        }
        args['label'] = label if label else identifier

        try:
            self.service.add_disk(**args)
        except Exception as e:
            raise AzureDataDiskCreateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def show(self, disk_name):
        """
            Show details of the specified disk
        """
        try:
            disk = self.service.get_disk(disk_name)
        except Exception as e:
            raise AzureDataDiskShowError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        return self.__decorate_disk(disk)

    def delete(self, disk_name):
        """
            Delete data disk and the underlying vhd disk image
            Note the deletion will fail if the disk is still
            in use, meaning attached to an instance
        """
        try:
            self.service.delete_disk(disk_name, delete_vhd=True)
        except Exception as e:
            raise AzureDataDiskDeleteError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def list(self):
        """
            List disk(s) from your image repository
        """
        disks = []
        try:
            disks = self.service.list_disks()
        except Exception:
            pass
        return [
            self.__decorate_disk_list(disk) for disk in disks
        ]

    def show_attached(
        self, cloud_service_name, instance_name=None, at_lun=None
    ):
        """
            Show details of the data disks attached to the virtual
            machine. If a lun is specified show only details for the disk
            at the specified lun
        """
        if not instance_name:
            instance_name = cloud_service_name

        disks = []
        luns = [at_lun] if at_lun is not None else list(range(Defaults.max_vm_luns()))
        for lun in luns:
            try:
                disks.append(self.service.get_data_disk(
                    cloud_service_name, cloud_service_name, instance_name, lun
                ))
            except Exception as e:
                if at_lun is not None:
                    # only if a disk information is requested for a specific
                    # lun but does not exist, an exception is raised
                    raise AzureDataDiskShowError(
                        '%s: %s' % (type(e).__name__, format(e))
                    )
        return [self.__decorate_attached_disk(disk) for disk in disks]

    def attach(
        self, disk_name, cloud_service_name, instance_name=None,
        label=None, lun=None, host_caching=None, blob_name=None
    ):
        """
            Attach existing data disk to the instance
        """
        if not instance_name:
            instance_name = cloud_service_name

        if lun not in list(range(Defaults.max_vm_luns())):
            lun = self.__get_first_available_lun(
                cloud_service_name, instance_name
            )

        if disk_name and not blob_name:
            # assume existing data-disk
            args = {
                'disk_name': disk_name
            }
        elif disk_name and blob_name:
            # create new data-disk based using disk_name
            args = {
                'disk_name': disk_name,
                'source_media_link': self.__data_disk_url(blob_name)
            }
        elif not disk_name and blob_name:
            # find data-disk name for blob_name,
            # or create a new data-disk for blob_name
            disk_name = self.__find_existing_disk_name_for_blob_name(
                blob_name,
                self.service.list_disks()
            )
            if disk_name:
                args = {
                    'disk_name': disk_name
                }
            else:
                args = {
                    'disk_name': self.__strip_platform_extension(blob_name),
                    'source_media_link': self.__data_disk_url(blob_name)
                }
        else:
            raise AzureDataDiskAttachError(
                "Neither disk_name nor blob_name was supplied"
            )

        if host_caching:
            args['host_caching'] = host_caching
        if label:
            args['disk_label'] = label

        try:
            result = self.service.add_data_disk(
                cloud_service_name, cloud_service_name, instance_name, lun,
                **args
            )
            self.attached_lun = lun
        except Exception as e:
            raise AzureDataDiskAttachError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        return result.request_id

    def detach(self, lun, cloud_service_name, instance_name=None):
        """
            Delete data disk from the instance, retaining underlying vhd blob
        """
        if not instance_name:
            instance_name = cloud_service_name

        try:
            result = self.service.delete_data_disk(
                cloud_service_name, cloud_service_name, instance_name, lun,
                delete_vhd=False
            )
        except Exception as e:
            raise AzureDataDiskDeleteError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        return result.request_id

    def __get_first_available_lun(self, cloud_service_name, instance_name):
        lun = 0
        while lun < Defaults.max_vm_luns():
            try:
                self.service.get_data_disk(
                    cloud_service_name, cloud_service_name, instance_name, lun
                )
            except AzureMissingResourceHttpError:
                return lun
            else:
                lun += 1
        raise AzureDataDiskNoAvailableLun(
            "All LUNs on this VM are occupied."
        )

    def __generate_filename(self, identifier):
        """
            Generate vhd disk name with respect to the Azure naming
            conventions for data disks
        """
        self.data_disk_name = '%s-data-disk-%s.vhd' % (
            identifier, datetime.isoformat(datetime.utcnow()).replace(':', '_')
        )
        return self.data_disk_name

    def __data_disk_url(self, filename):
        blob_service = PageBlobService(
            self.account.storage_name(),
            self.account.storage_key(),
            endpoint_suffix=self.account.get_blob_service_host_base()
        )
        return blob_service.make_blob_url(
            self.account.storage_container(),
            filename
        )

    def __strip_platform_extension(self, name):
        extensions = ['.vhd', '.vhdfixed']

        for extension in extensions:
            if name.endswith(extension):
                return name[:-len(extension)]

    def __find_existing_disk_name_for_blob_name(self, blob_name, disks):
        """
            if a data-disk object exists for the given blob name, find it;
            if not, return None as a signal to generate one.
        """
        disk_url = self.__data_disk_url(blob_name)
        for disk in disks:
            if disk.media_link == disk_url:
                return disk.name
        return None

    def __decorate_attached_disk(self, data_virtual_hard_disk):
        return {
            'label': data_virtual_hard_disk.disk_label,
            'host-caching': data_virtual_hard_disk.host_caching,
            'disk-url': data_virtual_hard_disk.media_link,
            'source-image-url': data_virtual_hard_disk.source_media_link,
            'lun': data_virtual_hard_disk.lun,
            'size': '%d GB' % data_virtual_hard_disk.logical_disk_size_in_gb
        }

    def __decorate_disk(self, disk):
        attach_info = {}
        if disk.attached_to:
            attach_info = {
                'hosted_service_name': disk.attached_to.hosted_service_name,
                'deployment_name': disk.attached_to.deployment_name,
                'role_name': disk.attached_to.role_name
            }
        return {
            'affinity_group': disk.affinity_group,
            'attached_to': attach_info,
            'has_operating_system': disk.has_operating_system,
            'is_corrupted': disk.is_corrupted,
            'location': disk.location,
            'logical_disk_size_in_gb': '%d GB' % disk.logical_disk_size_in_gb,
            'label': disk.label,
            'media_link': disk.media_link,
            'name': disk.name,
            'os': disk.os,
            'source_image_name': disk.source_image_name
        }

    def __decorate_disk_list(self, disk):
        attached = True if disk.attached_to else False
        return {
            'is_attached': attached,
            'name': disk.name,
        }

    def __generate_vhd_footer(self, disk_size_in_gb):
        """
        Kudos to Steven Edouard: https://gist.github.com/sedouard
        who provided the following:

        Generate an empty vhd fixed disk of the specified size.
        The file must be conform to the VHD Footer Format Specification at
        https://technet.microsoft.com/en-us/virtualization/bb676673.aspx#E3B
        which specifies the data structure as follows:
        * Field         Size (bytes)
        * Cookie        8
        * Features      4
        * Version       4
        * Data Offset   4
        * TimeStamp     4
        * Creator App   4
        * Creator Ver   4
        * CreatorHostOS 4
        * Original Size 8
        * Current Size  8
        * Disk Geo      4
        * Disk Type     4
        * Checksum      4
        * Unique ID     16
        * Saved State   1
        * Reserved      427
        """
        # disk size in bytes
        byte_size = int(disk_size_in_gb) * 1073741824
        # the ascii string 'conectix'
        cookie = bytearray(
            [0x63, 0x6f, 0x6e, 0x65, 0x63, 0x74, 0x69, 0x78]
        )
        # no features enabled
        features = bytearray(
            [0x00, 0x00, 0x00, 0x02]
        )
        # current file version
        version = bytearray(
            [0x00, 0x01, 0x00, 0x00]
        )
        # in the case of a fixed disk, this is set to -1
        data_offset = bytearray(
            [0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
        )
        # hex representation of seconds since january 1st 2000
        timestamp = bytearray.fromhex(
            hex(int(datetime.now().strftime('%s')) - 946684800).replace(
                'L', ''
            ).replace('0x', '').zfill(8))
        # ascii code for 'wa' = windowsazure
        creator_app = bytearray(
            [0x77, 0x61, 0x00, 0x00]
        )
        # ascii code for version of creator application
        creator_version = bytearray(
            [0x00, 0x07, 0x00, 0x00]
        )
        # creator host os. windows or mac, ascii for 'wi2k'
        creator_os = bytearray(
            [0x57, 0x69, 0x32, 0x6b]
        )
        original_size = bytearray.fromhex(
            hex(byte_size).replace('0x', '').zfill(16)
        )
        current_size = bytearray.fromhex(
            hex(byte_size).replace('0x', '').zfill(16)
        )
        # 0x820=2080 cylenders, 0x10=16 heads, 0x3f=63 sectors/track
        disk_geometry = bytearray(
            [0x08, 0x20, 0x10, 0x3f]
        )
        # 0x2 = fixed hard disk
        disk_type = bytearray(
            [0x00, 0x00, 0x00, 0x02]
        )
        # a uuid
        unique_id = bytearray.fromhex(uuid4().hex)
        # saved state and reserved
        saved_reserved = bytearray(428)
        # Compute Checksum with Checksum = ones compliment of sum of
        # all fields excluding the checksum field
        to_checksum_array = \
            cookie + features + version + data_offset + \
            timestamp + creator_app + creator_version + \
            creator_os + original_size + current_size + \
            disk_geometry + disk_type + unique_id + saved_reserved

        total = 0
        for b in to_checksum_array:
            total += b
        total = ~total

        # handle two's compliment
        def tohex(val, nbits):
            return hex((val + (1 << nbits)) % (1 << nbits))

        checksum = bytearray.fromhex(
            tohex(total, 32).replace('0x', '')
        )

        # vhd disk blob
        blob_data = \
            cookie + features + version + data_offset + \
            timestamp + creator_app + creator_version + \
            creator_os + original_size + current_size + \
            disk_geometry + disk_type + checksum + unique_id + saved_reserved
        return bytes(blob_data)
