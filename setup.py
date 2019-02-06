#!/usr/bin/env python
# coding=utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""setuptools install script"""
import os
import sys

from setuptools import setup, find_packages, Command


HERE = os.path.abspath(os.path.dirname(__file__))

ABOUT = {}
with open(os.path.join(HERE, 'laniakea', '__version__.py')) as fo:
    exec(fo.read(), ABOUT)  # pylint: disable=exec-used

REQUIRED = [
    'appdirs',
    'azure-mgmt-resource==1.2.2',
    'azure-common==1.1.14',
    'boto>=2.48.0,<3.0',
    'packet-python==1.37.1',
    'apache-libcloud==2.4.0',
    'pycryptodome==3.7.3'
]


def README():
    with open('README.md') as fo:
        return fo.read()


class PublishCommand(Command):
    """Command class for: setup.py publish"""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(text):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(text))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            os.system('rm -rf {}'.format(os.path.join(HERE, 'dist')))
        except OSError:
            pass

        self.status('Building Source and Wheel distribution ...')
        os.system('{0} setup.py sdist bdist_wheel'.format(sys.executable))

        self.status('Pushing git tags ...')
        os.system('git tag v{0}'.format(ABOUT['__version__']))
        os.system('git push origin v{0}'.format(ABOUT['__version__']))

        self.status('Uploading the package to PyPI via Twine ...')
        os.system('twine upload dist/*')

        sys.exit()


if __name__ == '__main__':
    setup(
        version=ABOUT['__version__'],
        name=ABOUT['__title__'],
        license=ABOUT['__license__'],
        keywords=ABOUT['__keywords__'],
        description=ABOUT['__description__'],
        long_description=README(),
        long_description_content_type='text/markdown',
        author=ABOUT['__author__'],
        author_email=ABOUT['__author_email__'],
        maintainer=ABOUT['__maintainer__'],
        maintainer_email=ABOUT['__maintainer_email__'],
        url=ABOUT['__url__'],
        project_urls=ABOUT['__project_urls__'],
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
        install_requires=REQUIRED,
        packages=find_packages(),
        package_data={
            'laniakea': [
                'examples/*',
                'userdata/**/*',
            ]
        },
        cmdclass={
            'publish': PublishCommand,
        }
    )
