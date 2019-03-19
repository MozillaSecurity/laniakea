# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Microsoft Azure CLI"""
import os
import logging
import argparse
import json

from laniakea.core.common import Focus

from .manager import AzureManager, AzureManagerException

logger = logging.getLogger('Laniakea')


class AzureCommandLine:
    """
    Sub command-line interface for the Microsoft Azure provider.
    """
    HOME = os.path.dirname(os.path.abspath(__file__))
    VERSION = 0.1

    @classmethod
    def add_arguments(cls, subparsers, dirs):
        parser = subparsers.add_parser(
            'azure',
            help='Microsoft Azure',
            formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=40, width=120))

        m = parser.add_argument_group('Mandatory Azure Parameters')  # pylint: disable=invalid-name

        m.add_argument('-region',
                       type=str,
                       metavar='name',
                       help='Azure region.')
        m.add_argument('-count',
                       type=int,
                       metavar='n',
                       default=1,
                       help='Number of instances to launch.')
        m.add_argument('-create',
                       action='store_true',
                       help='Create an instance pool.')
        m.add_argument('-delete',
                       action='store_true',
                       help='Delete an instance pool.')
        m.add_argument('-group-name',
                       type=str,
                       metavar='name',
                       help='Group name to be deleted.')
        m.add_argument('-conf',
                       metavar='path',
                       type=argparse.FileType(),
                       default=os.path.join(dirs.user_config_dir, 'azure.json'),
                       help='Deployment template for Windows Azure')

        u = parser.add_argument_group('UserData Parameters')  # pylint: disable=invalid-name
        u.add_argument('-template',
                       metavar='path',
                       type=argparse.FileType(),
                       default=os.path.join(dirs.user_config_dir, 'userdata', 'azure', 'template.json'),
                       help='Deployment template for Windows Azure')

        o = parser.add_argument_group('Optional Parameters')  # pylint: disable=invalid-name
        o.add_argument('-version',
                       action='version',
                       version='%(prog)s {}'.format(cls.VERSION),
                       help=argparse.SUPPRESS)

    @classmethod
    def main(cls, args, settings=None, userdata=None):
        logger.info('Using Azure configuration from %s', Focus.info(args.conf.name))
        try:
            settings = json.loads(args.conf.read())
        except ValueError as msg:
            logger.error('Unable to parse %s: %s', args.settings.name, msg)
            return 1

        logger.info('Using Azure instance template from %s', Focus.info(args.template.name))
        try:
            template = json.loads(args.template.read())
        except ValueError as msg:
            logger.error('Unable to parse %s: %s', args.template.name, msg)
            return 1

        cluster = AzureManager(settings)

        logger.info('Creating instance parameters.')
        try:
            parameters = cluster.create_parameters(args)
        except ValueError:
            logger.error('Unable to create parameters.')
            return 1

        try:
            cluster.connect()
        except AzureManagerException as msg:
            logger.error(msg)
            return 1

        if args.create:
            try:
                cluster.create(parameters, args.storage_name, template)
            except ValueError as msg:
                logging.error(msg)
                return 1

        if args.delete:
            try:
                cluster.terminate(args.group_name)
            except ValueError as msg:
                logging.error(msg)
                return 1

        return 0
