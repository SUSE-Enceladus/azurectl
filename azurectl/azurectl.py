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
import sys
import docopt

# project
from . import logger
from .app import App
from .defaults import Defaults
from .azurectl_exceptions import AzureError


def extras(help, version, options, doc):
    """
    Overwritten method from docopt

    We want to show our own usage for -h|--help
    """
    if help and any((o.name in ('-h', '--help')) and o.value for o in options):
        usage(doc.strip("\n"))
        sys.exit(1)
    if version and any(o.name == '--version' and o.value for o in options):
        print(version)
        sys.exit()


def main():
    """
        azurectl - invoke the Application
    """
    docopt.__dict__['extras'] = extras
    logger.init()
    try:
        App()
    except AzureError as e:
        # known exception, log information and exit
        logger.log.error('%s: %s', type(e).__name__, format(e))
        sys.exit(1)
    except docopt.DocoptExit as e:
        # exception caught by docopt, results in usage message
        usage(format(e))
        sys.exit(1)
    except SystemExit:
        # user exception, program aborted by user
        sys.exit(1)
    except Exception:
        # exception we did no expect, show python backtrace
        logger.log.error('Unexpected error:')
        raise


def usage(command_usage):
    """
    Instead of the docopt way to show the usage information we
    provide an azurectl specific usage information. The usage
    data now always consists of

    * the generic call
      azurectl [global options] service <command> [<args>]

    * the command specific usage defined by the docopt string
      short form by default, long form with -h | --help

    * the global options
    """
    with open(Defaults.project_file('cli.py'), 'r') as cli:
        program_code = cli.readlines()

    global_options = '\n'
    process_lines = False
    for line in program_code:
        if line.rstrip().startswith('global options'):
            process_lines = True
        if line.rstrip() == '"""':
            process_lines = False
        if process_lines:
            global_options += format(line)

    print('usage: azurectl [global options] service <command> [<args>]\n')
    print(format(command_usage).replace('usage:', '      '))
    if 'global options' not in command_usage:
        print(format(global_options))

    if not format(command_usage).startswith('usage:'):
        error_details = format(command_usage).splitlines()[0]
        print(error_details)
