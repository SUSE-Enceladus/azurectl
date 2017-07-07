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

class raises(object):
    """
    exception decorator as used in nose, tools/nontrivial.py
    """
    def __init__(self, *exceptions):
        self.exceptions = exceptions
        self.valid = ' or '.join([e.__name__ for e in exceptions])

    def __call__(self, func):
        name = func.__name__

        def newfunc(*args, **kw):
            try:
                func(*args, **kw)
            except self.exceptions:
                pass
            except:
                raise
            else:
                message = "%s() did not raise %s" % (name, self.valid)
                raise AssertionError(message)
        newfunc = wraps(func)(newfunc)
        return newfunc
