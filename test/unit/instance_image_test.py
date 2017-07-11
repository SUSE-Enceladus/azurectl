from .test_helper import argv_kiwi_tests

import mock
import random
import string
import sys
from collections import namedtuple
from mock import (patch, call)
from pytest import raises
from azure.servicemanagement.models import (
    OSImageDetails,
    ReplicationProgress,
    ReplicationProgressElement
)
from azurectl.account.service import AzureAccount
from azurectl.config.parser import Config
from azurectl.instance.image import Image
import azurectl

from azurectl.azurectl_exceptions import (
    AzureBlobServicePropertyError,
    AzureOsImageCreateError,
    AzureOsImageDeleteError,
    AzureOsImageDetailsShowError,
    AzureOsImageListError,
    AzureOsImagePublishError,
    AzureOsImageReplicateError,
    AzureOsImageShowError,
    AzureOsImageUnReplicateError,
    AzureOsImageUpdateError
)


class TestImage:
    def setup(self):
        MyResult = namedtuple(
            'MyResult',
            'request_id'
        )
        self.myrequest = MyResult(request_id=42)
        self.fake_image_name = 'some-name'

        MyStruct = namedtuple(
            'MyStruct',
            'affinity_group category description eula icon_uri image_family \
             is_premium label language location logical_size_in_gb media_link \
             name os os_state pricing_detail_link privacy_uri \
             published_date publisher_name recommended_vm_size show_in_gui \
             small_icon_uri'
        )
        self.list_os_images = [MyStruct(
            affinity_group='group',
            category='cloud',
            description='nice',
            eula='eula',
            icon_uri='url',
            image_family='disks',
            is_premium=False,
            label='bob',
            language='English',
            location='West US',
            logical_size_in_gb=30,
            media_link='url',
            name=self.fake_image_name,
            os='linux',
            os_state='brilliant',
            pricing_detail_link='url',
            privacy_uri='url',
            published_date='date',
            publisher_name='suse',
            recommended_vm_size=10,
            show_in_gui=True,
            small_icon_uri='url'
        )]

        self.os_image = mock.Mock()
        self.os_image.eula = 'eula'
        self.os_image.description = 'description'
        self.os_image.language = 'en_US'
        self.os_image.image_family = 'family'
        self.os_image.icon_uri = 'OpenSuse12_100.png'
        self.os_image.label = 'label'
        self.os_image.small_icon_uri = 'OpenSuse12_45.png'
        self.os_image.published_date = '2016-01-20'
        self.os_image.privacy_uri = 'http://privacy.uri'
        self.os_image.show_in_gui = 'true'
        self.os_image.recommended_vm_size = 'large'


        self.os_image_updated = mock.Mock()
        self.os_image_updated.eula = 'eula'
        self.os_image_updated.description = 'description'
        self.os_image_updated.language = 'en_US'
        self.os_image_updated.image_family = 'family'
        self.os_image_updated.icon_uri = 'OpenSuse12_100.png'
        self.os_image_updated.label = 'label'
        self.os_image_updated.small_icon_uri = 'OpenSuse12_45.png'
        self.os_image_updated.published_date = '2016-01-20T00:00:00Z'
        self.os_image_updated.privacy_uri = 'http://privacy.uri/'
        self.os_image_updated.show_in_gui = True
        self.os_image_updated.recommended_vm_size = 'large'

        account = AzureAccount(
            Config(
                region_name='East US 2', filename='../data/config'
            )
        )
        self.service = mock.Mock()
        account.get_management_service = mock.Mock(return_value=self.service)
        account.get_blob_service_host_base = mock.Mock(
            return_value='test.url'
        )
        account.storage_key = mock.Mock()
        self.image = Image(account)

    def __fake_os_image_details(self, name, regions_and_percents=None):
        if regions_and_percents is None:
            regions_and_percents = []

        fake = OSImageDetails()
        regions_and_percents.reverse()
        while regions_and_percents:
            element = ReplicationProgressElement()
            element.location = regions_and_percents.pop()
            element.progress = regions_and_percents.pop()
            fake.replication_progress.replication_progress_elements.append(
                element
            )
        return fake

    def test_list(self):
        self.service.list_os_images.return_value = self.list_os_images
        assert self.image.list() == [self.list_os_images.pop()._asdict()]

    def test_list_raises_error(self):
        self.service.list_os_images.side_effect = Exception
        with raises(AzureOsImageListError):
            self.image.list()

    def test_show(self):
        mock_response = self.list_os_images[0]
        self.service.get_os_image.return_value = mock_response
        assert self.image.show(mock_response.name) == mock_response._asdict()

    def test_show_raises_error(self):
        mock_response = self.list_os_images[0]
        self.service.get_os_image.side_effect = Exception
        with raises(AzureOsImageShowError):
            self.image.show(mock_response.name)

    @patch('azurectl.instance.image.BaseBlobService.get_blob_properties')
    def test_create_raise_blob_error(self, mock_get_blob_props):
        mock_get_blob_props.side_effect = Exception
        with raises(AzureBlobServicePropertyError):
            self.image.create('some-name', 'some-blob')

    @patch('azurectl.instance.image.BaseBlobService.get_blob_properties')
    def test_create_raise_os_image_error(self, mock_get_blob_props):
        self.service.add_os_image.side_effect = Exception
        with raises(AzureOsImageCreateError):
            self.image.create('some-name', 'some-blob')

    @patch('azurectl.instance.image.BaseBlobService.get_blob_properties')
    def test_create(self, mock_get_blob_props):
        self.service.add_os_image.return_value = self.myrequest
        request_id = self.image.create(
            'some-name', 'some-blob'
        )
        assert request_id == 42
        self.service.add_os_image.assert_called_once_with(
            'some-name',
            'https://bob.blob.test.url/foo/some-blob',
            'some-name',
            'Linux'
        )

    def test_delete(self):
        self.service.delete_os_image.return_value = self.myrequest
        request_id = self.image.delete(
            'some-name', False
        )
        assert request_id == 42
        self.service.delete_os_image.assert_called_once_with(
            'some-name', False
        )

    def test_delete_raise_os_delete_error(self):
        self.service.delete_os_image.side_effect = Exception
        with raises(AzureOsImageDeleteError):
            self.image.delete('some-name')

    def test_replicate(self):
        location_type = namedtuple(
            'location_type', 'name'
        )
        self.service.replicate_vm_image.return_value = self.myrequest
        self.service.list_locations.return_value = [
            location_type(name='a'),
            location_type(name='b'),
            location_type(name='c')
        ]
        request_id = self.image.replicate(
            'some-name', ['all'], 'offer', 'sku', 'version'
        )
        assert request_id == 42
        self.service.replicate_vm_image.assert_called_once_with(
            'some-name', ['a', 'b', 'c'], 'offer', 'sku', 'version'
        )

    def test_replication_status(self):
        fake_details = self.__fake_os_image_details(
            self.fake_image_name,
            ['Region 1', 100, 'Region 2', 50]
        )
        self.service.get_os_image_details.return_value = fake_details
        expected_results = [
            {'region': 'Region 1', 'replication-progress': '100%'},
            {'region': 'Region 2', 'replication-progress': '50%'}
        ]
        results = self.image.replication_status(self.fake_image_name)
        self.service.get_os_image_details.assert_called_once_with(
            self.fake_image_name
        )
        assert results == expected_results

    def test_replication_status_populates_cache(self):
        fake_details = self.__fake_os_image_details(
            self.fake_image_name,
            ['Region 1', 100, 'Region 2', 50]
        )
        self.service.get_os_image_details.return_value = fake_details
        self.image.cached_replication_status = None
        self.image.replication_status(self.fake_image_name)
        self.service.get_os_image_details.assert_called_once_with(
            self.fake_image_name
        )
        assert self.image.cached_replication_status == \
            fake_details.replication_progress.replication_progress_elements

    def test_replication_status_upstream_exception(self):
        self.service.get_os_image_details.side_effect = Exception
        with raises(AzureOsImageDetailsShowError):
            results = self.image.replication_status(self.fake_image_name)

    @patch('azurectl.instance.image.log')
    def test_print_replication_status(self, mock_log):
        fake_details = self.__fake_os_image_details(
            self.fake_image_name,
            ['Region 1', 100, 'Region 2', 50]
        )
        self.image.cached_replication_status = \
            fake_details.replication_progress.replication_progress_elements
        self.image.print_replication_status(self.fake_image_name)
        mock_log.progress.assert_called_once_with(150, 200, 'Replicating')

    @patch('azurectl.instance.image.log')
    def test_print_replication_status_populates_cache(self, mock_log):
        fake_details = self.__fake_os_image_details(
            self.fake_image_name,
            ['Region 1', 100, 'Region 2', 50]
        )
        self.service.get_os_image_details.return_value = fake_details
        self.image.cached_replication_status = None
        self.image.print_replication_status(self.fake_image_name)
        self.service.get_os_image_details.assert_called_once_with(self.fake_image_name)
        assert self.image.cached_replication_status == \
            fake_details.replication_progress.replication_progress_elements

    def test_wait_for_replication_completion(self):
        self.service.get_os_image_details.side_effect = iter([
            self.__fake_os_image_details(
                self.fake_image_name,
                ['Region 1', 100, 'Region 2', 50]
            ),
            self.__fake_os_image_details(
                self.fake_image_name,
                ['Region 1', 100, 'Region 2', 100]
            )
        ])
        self.image.sleep_between_requests = 0
        self.image.wait_for_replication_completion(self.fake_image_name)
        assert self.service.get_os_image_details.call_count == 2

    def test_wait_for_replication_completion_upstream_exception(self):
        self.service.get_os_image_details.side_effect = Exception
        self.image.sleep_between_requests = 0
        self.image.max_failures = 4
        with raises(AzureOsImageDetailsShowError):
            self.image.wait_for_replication_completion(self.fake_image_name)

    def test_unreplicate(self):
        self.service.unreplicate_vm_image.return_value = self.myrequest
        request_id = self.image.unreplicate('some-name')
        assert request_id == 42
        self.service.unreplicate_vm_image.assert_called_once_with(
            'some-name'
        )

    def test_publish(self):
        self.service.share_vm_image.return_value = self.myrequest
        request_id = self.image.publish('some-name', 'public')
        assert request_id == 42
        self.service.share_vm_image.assert_called_once_with(
            'some-name', 'public'
        )

    def test_replicate_raises_error(self):
        self.service.replicate_vm_image.side_effect = AzureOsImageReplicateError
        with raises(AzureOsImageReplicateError):
            self.image.replicate(
                'some-name', 'some-regions', 'offer', 'sku', 'version'
            )

    def test_unreplicate_raises_error(self):
        self.service.unreplicate_vm_image.side_effect = \
            AzureOsImageUnReplicateError
        with raises(AzureOsImageUnReplicateError):
            self.image.unreplicate('some-name')

    def test_publish_raises_error(self):
        self.service.share_vm_image.side_effect = AzureOsImagePublishError
        with raises(AzureOsImagePublishError):
            self.image.publish('some-name', 'public')

    def test_update(self):
        get_os_image_results = [
            self.os_image_updated, self.os_image
        ]

        def side_effect(arg):
            return get_os_image_results.pop()

        self.service.get_os_image.side_effect = side_effect

        update_record = {
            'eula': self.os_image.eula,
            'description': self.os_image.description,
            'language': self.os_image.language,
            'image_family': self.os_image.image_family,
            'icon_uri': self.os_image.icon_uri,
            'label': self.os_image.label,
            'small_icon_uri': self.os_image.small_icon_uri,
            'published_date': self.os_image.published_date,
            'privacy_uri': self.os_image.privacy_uri,
            'show_in_gui': self.os_image.show_in_gui,
            'recommended_vm_size': self.os_image.recommended_vm_size
        }

        self.image.update('some-name', update_record)

        assert self.os_image.description == \
            self.os_image_updated.description
        assert self.os_image.eula == \
            self.os_image_updated.eula
        assert self.os_image.icon_uri in \
            self.os_image_updated.icon_uri
        assert self.os_image.image_family == \
            self.os_image_updated.image_family
        assert self.os_image.label == \
            self.os_image_updated.label
        assert self.os_image.language == \
            self.os_image_updated.language
        assert self.os_image.privacy_uri in \
            self.os_image_updated.privacy_uri
        assert self.os_image.published_date == \
            self.os_image_updated.published_date
        assert self.os_image.small_icon_uri in \
            self.os_image_updated.small_icon_uri
        assert self.os_image.show_in_gui == \
            self.os_image_updated.show_in_gui
        assert self.os_image.recommended_vm_size == \
            self.os_image_updated.recommended_vm_size

        self.service.update_os_image_from_image_reference.assert_called_once_with(
            'some-name', self.os_image
        )

    def test_update_raises_invalid_date_format(self):
        self.os_image.published_date = 'xxx'
        get_os_image_results = [
            self.os_image_updated, self.os_image
        ]

        def side_effect(arg):
            return get_os_image_results.pop()

        self.service.get_os_image.side_effect = side_effect
        with raises(AzureOsImageUpdateError):
            self.image.update(
                'some-name', {'published_date': self.os_image.published_date}
            )

    def test_update_raises_value_unchanged(self):
        self.os_image.description = 'a'
        self.os_image_updated.description = 'b'
        get_os_image_results = [
            self.os_image_updated, self.os_image
        ]

        def side_effect(arg):
            return get_os_image_results.pop()

        self.service.get_os_image.side_effect = side_effect
        with raises(AzureOsImageUpdateError):
            self.image.update(
                'some-name', {'description': self.os_image.description}
            )

    def test_update_raises_image_metadata_request_failed(self):
        self.service.get_os_image.side_effect = Exception
        with raises(AzureOsImageUpdateError):
            self.image.update('some-name', {})

    def test_update_raises_on_update_os_image_from_image_reference(self):
        self.service.update_os_image_from_image_reference.side_effect = \
            Exception
        with raises(AzureOsImageUpdateError):
            self.image.update('some-name', {})
