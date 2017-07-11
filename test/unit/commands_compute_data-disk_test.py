from .test_helper import argv_kiwi_tests

import sys
import mock
from mock import patch
import azurectl
import importlib
from pytest import raises

from azurectl.azurectl_exceptions import AzureInvalidCommand


class TestComputeDataDiskTask:
    def setup(self):
        data_disk = importlib.import_module(
            'azurectl.commands.compute_data-disk'
        )
        # instantiate the command task
        sys.argv = [
            sys.argv[0], '--config', '../data/config',
            '--storage-container', 'foo',
            'compute', 'data-disk', 'help'
        ]
        self.task = data_disk.ComputeDataDiskTask()
        self.task.request_wait = mock.Mock()
        # mock out the DataDisk class the commands interface with
        disk = mock.Mock()
        disk.attached_lun = 0
        data_disk.DataDisk = mock.Mock(
            return_value=disk
        )
        # mock out the help class
        data_disk.Help = mock.Mock(
            return_value=mock.Mock()
        )
        # mock out the output class
        data_disk.DataOutput = mock.Mock(
            return_value=mock.Mock()
        )
        # variables used in multiple tests
        self.cloud_service_name = 'mockcloudservice'
        self.instance_name = 'mockcloudserviceinstance1'
        self.lun = disk.attached_lun
        self.cache_method = 'ReadWrite'
        self.disk_filename = 'mockcloudserviceinstance1-data-disk-0.vhd'
        self.disk_name = 'mockcloudserviceinstance1-data-disk-0'
        self.disk_url = ('https://foo/bar/' + self.disk_filename)
        self.disk_label = 'Mock data disk'
        self.disk_size = 42

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def __init_command_args(self, overrides=None):
        '''
            Provide an empty set of command arguments to be customized in tests
        '''
        command_args = {
            'create': False,
            'delete': False,
            'attach': False,
            'detach': False,
            'show': False,
            'list': False,
            'help': False,
            'attached': False,
            '--cloud-service-name': None,
            '--size': None,
            '--instance-name': None,
            '--disk-basename': None,
            '--label': None,
            '--disk-name': None,
            '--blob-name': None,
            '--lun': None,
            '--no-cache': False,
            '--read-only-cache': False,
            '--read-write-cache': False,
            '--wait': True
        }
        if overrides:
            command_args.update(overrides)
        self.task.command_args = command_args

    def test_help(self):
        # given
        self.__init_command_args({
            'help': True
        })
        # when
        self.task.process()
        # then
        self.task.manual.show.assert_called_once_with(
            'azurectl::compute::data_disk'
        )

    def test_create(self):
        # given
        self.__init_command_args({
            'create': True,
            '--disk-basename': self.cloud_service_name,
            '--size': self.disk_size,
            '--label': 'some-label'
        })
        # when
        self.task.process()
        # then
        self.task.data_disk.create.assert_called_once_with(
            self.cloud_service_name,
            self.disk_size,
            self.task.command_args['--label']
        )

    def test_attach(self):
        # given
        self.__init_command_args({
            'attach': True,
            '--cloud-service-name': self.cloud_service_name,
            '--instance-name': self.instance_name,
            '--label': self.disk_label,
            '--disk-name': self.disk_name,
            '--lun': format(self.lun)
        })
        # when
        self.task.process()
        # then
        self.task.data_disk.attach.assert_called_once_with(
            self.disk_name,
            self.cloud_service_name,
            self.instance_name,
            label=self.disk_label,
            lun=self.lun
        )

    def test_attach_with_blob_name(self):
        self.__init_command_args({
            'attach': True,
            '--cloud-service-name': self.cloud_service_name,
            '--instance-name': self.instance_name,
            '--label': self.disk_label,
            '--blob-name': self.disk_filename,
            '--lun': format(self.lun)
        })
        # when
        self.task.process()
        # then
        self.task.data_disk.attach.assert_called_once_with(
            None,
            self.cloud_service_name,
            self.instance_name,
            label=self.disk_label,
            lun=self.lun,
            blob_name=self.disk_filename
        )

    def test_attach_with_disk_name_and_blob_name(self):
        self.__init_command_args({
            'attach': True,
            '--cloud-service-name': self.cloud_service_name,
            '--instance-name': self.instance_name,
            '--label': self.disk_label,
            '--disk-name': self.disk_name,
            '--blob-name': self.disk_filename,
            '--lun': format(self.lun)
        })
        # when
        self.task.process()
        # then
        self.task.data_disk.attach.assert_called_once_with(
            self.disk_name,
            self.cloud_service_name,
            self.instance_name,
            label=self.disk_label,
            lun=self.lun,
            blob_name=self.disk_filename
        )

    def test_disk_name_or_blob_name_is_required(self):
        self.__init_command_args({
            'attach': True,
            '--cloud-service-name': self.cloud_service_name,
            '--instance-name': self.instance_name,
            '--label': self.disk_label,
            '--lun': format(self.lun)
        })
        with raises(AzureInvalidCommand):
            self.task.process()

    def test_attach_with_cache_method(self):
        sets = [
            ['--no-cache', 'None'],
            ['--read-only-cache', 'ReadOnly'],
            ['--read-write-cache', 'ReadWrite']
        ]
        for cache_method_arg, host_caching in sets:
            self.__check_attach_with_cache_method(
                cache_method_arg, host_caching
            )

    def test_detach(self):
        # given
        self.__init_command_args({
            'detach': True,
            '--cloud-service-name': self.cloud_service_name,
            '--instance-name': self.instance_name,
            '--lun': self.lun
        })
        # when
        self.task.process()
        # then
        self.task.data_disk.detach.assert_called_once_with(
            self.lun, self.cloud_service_name, self.instance_name
        )

    def test_show(self):
        # given
        self.__init_command_args({
            'show': True,
            '--disk-name': self.disk_name
        })
        # when
        self.task.process()
        # then
        self.task.data_disk.show.assert_called_once_with(
            self.disk_name
        )

    def test_show_attached(self):
        # given
        self.__init_command_args({
            'show': True,
            'attached': True,
            '--cloud-service-name': self.cloud_service_name,
            '--instance-name': self.instance_name,
            '--lun': self.lun
        })
        # when
        self.task.process()
        # then
        self.task.data_disk.show_attached.assert_called_once_with(
            self.cloud_service_name, self.instance_name, self.lun
        )

    def test_delete(self):
        # given
        self.__init_command_args({
            'delete': True,
            '--disk-name': self.disk_name
        })
        # when
        self.task.process()
        # then
        self.task.data_disk.delete.assert_called_once_with(
            self.disk_name
        )

    def test_list(self):
        # given
        self.__init_command_args({'list': True})
        # when
        self.task.process()
        # then
        self.task.data_disk.list.assert_called_once_with()

    def __check_attach_with_cache_method(self, cache_method_arg, host_caching):
        # given
        self.__init_command_args({
            'attach': True,
            '--cloud-service-name': self.cloud_service_name,
            '--instance-name': self.instance_name,
            '--disk-name': self.disk_name,
        })
        self.task.command_args[cache_method_arg] = True
        # when
        self.task.process()
        # then
        self.task.data_disk.attach.assert_called_with(
            self.disk_name,
            self.cloud_service_name,
            self.instance_name,
            host_caching=host_caching
        )
