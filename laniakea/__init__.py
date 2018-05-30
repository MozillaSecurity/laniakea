# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
'''
Laniakea is a utility for managing instances at various cloud providers and aids in setting up a fuzzing cluster.
'''
import argparse
import json
import logging
import os
import shutil

from .core.common import Focus


# Todo (posidron): Add modules dynamically.
MODULES = []
try:
    from .core.providers.ec2 import Ec2CommandLine
    MODULES.append(Ec2CommandLine)
except ImportError:
    pass
try:
    from .core.providers.azure import AzureCommandLine
    MODULES.append(AzureCommandLine)
except ImportError:
    pass


logger = logging.getLogger('laniakea')


class LaniakeaCommandLine(object):
    '''
    Command-line interface for Laniakea.
    '''
    HOME = os.path.dirname(os.path.abspath(__file__))
    VERSION = '0.9'

    @classmethod
    def parse_args(cls):
        import appdirs

        # Initialize configuration and userdata directories.
        dirs = appdirs.AppDirs('laniakea', 'Mozilla Security')
        if not os.path.isdir(dirs.user_config_dir):
            shutil.copytree(os.path.join(cls.HOME, 'examples'), dirs.user_config_dir)
            shutil.copytree(os.path.join(cls.HOME, 'userdata'), os.path.join(dirs.user_config_dir, 'userdata'))

        parser = argparse.ArgumentParser(
            description='Laniakea Runtime v{}'.format(cls.VERSION),
            prog='laniakea',
            add_help=False,
            formatter_class=lambda prog:
                argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=30, width=100),
            epilog='The exit status is 0 for non-failures and 1 for failures.')

        subparsers = parser.add_subparsers(dest='provider',
                                           description='Use -h to see the help menu of each provider.',
                                           title='Laniakea Cloud Providers',
                                           metavar='')

        for module in MODULES:
            module.add_arguments(subparsers, dirs)

        base = parser.add_argument_group('Laniakea Base Parameter')
        base.add_argument('-verbosity',
                          default=2,
                          type=int,
                          choices=list(range(1, 6, 1)),
                          help='Log sensitivity.')

        base.add_argument('-focus',
                          action='store_true',
                          default=False,
                          help=argparse.SUPPRESS)

        base.add_argument('-settings',
                          metavar='path',
                          type=argparse.FileType(),
                          default=os.path.join(dirs.user_config_dir, 'laniakea.json'),
                          help='Laniakea core settings.')

        base.add_argument('-h', '-help', '--help',
                          action='help',
                          help=argparse.SUPPRESS)

        base.add_argument('-version',
                          action='version',
                          version='%(prog)s {}'.format(cls.VERSION),
                          help=argparse.SUPPRESS)

        return parser.parse_args()

    @classmethod
    def main(cls):
        args = cls.parse_args()

        Focus.init() if args.focus else Focus.disable()

        logging.basicConfig(format='[Laniakea] %(asctime)s %(levelname)s: %(message)s',
                            level=args.verbosity * 10,
                            datefmt='%Y-%m-%d %H:%M:%S')

        logger.info('Loading Laniakea configuration from %s', Focus.data(args.settings.name))
        try:
            settings = json.loads(args.settings.read())
        except ValueError as msg:
            logger.error('Unable to parse %s: %s', args.settings.name, msg)
            return 1

        if args.provider:
            globals()[args.provider.title() + 'CommandLine']().main(args, settings)
