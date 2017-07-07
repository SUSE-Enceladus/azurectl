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
import collections
import dateutil.parser
import os
import time
from azure.storage.blob.baseblobservice import BaseBlobService

# project
from azurectl.azurectl_exceptions import (
    AzureOsImageDetailsShowError,
    AzureOsImageListError,
    AzureOsImageShowError,
    AzureBlobServicePropertyError,
    AzureOsImageCreateError,
    AzureOsImageDeleteError,
    AzureOsImageReplicateError,
    AzureOsImageUnReplicateError,
    AzureOsImagePublishError,
    AzureOsImageUpdateError
)
from azurectl.defaults import Defaults
from azurectl.logger import log


class Image(object):
    """
        Implements Azure image management from a previously uploaded
        vhd disk image file. This includes the following task
        + creation and deletion of VM images
        + replication of VM images to multiple regions
        + listing VM images
        + publish VM images
    """
    def __init__(self, account):
        self.account = account
        self.service = self.account.get_management_service()
        self.sleep_between_requests = 120
        self.max_failures = 5
        self.cached_replication_status = None

    def list(self):
        result = []
        try:
            for image in self.service.list_os_images():
                result.append(self.__decorate_image_for_results(image))
        except Exception as e:
            raise AzureOsImageListError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        return result

    def show(self, name):
        try:
            image = self.service.get_os_image(name)
        except Exception as e:
            raise AzureOsImageShowError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        return self.__decorate_image_for_results(image)

    def create(self, name, blob_name, label=None, container_name=None):
        if not container_name:
            container_name = self.account.storage_container()
        if not label:
            label = name
        try:
            storage = BaseBlobService(
                self.account.storage_name(),
                self.account.storage_key(),
                endpoint_suffix=self.account.get_blob_service_host_base()
            )
            storage.get_blob_properties(
                container_name, blob_name
            )
        except Exception as e:
            raise AzureBlobServicePropertyError(
                '%s not found in container %s' % (blob_name, container_name)
            )
        try:
            media_link = storage.make_blob_url(container_name, blob_name)
            result = self.service.add_os_image(
                label, media_link, name, 'Linux'
            )
            return (result.request_id)
        except Exception as e:
            raise AzureOsImageCreateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def delete(self, name, delete_disk=False):
        try:
            result = self.service.delete_os_image(
                name, delete_disk
            )
            return(result.request_id)
        except Exception as e:
            raise AzureOsImageDeleteError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def update(self, image_name, update_record):
        try:
            os_image = self.service.get_os_image(image_name)
        except Exception as e:
            raise AzureOsImageUpdateError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        self.__decorate_os_image_attributes_for_update(
            os_image, update_record
        )
        try:
            self.service.update_os_image_from_image_reference(
                image_name, os_image
            )
            os_image_updated = self.service.get_os_image(
                image_name
            )
        except Exception as e:
            raise AzureOsImageUpdateError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        elements_not_changed = []
        for name in sorted(update_record.keys()):
            value_desired = Defaults.get_attribute(os_image, name)
            value_current = Defaults.get_attribute(os_image_updated, name)
            if '_uri' in name:
                # Use normalized paths to compare, avoids false positives
                value_desired = os.path.normpath(value_desired)
                value_current = os.path.normpath(value_current)
            if value_desired != value_current:
                elements_not_changed.append(name)
        if elements_not_changed:
            message = [
                'The element(s) "%s" could not be updated.' %
                ','.join(elements_not_changed),
                'Please check if your account is registered as image publisher'
            ]
            raise AzureOsImageUpdateError(
                ' '.join(message)
            )

    def replicate(self, name, regions, offer, sku, version):
        '''
        Note: The regions are not additive. If a VM Image has already
        been replicated to Regions A, B, and C, and a request is made
        to replicate to Regions A and D, the VM Image will remain in
        Region A, will be replicated in Region D, and will be
        unreplicated from Regions B and C
        '''
        if 'all' in regions:
            regions = []
            for location in self.service.list_locations():
                regions.append(location.name)
        try:
            result = self.service.replicate_vm_image(
                name, regions, offer, sku, version
            )
            return(result.request_id)
        except Exception as e:
            raise AzureOsImageReplicateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def replication_status(self, name):
        try:
            image_details = self.service.get_os_image_details(name)
        except Exception as e:
            raise AzureOsImageDetailsShowError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        self.cached_replication_status = \
            image_details.replication_progress.replication_progress_elements

        results = []
        for element in image_details.replication_progress:
            results.append(
                self.__decorate_replication_progress_element(element)
            )
        return results

    def print_replication_status(self, name):
        if not self.cached_replication_status:
            self.replication_status(name)
        cumulative_progress = 0
        for element in self.cached_replication_status:
            cumulative_progress += element.progress
        log.progress(
            cumulative_progress,
            len(self.cached_replication_status) * 100,
            'Replicating'
        )

    def wait_for_replication_completion(self, name):
        failures = 0
        complete = False
        while not complete:
            try:
                time.sleep(self.sleep_between_requests)
                complete = self.__replication_is_complete(
                    self.replication_status(name)
                )
                failures = 0
            except Exception as e:
                if failures >= self.max_failures:
                    raise AzureOsImageDetailsShowError(
                        '%s: %s' % (type(e).__name__, format(e))
                    )
                else:
                    failures += 1

    def unreplicate(self, name):
        try:
            result = self.service.unreplicate_vm_image(name)
            return(result.request_id)
        except Exception as e:
            raise AzureOsImageUnReplicateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def publish(self, name, permission):
        try:
            result = self.service.share_vm_image(name, permission)
            return(result.request_id)
        except Exception as e:
            raise AzureOsImagePublishError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def __replication_is_complete(self, status):
        """
            Based on a collection of __decorate_replication_progress_elements,
            determine if progress is 100 in all regions
        """
        return all(
            [element['replication-progress'] == '100%' for element in status]
        )

    def __convert_date_to_azure_format(self, timestring):
        """
            Convert the given date string into the format used by the Azure API
        """
        try:
            return dateutil.parser.parse(timestring).strftime(
                '%Y-%m-%dT%H:%M:%SZ'
            )
        except Exception as e:
            raise AzureOsImageUpdateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def __decorate_os_image_attributes_for_update(self, image, update_record):
        ordered_update_record = collections.OrderedDict(
            sorted(update_record.items())
        )
        for name, value in ordered_update_record.items():
            if value is not None:
                if '_date' in name:
                    value = self.__convert_date_to_azure_format(value)
                if 'show_in_gui' in name:
                    value = value.lower() in ("yes", "true", "t", "1")
                Defaults.set_attribute(image, name, value)
        return image

    def __decorate_image_for_results(self, image):
        return {
            'affinity_group': image.affinity_group,
            'category': image.category,
            'description': image.description,
            'eula': image.eula,
            'icon_uri': image.icon_uri,
            'image_family': image.image_family,
            'is_premium': image.is_premium,
            'label': image.label,
            'language': image.language,
            'location': image.location,
            'logical_size_in_gb': image.logical_size_in_gb,
            'media_link': image.media_link,
            'name': image.name,
            'os': image.os,
            'os_state': image.os_state,
            'pricing_detail_link': image.pricing_detail_link,
            'privacy_uri': image.privacy_uri,
            'published_date': image.published_date,
            'publisher_name': image.publisher_name,
            'recommended_vm_size': image.recommended_vm_size,
            'show_in_gui': image.show_in_gui,
            'small_icon_uri': image.small_icon_uri
        }

    def __decorate_replication_progress_element(self, element):
        return {
            'region': element.location,
            'replication-progress': '{}%'.format(element.progress)
        }
