from functools import wraps
from mock import patch
import azurectl.logger
import logging
import sys

azurectl.logger.init()

# default log level, overwrite when needed
azurectl.logger.log.setLevel(logging.WARN)

# default commandline used for any test, overwrite when needed
sys.argv = [
    sys.argv[0], 'compute', 'vm', 'types'
]
argv_kiwi_tests = sys.argv
