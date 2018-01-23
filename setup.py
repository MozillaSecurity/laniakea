#!/usr/bin/env python
# coding=utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from setuptools import setup

if __name__ == '__main__':
    setup(
        classifiers=[
            'Intended Audience :: Developers',
            'Topic :: Software Development :: Testing',
            'Topic :: Security',
            'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6'
        ],
        description='Utility to automate creating EC2 instances.',
        entry_points={
            "console_scripts": ["laniakea = laniakea:LaniakeaCommandLine.main"]
        },
        install_requires=['appdirs', 'boto'],
        license='MPL 2.0',
        maintainer='Christoph Diehl',
        maintainer_email='cdiehl@mozilla.com',
        name='laniakea',
        packages=['laniakea', 'laniakea.core'],
        package_data={'laniakea': [
            'examples/*',
            'userdata/*',
        ]},
        package_dir={'laniakea': 'src'},
        url='https://github.com/MozillaSecurity/laniakea',
        version='0.6')
