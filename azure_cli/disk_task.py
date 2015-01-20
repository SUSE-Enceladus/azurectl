from cli_task import CliTask
from storage_account import StorageAccount
from data_collector import DataCollector
from logger import Logger
from exceptions import *
from apscheduler.scheduler import Scheduler

class DiskTask(CliTask):
    def process(self):
        account = StorageAccount(self.account_name, self.config_file)
        self.disk = self.azure.Disk(account, self.command_args['<container>'])
        if self.command_args['upload']:
            self.__upload()
        elif self.command_args['delete']:
            self.__delete()
        else:
            raise AzureUnknownDiskCommand(self.command_args)


    def __upload(self):
        progress = Scheduler()
        progress.start()
        progress.add_interval_job(
            self.disk.print_upload_status, seconds = 2
        )
        image = self.command_args['<image>']
        self.disk.upload(
            image,
            self.global_args['--max-data-size'],
            self.global_args['--max-chunk-size']
        )
        progress.shutdown()
        Logger.info('Uploaded %s' % image)

    def __delete(self):
        image = self.command_args['<image>']
        self.disk.delete(image)
        Logger.info('Deleted %s' % image)
