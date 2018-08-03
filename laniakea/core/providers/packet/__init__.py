# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Packet Bare Metal CLI"""
import os
import json
import logging
import argparse

from laniakea.core.common import Focus
from laniakea.core.userdata import UserData
from .manager import PacketManager, PacketManagerException

logger = logging.getLogger('laniakea')


class PacketCommandLine(object):
    """
    Sub command-line interface for the Packet provider.
    """
    HOME = os.path.dirname(os.path.abspath(__file__))
    VERSION = 0.1

    @classmethod
    def add_arguments(cls, subparsers, dirs):
        """Argument parser of this module.
        """
        parser = subparsers.add_parser(
            'packet',
            help='Packet Bare Metal',
            formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=40, width=120))

        m = parser.add_argument_group('Mandatory Packet Parameters')

        g = m.add_mutually_exclusive_group(required=False)
        g.add_argument('-create-demand',
                       action='store_true',
                       help='Create an on demand based bare metal device instance.')

        g.add_argument('-create-spot',
                       action='store_true',
                       help='Create a spot price based bare metal device instance.')

        g.add_argument('-reboot',
                       nargs='?',
                       const=-1,
                       metavar='n',
                       help='Reboot active instances.')

        g.add_argument('-stop',
                       nargs='?',
                       const=-1,
                       metavar='n',
                       help='Stop active instances.')

        g.add_argument('-terminate',
                       nargs='?',
                       const=-1,
                       metavar='n',
                       help='Terminate active instances.')

        o = parser.add_argument_group('Optional Parameters')
        o.add_argument('-create-volume',
                       nargs='+',
                       type=str,
                       metavar='s',
                       help='Create storage: <plan> <size> <region> <description>')

        o.add_argument('-conf',
                       metavar='path',
                       type=argparse.FileType(),
                       default=os.path.join(dirs.user_config_dir, 'examples', 'packet', 'packet.json'),
                       help='Packet configuration')

        o.add_argument('-list-projects',
                       action='store_true',
                       help='List available projects.')

        o.add_argument('-list-plans',
                       action='store_true',
                       help='List available plans.')

        o.add_argument('-list-operating-systems',
                       action='store_true',
                       help='List available operating systems.')

        o.add_argument('-list-spot-prices',
                       action='store_true',
                       help='List spot prices.')

        o.add_argument('-list-facilities',
                       action='store_true',
                       help='List available facilities.')

        o.add_argument('-list-devices',
                       action='store_true',
                       help='List devices under given project name.')

        o.add_argument('-project',
                       metavar='project',
                       type=str,
                       default='fuzzing',
                       help='The project to perform operations on.')
        o.add_argument('-tags',
                       metavar='seq',
                       nargs='+',
                       type=str,
                       help='Tags associtated with the instance.')
        o.add_argument('-region',
                       metavar='region',
                       type=str,
                       default='nrt1',
                       help='The facility in which the instance is going to run.')
        o.add_argument('-os',
                       metavar='name',
                       type=str,
                       default='ubuntu_18_04',
                       help='The operating system for the created instance.')
        o.add_argument('-plan',
                       metavar='name',
                       type=str,
                       default='baremetal_0',
                       help='The instance type to run.')
        o.add_argument('-max-spot-price',
                       metavar='#',
                       type=float,
                       default='0.05',
                       help='Max price for spot instances.')
        o.add_argument('-count',
                       metavar='#',
                       type=int,
                       default='1',
                       help='The amount of devices to be spawned.')
        o.add_argument('-only',
                       metavar='k=v',
                       nargs='+',
                       type=str,
                       help='Filter instances by criterias.')
        o.add_argument('-version',
                       action='version',
                       version='%(prog)s {}'.format(cls.VERSION),
                       help=argparse.SUPPRESS)

    @classmethod
    def main(cls, args, settings=None, userdata=None):
        """Main entry point of this module.
        """
        # Packet Configuration
        logger.info('Using Packet configuration from %s', Focus.info(args.conf.name))
        try:
            conf = json.loads(args.conf.read())
        except ValueError as msg:
            logger.error('Unable to parse %s: %s', args.conf.name, msg)
            return 1

        # Handle Tags
        if args.tags and (args.create_spot or args.create_demand):
            logger.info('Assigning the following tags to the instance: %r', args.tags)

        if args.only:
            try:
                args.only = UserData.parse_only_criterias(args.only)
            except ValueError:
                logger.error('-only requires format of: name=value')
                return 1
            logging.info('Using filter %r to return only matching devices.', args.only)

        # Packet Manager
        try:
            cluster = PacketManager(conf)
        except PacketManagerException as msg:
            logger.error(msg)
            return 1
        project = cluster.conf.get('projects').get(args.project)

        # List Operations
        if args.list_projects:
            cluster.print_projects(cluster.list_projects())

        if args.list_plans:
            cluster.print_plans(cluster.list_plans())

        if args.list_spot_prices:
            cluster.print_spot_prices(cluster.list_spot_prices())

        if args.list_operating_systems:
            cluster.print_operating_systems(cluster.list_operating_systems())

        if args.list_facilities:
            cluster.print_facilities(cluster.list_facilities())

        if args.list_devices and args.project:
            cluster.print_devices(cluster.list_devices(project, conditions=args.only))

        if args.create_volume:
            if len(args.create_volume) < 4:
                logger.error('Not enough arguments for creating a volume storage.')
                return 1
            [plan, size, region, label] = args.create_volume
            try:
                cluster.create_volume(project, plan, size, region, label)
            except PacketManagerException as msg:
                logger.error(msg)
                return 1

        # Device Pre-Checks
        if (args.create_spot or args.create_demand) \
            and (args.region and args.plan):
            logging.info('Validating requested remote capacities ...')
            try:
                status = cluster.validate_capacity([
                    [args.region, args.plan, str(args.count)]
                ])
                if status:
                    logger.info('Requested capacities are available.')
            except PacketManagerException as msg:
                logger.error(msg)
                return 1

        # Device Creation
        if args.create_spot \
            and args.region \
            and args.plan \
            and args.max_spot_price \
            and args.os:
            try:
                devices = cluster.create_spot(project_id=project,
                                              facility=args.region,
                                              plan=args.plan,
                                              operating_system=args.os,
                                              spot_price_max=args.max_spot_price,
                                              tags=args.tags,
                                              userdata=userdata,
                                              count=args.count)
                cluster.print_devices(devices)
            except PacketManagerException as msg:
                logger.error(msg)
                return 1

        if args.create_demand \
            and args.region \
            and args.plan \
            and args.os:
            try:
                devices = cluster.create_demand(project_id=project,
                                                facility=args.region,
                                                plan=args.plan,
                                                tags=args.tags,
                                                operating_system=args.os,
                                                userdata=userdata,
                                                count=args.count)
                cluster.print_devices(devices)
            except PacketManagerException as msg:
                logger.error(msg)
                return 1

        # Device Operations
        if args.reboot:
            try:
                cluster.reboot(cluster.list_devices(project, conditions=args.only))
            except PacketManagerException as msg:
                logger.error(msg)
                return 1

        if args.stop:
            try:
                cluster.stop(cluster.list_devices(project, conditions=args.only))
            except PacketManagerException as msg:
                logger.error(msg)
                return 1

        if args.terminate:
            try:
                cluster.terminate(cluster.list_devices(project, conditions=args.only))
            except PacketManagerException as msg:
                logger.error(msg)
                return 1
