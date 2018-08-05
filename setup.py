#!/usr/bin/env python
# coding=utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""setuptools install script"""
import os
from setuptools import setup, find_packages


HERE = os.path.abspath(os.path.dirname(__file__))

def readme():
    with open('README.md') as fo:
        return fo.read()

about = {}
with open(os.path.join(HERE, 'laniakea', '__version__.py')) as fo:
    exec(fo.read(), about)

requires = [
    'appdirs',
    'azure-mgmt-resource==1.2.2',
    'azure-common==1.1.14',
    'boto>=2.48.0,<3.0'
    'packet-python==1.37.1'
]


if __name__ == '__main__':
    setup(
        version=about['__version__'],
        name=about['__title__'],
        license=about['__license__'],
        keywords=about['__keywords__'],
        description=about['__description__'],
        long_description=readme(),
        long_description_content_type='text/markdown',
        author=about['__author__'],
        author_email=about['__author_email__'],
        maintainer=about['__maintainer__'],
        maintainer_email=about['__maintainer_email__'],
        url=about['__url__'],
        project_urls=about['__project_urls__'],
        classifiers=[
            'Intended Audience :: Developers',
            'Topic :: Software Development :: Testing',
            'Topic :: Security',
            'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.6'
        ],
        entry_points={
            "console_scripts": [
                "laniakea = laniakea:LaniakeaCommandLine.main"
            ]
        },
        install_requires=requires,
        packages=find_packages(),
        package_data={
            'laniakea': [
                'examples/*',
                'userdata/**/*',
            ]
        }
    )
