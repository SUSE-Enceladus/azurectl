from .test_helper import argv_kiwi_tests

import sys
import mock
from mock import patch
from mock import call
import azurectl
from azurectl.commands.compute_vm import ComputeVmTask


class TestComputeVmTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], '--config', '../data/config',
            'compute', 'vm', 'delete', '--cloud-service-name', 'cloudservice',
            '--instance-name', 'foo'
        ]
        self.task = ComputeVmTask()
        self.task.request_wait = mock.Mock()
        vm = mock.Mock()
        vm.create_network_configuration = mock.Mock(
            return_value={}
        )
        vm.create_linux_configuration = mock.Mock(
            return_value={}
        )
        azurectl.commands.compute_vm.VirtualMachine = mock.Mock(
            return_value=vm
        )
        cloud_service = mock.Mock()
        cloud_service.create = mock.Mock(
            return_value=42
        )
        azurectl.commands.compute_vm.CloudService = mock.Mock(
            return_value=cloud_service
        )
        azurectl.commands.compute_vm.Help = mock.Mock(
            return_value=mock.Mock()
        )
        azurectl.commands.compute_vm.AzureAccount = mock.Mock(
            return_value=mock.Mock()
        )

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def __init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['--cloud-service-name'] = 'cloudservice'
        self.task.command_args['--image-name'] = 'image'
        self.task.command_args['--instance-name'] = None
        self.task.command_args['--custom-data'] = None
        self.task.command_args['--instance-type'] = None
        self.task.command_args['--label'] = None
        self.task.command_args['--password'] = None
        self.task.command_args['--reserved-ip-name'] = None
        self.task.command_args['--ssh-private-key-file'] = '../data/id_test'
        self.task.command_args['--fingerprint'] = None
        self.task.command_args['--ssh-port'] = None
        self.task.command_args['--user'] = None
        self.task.command_args['--wait'] = True
        self.task.command_args['--deallocate-resources'] = True
        self.task.command_args['create'] = False
        self.task.command_args['delete'] = False
        self.task.command_args['reboot'] = False
        self.task.command_args['shutdown'] = False
        self.task.command_args['start'] = False
        self.task.command_args['regions'] = False
        self.task.command_args['types'] = False
        self.task.command_args['status'] = False
        self.task.command_args['show'] = False
        self.task.command_args['help'] = False

    @patch('azurectl.commands.compute_vm.DataOutput')
    @patch('azurectl.commands.compute_vm.VirtualMachine')
    def test_process_compute_vm_status(self, mock_vm, mock_out):
        self.__init_command_args()
        self.task.command_args['status'] = True
        vm = mock.Mock()
        mock_vm.return_value = vm
        vm.instance_status = mock.Mock(
            return_value='ReadyRole'
        )
        self.task.process()
        self.task.vm.instance_status.assert_called_once_with(
            'cloudservice', 'cloudservice'
        )

    @patch('azurectl.commands.compute_vm.DataOutput')
    def test_process_compute_vm_types(self, mock_out):
        self.__init_command_args()
        self.task.command_args['types'] = True
        self.task.process()
        self.task.account.instance_types.assert_called_once_with()

    @patch('azurectl.commands.compute_vm.DataOutput')
    def test_process_compute_vm_regions(self, mock_out):
        self.__init_command_args()
        self.task.command_args['regions'] = True
        self.task.process()
        self.task.account.locations.assert_called_once_with('PersistentVMRole')

    @patch('azurectl.commands.compute_vm.DataOutput')
    @patch('azurectl.commands.compute_vm.VirtualMachine')
    @patch('azurectl.commands.compute_vm.time.sleep')
    def test_process_compute_vm_create(
        self, mock_sleep, mock_vm, mock_out
    ):
        self.__init_command_args()
        vm = mock.Mock()
        mock_vm.return_value = vm
        status_results = ['ReadyRole', 'Starting']

        def side_effect(cloud_service, instance_name):
            return status_results.pop()

        vm.instance_status.side_effect = side_effect
        vm.create_linux_configuration = mock.Mock(
            return_value={}
        )
        vm.create_network_configuration = mock.Mock(
            return_value={}
        )
        self.task.command_args['create'] = True
        self.task.process()
        self.task.cloud_service.create.assert_called_once_with(
            self.task.command_args['--cloud-service-name'],
            self.task.config.get_region_name()
        )
        self.task.vm.create_instance.assert_called_once_with(
            self.task.command_args['--cloud-service-name'],
            self.task.command_args['--image-name'],
            {},
            network_config={},
            label=self.task.command_args['--label'],
            machine_size='Small',
            reserved_ip_name=None
        )
        mock_sleep.assert_called_once_with(5)
        assert status_results == []

    @patch('azurectl.commands.compute_vm.DataOutput')
    def test_process_compute_vm_create_with_fingerprint(self, mock_out):
        self.task.command_args['--fingerprint'] = 'foo'
        self.task.command_args['create'] = True
        self.task.command_args['--wait'] = False
        self.task.process()
        self.task.vm.create_linux_configuration.assert_called_once_with(
            'azureuser', 'foo', True, None, None, 'foo'
        )

    @patch('azurectl.commands.compute_vm.DataOutput')
    def test_process_compute_vm_create_with_custom_data_file(self, mock_out):
        with open('../data/customdata', 'r') as file:
                expected_custom_data = file.read()
        self.task.command_args['--custom-data'] = '../data/customdata'
        self.task.command_args['create'] = True
        self.task.command_args['--wait'] = False
        self.task.process()
        self.task.vm.create_linux_configuration.assert_called_once_with(
            'azureuser', 'foo', True, None, expected_custom_data, ''
        )

    @patch('azurectl.commands.compute_vm.DataOutput')
    def test_process_compute_vm_create_with_custom_data_string(self, mock_out):
        with open('../data/customdata', 'r') as file:
            expected_custom_data = file.read()
        self.task.command_args['--custom-data'] = expected_custom_data
        self.task.command_args['create'] = True
        self.task.command_args['--wait'] = False
        self.task.process()
        self.task.vm.create_linux_configuration.assert_called_once_with(
            'azureuser', 'foo', True, None, expected_custom_data, ''
        )

    @patch('azurectl.commands.compute_vm.DataOutput')
    @patch('azurectl.commands.compute_vm.VirtualMachine')
    @patch('azurectl.commands.compute_vm.time.sleep')
    def test_process_compute_vm_delete(self, mock_sleep, mock_vm, mock_out):
        vm = mock.Mock()
        mock_vm.return_value = vm
        vm.instance_status = mock.Mock(
            return_value = 'Undefined'
        )
        self.__init_command_args()
        self.task.command_args['delete'] = True
        self.task.command_args['--cloud-service-name'] = 'cloudservice'
        self.task.command_args['--instance-name'] = None
        self.task.process()
        self.task.cloud_service.delete.assert_called_once_with(
            self.task.command_args['--cloud-service-name'],
            True
        )
        self.task.command_args['--cloud-service-name'] = 'cloudservice'
        self.task.command_args['--instance-name'] = 'instance'
        self.task.process()
        self.task.vm.delete_instance.assert_called_once_with(
            self.task.command_args['--cloud-service-name'],
            self.task.command_args['--instance-name']
        )

    @patch('azurectl.commands.compute_vm.DataOutput')
    def test_process_compute_vm_reboot_specific_instance(
        self, mock_out
    ):
        self.__init_command_args()
        self.task.command_args['reboot'] = True
        self.task.command_args['--wait'] = False
        self.task.command_args['--cloud-service-name'] = 'cloudservice'
        self.task.command_args['--instance-name'] = 'instance'
        self.task.process()
        self.task.vm.reboot_instance.assert_called_once_with(
            self.task.command_args['--cloud-service-name'],
            self.task.command_args['--instance-name']
        )

    @patch('azurectl.commands.compute_vm.DataOutput')
    def test_process_compute_vm_shutdown_specific_instance(self, mock_out):
        self.__init_command_args()
        self.task.command_args['shutdown'] = True
        self.task.command_args['--wait'] = False
        self.task.command_args['--cloud-service-name'] = 'cloudservice'
        self.task.command_args['--instance-name'] = 'instance'
        self.task.process()
        self.task.vm.shutdown_instance.assert_called_once_with(
            self.task.command_args['--cloud-service-name'],
            self.task.command_args['--instance-name'],
            self.task.command_args['--deallocate-resources']
        )

    @patch('azurectl.commands.compute_vm.DataOutput')
    def test_process_compute_vm_start_specific_instance(self, mock_out):
        self.__init_command_args()
        self.task.command_args['start'] = True
        self.task.command_args['--wait'] = False
        self.task.command_args['--cloud-service-name'] = 'cloudservice'
        self.task.command_args['--instance-name'] = 'instance'
        self.task.process()
        self.task.vm.start_instance.assert_called_once_with(
            self.task.command_args['--cloud-service-name'],
            self.task.command_args['--instance-name']
        )

    @patch('azurectl.commands.compute_vm.DataOutput')
    @patch('azurectl.commands.compute_vm.VirtualMachine')
    @patch('azurectl.commands.compute_vm.time.sleep')
    def test_process_compute_vm_reboot_default_instance(
        self, mock_sleep, mock_vm, mock_out
    ):
        self.__init_command_args()
        vm = mock.Mock()
        vm.instance_status = mock.Mock(
            return_value = 'ReadyRole'
        )
        mock_vm.return_value = vm
        self.task.command_args['reboot'] = True
        self.task.command_args['--wait'] = True
        self.task.command_args['--cloud-service-name'] = 'cloudservice'
        self.task.command_args['--instance-name'] = None
        self.task.process()
        self.task.vm.reboot_instance.assert_called_once_with(
            self.task.command_args['--cloud-service-name'],
            self.task.command_args['--cloud-service-name']
        )

    @patch('azurectl.commands.compute_vm.DataOutput')
    @patch('azurectl.commands.compute_vm.VirtualMachine')
    @patch('azurectl.commands.compute_vm.time.sleep')
    def test_process_compute_vm_shutdown_default_instance_deallocate(
        self, mock_sleep, mock_vm, mock_out
    ):
        self.__init_command_args()
        vm = mock.Mock()
        vm.instance_status = mock.Mock(
            return_value = 'StoppedDeallocated'
        )
        mock_vm.return_value = vm
        self.task.command_args['shutdown'] = True
        self.task.command_args['--wait'] = True
        self.task.command_args['--cloud-service-name'] = 'cloudservice'
        self.task.command_args['--instance-name'] = None
        self.task.process()
        self.task.vm.shutdown_instance.assert_called_once_with(
            self.task.command_args['--cloud-service-name'],
            self.task.command_args['--cloud-service-name'],
            self.task.command_args['--deallocate-resources']
        )

    @patch('azurectl.commands.compute_vm.DataOutput')
    @patch('azurectl.commands.compute_vm.VirtualMachine')
    @patch('azurectl.commands.compute_vm.time.sleep')
    def test_process_compute_vm_shutdown_default_instance(
        self, mock_sleep, mock_vm, mock_out
    ):
        self.__init_command_args()
        vm = mock.Mock()
        vm.instance_status = mock.Mock(
            return_value = 'Stopped'
        )
        mock_vm.return_value = vm
        self.task.command_args['shutdown'] = True
        self.task.command_args['--deallocate-resources'] = False
        self.task.command_args['--wait'] = True
        self.task.command_args['--cloud-service-name'] = 'cloudservice'
        self.task.command_args['--instance-name'] = None
        self.task.process()
        self.task.vm.shutdown_instance.assert_called_once_with(
            self.task.command_args['--cloud-service-name'],
            self.task.command_args['--cloud-service-name'],
            self.task.command_args['--deallocate-resources']
        )

    @patch('azurectl.commands.compute_vm.DataOutput')
    @patch('azurectl.commands.compute_vm.VirtualMachine')
    @patch('azurectl.commands.compute_vm.time.sleep')
    def test_process_compute_vm_start_default_instance(
        self, mock_sleep, mock_vm, mock_out
    ):
        self.__init_command_args()
        vm = mock.Mock()
        vm.instance_status = mock.Mock(
            return_value = 'ReadyRole'
        )
        mock_vm.return_value = vm
        self.task.command_args['start'] = True
        self.task.command_args['--cloud-service-name'] = 'cloudservice'
        self.task.command_args['--instance-name'] = None
        self.task.process()
        self.task.vm.start_instance.assert_called_once_with(
            self.task.command_args['--cloud-service-name'],
            self.task.command_args['--cloud-service-name']
        )

    @patch('azurectl.commands.compute_vm.DataOutput')
    def test_process_compute_vm_show(self, mock_out):
        self.__init_command_args()
        self.task.command_args['show'] = True
        self.task.command_args['--cloud-service-name'] = 'cloudservice'
        self.task.process()
        self.task.cloud_service.get_properties.assert_called_once_with(
            self.task.command_args['--cloud-service-name']
        )

    def test_process_compute_vm_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'azurectl::compute::vm'
        )
