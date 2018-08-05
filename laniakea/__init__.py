# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Laniakea is a utility for managing instances at various cloud providers and aids in setting up a fuzzing cluster.
"""
import os
import json
import shutil
import logging
import argparse

import appdirs

from .__version__ import __version__, __title__
from .core.common import Focus, ModuleLoader
from .core.userdata import UserData, UserDataException

logger = logging.getLogger(__title__)


class LaniakeaCommandLine:
    """
    Command-line interface for Laniakea.
    """
    HOME = os.path.dirname(os.path.abspath(__file__))
    VERSION = __version__

    @classmethod
    def parse_args(cls):
        """Main argument parser of Laniakea.
        """
        # Initialize configuration and userdata directories.
        dirs = appdirs.AppDirs(__title__, 'Mozilla Security')
        if not os.path.isdir(dirs.user_config_dir):
            shutil.copytree(os.path.join(cls.HOME, 'examples'), dirs.user_config_dir)
            shutil.copytree(os.path.join(cls.HOME, 'userdata'), os.path.join(dirs.user_config_dir, 'userdata'))

        parser = argparse.ArgumentParser(
            description='Laniakea Runtime v{}'.format(cls.VERSION),
            prog=__title__,
            add_help=False,
            formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=40, width=120),
            epilog='The exit status is 0 for non-failures and 1 for failures.')

        subparsers = parser.add_subparsers(dest='provider',
                                           description='Use -h to see the help menu of each provider.',
                                           title='Laniakea Cloud Providers',
                                           metavar='')

        modules = ModuleLoader()
        modules.load(os.getcwd(), 'laniakea/core/providers')

        for name, module in modules.modules.items():
            globals()[name] = module

        for module, cli in modules.command_line_interfaces():
            getattr(module, cli).add_arguments(subparsers, dirs)

        base = parser.add_argument_group('Laniakea Base Parameters')
        base.add_argument('-verbosity',
                          default=2,
                          type=int,
                          choices=list(range(1, 6, 1)),
                          help='Log sensitivity.')

        base.add_argument('-focus',
                          action='store_true',
                          default=True,
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

        userdata = parser.add_argument_group('UserData Parameters')
        userdata.add_argument('-userdata',
                              metavar='path',
                              type=argparse.FileType(),
                              help='UserData script for the provisioning process.')

        userdata.add_argument('-list-userdata-macros',
                              action='store_true',
                              help='List available macros.')

        userdata.add_argument('-print-userdata',
                              action='store_true',
                              help='Print the UserData script to stdout.')

        userdata.add_argument('-userdata-macros',
                              metavar='k=v',
                              nargs='+',
                              type=str,
                              help='Custom macros for the UserData.')

        return parser.parse_args()

    @classmethod
    def main(cls):
        """Main entry point of Laniakea.
        """
        args = cls.parse_args()

        if args.focus:
            Focus.init()
        else:
            Focus.disable()

        logging.basicConfig(format='[Laniakea] %(asctime)s %(levelname)s: %(message)s',
                            level=args.verbosity * 10,
                            datefmt='%Y-%m-%d %H:%M:%S')

        # Laniakea base configuration
        logger.info('Loading Laniakea configuration from %s', Focus.data(args.settings.name))
        try:
            settings = json.loads(args.settings.read())
        except ValueError as msg:
            logger.error('Unable to parse %s: %s', args.settings.name, msg)
            return 1

        # UserData
        userdata = ''

        if args.userdata:
            logger.info('Reading user data script content from %s', Focus.info(args.userdata.name))
            try:
                userdata = UserData.handle_import_tags(args.userdata.read(),
                                                       os.path.dirname(args.userdata.name))
            except UserDataException as msg:
                logging.error(msg)
                return 1

        if args.list_userdata_macros:
            UserData.list_tags(userdata)
            return 0

        if args.userdata_macros:
            args.userdata_macros = UserData.convert_pair_to_dict(args.userdata_macros or '')
            userdata = UserData.handle_tags(userdata, args.userdata_macros)

        if args.print_userdata:
            logger.info('Combined UserData script:\n%s', userdata)
            return 0

        if args.provider:
            provider = getattr(globals()[args.provider], args.provider.title() + 'CommandLine')
            provider().main(args, settings, userdata)

        return 0
