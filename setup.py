#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from azurectl.version import __VERSION__

config = {
    'name': 'azurectl',
    'description': 'Manage Azure PubCloud Service',
    'author': 'PubCloud Development team',
    'url': 'https://github.com/SUSE/azurectl',
    'download_url': 'https://github.com/SUSE/azurectl',
    'author_email': 'public-cloud-dev@susecloud.net',
    'version': __VERSION__,
    'install_requires': [
        'docopt>=0.6.2',
        'APScheduler>=3.0.2',
        'azure-storage>=0.30.0',
        'azure-servicemanagement-legacy>=0.20.1',
        'python-dateutil>=2.4',
        'pyOpenSSL',
        'setuptools>=5.4'
    ],
    'packages': ['azurectl'],
    'entry_points': {
        'console_scripts': ['azurectl=azurectl.azurectl:main'],
    },
    'include_package_data': True,
    'zip_safe': False,
    'classifiers': [
        # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Operating System'
    ]
}

setup(**config)
