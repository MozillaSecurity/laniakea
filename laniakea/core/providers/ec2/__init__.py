# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import json
import logging
import argparse

import boto.exception

from laniakea.core.common import Focus
from laniakea.core.userdata import UserData
from .manager import EC2Manager

logger = logging.getLogger('laniakea')


class Ec2CommandLine(object):
    """
    Sub command-line interface for the Amazon EC2 provider.
    """
    HOME = os.path.dirname(os.path.abspath(__file__))
    VERSION = 0.8

    @classmethod
    def add_arguments(cls, subparsers, dirs):
        parser = subparsers.add_parser(
            'ec2',
            help='Amazon Elastic Cloud Computing',
            formatter_class=lambda prog:
                argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=30, width=100))

        m = parser.add_argument_group('Mandatory EC2 Parameters')

        g = m.add_mutually_exclusive_group(required=False)
        g.add_argument('-create-on-demand',
                       action='store_true',
                       help='Create on-demand instances.')

        g.add_argument('-create-spot',
                       action='store_true',
                       help='Create spot instances.')

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

        g.add_argument('-status',
                       action='store_true',
                       help='List current state of instances.')

        g.add_argument('-run',
                       metavar='cmd',
                       type=str,
                       default='',
                       help='Execute commands via SSH')

        g.add_argument('-list-userdata-macros',
                       action='store_true',
                       help='List available macros.')

        g.add_argument('-print-userdata',
                       action='store_true',
                       help='Print the UserData script to stdout.')

        u = parser.add_argument_group('UserData Parameters')
        u.add_argument('-userdata',
                       metavar='path',
                       type=argparse.FileType(),
                       default=os.path.join(dirs.user_config_dir, 'userdata', 'ec2', 'default.sh'),
                       help='UserData script for cloud-init process.')

        u.add_argument('-userdata-macros',
                       metavar='k=v',
                       nargs='+',
                       type=str,
                       help='Custom macros for the UserData.')

        o = parser.add_argument_group('Optional Parameters')
        o.add_argument('-tags',
                       metavar='k=v',
                       nargs='+',
                       type=str,
                       help='Assign tags to instances.')

        o.add_argument('-only',
                       metavar='k=v',
                       nargs='+',
                       type=str,
                       help='Filter instances by criterias.')

        o.add_argument('-images',
                       metavar='path',
                       type=argparse.FileType(),
                       default=os.path.join(dirs.user_config_dir, 'images.json'),
                       help='EC2 image definitions.')

        o.add_argument('-image-name',
                       metavar='str',
                       type=str,
                       default='default',
                       help='Name of image definition.')

        o.add_argument('-image-args',
                       metavar='k=v',
                       nargs='+',
                       type=str,
                       help='Custom image arguments.')

        o.add_argument('-profile',
                       metavar='str',
                       type=str,
                       default='laniakea',
                       help='AWS profile name in the .boto configuration.')

        o.add_argument('-max-spot-price',
                       metavar='#',
                       type=float,
                       default=0.05,
                       help='Max price for spot instances.')

        o.add_argument('-region',
                       type=str,
                       default='us-west-2',
                       help='EC2 region name.')

        o.add_argument('-zone',
                       type=str,
                       default=None,
                       help='EC2 placement zone.')

        o.add_argument('-root-device-type',
                       type=str,
                       default='ebs',
                       choices=['ebs', 'instance_store'],
                       help='The root device type.')

        o.add_argument('-ebs-size',
                       type=int,
                       default=None,
                       help='The root disk space size.')

        o.add_argument('-ebs-volume-type',
                       type=str,
                       default='gp2',
                       choices=['gp2', 'io1', 'standard'],
                       help='The root disk volume type.')

        o.add_argument('-ebs-volume-delete-on-termination',
                       action='store_true',
                       default=False,
                       help='Delete the root EBS volume on termination.')

        o.add_argument('-version',
                       action='version',
                       version='%(prog)s {}'.format(cls.VERSION),
                       help=argparse.SUPPRESS)

    @classmethod
    def main(cls, args, settings):
        args.only = UserData.convert_pair_to_dict(args.only or '')
        args.tags = UserData.convert_pair_to_dict(args.tags or '')
        args.image_args = UserData.convert_str_to_int(UserData.convert_pair_to_dict(args.image_args or {}))

        logger.info('Using image definition "%s" from %s', Focus.info(args.image_name), Focus.info(args.images.name))
        try:
            images = json.loads(args.images.read())
        except ValueError as msg:
            logger.error('Unable to parse %s: %s', args.images.name, msg)
            return 1

        logger.info('Reading user data script content from %s', Focus.info(args.userdata.name))
        userdata = args.userdata.read()
        if args.list_userdata_macros:
            UserData.list_tags(userdata)
            return 0
        userdata = UserData.handle_import_tags(userdata)

        args.userdata_macros = UserData.convert_pair_to_dict(args.userdata_macros or '')
        userdata = UserData.handle_tags(userdata, args.userdata_macros)

        if args.print_userdata:
            logger.info('Combined user-data script:')
            print(userdata)
            return 0

        if not userdata:
            return 1

        images[args.image_name]['user_data'] = userdata

        if args.image_args:
            logger.info('Setting custom image parameters for upcoming instances: %r ', args.image_args)
            images[args.image_name].update(args.image_args)

        logger.info('Using Boto configuration profile "%s"', Focus.info(args.profile))

        # If a zone has been specified on the command line, use that for all of our images
        if args.zone:
            for image_name in images:
                images[image_name]['placement'] = args.zone

        cluster = EC2Manager(images)
        try:
            cluster.connect(profile_name=args.profile, region=args.region)
        except Exception as msg:
            logger.error(msg)
            return 1

        if args.create_on_demand:
            try:
                cluster.create_on_demand(args.image_name, args.tags, args.root_device_type, args.ebs_size,
                                         args.ebs_volume_type, args.ebs_volume_delete_on_termination)
            except boto.exception.EC2ResponseError as msg:
                logger.error(msg)
                return 1

        if args.create_spot:
            try:
                cluster.create_spot(args.max_spot_price, args.image_name, args.tags, args.root_device_type,
                                    args.ebs_size, args.ebs_volume_type, args.ebs_volume_delete_on_termination)
            except boto.exception.EC2ResponseError as msg:
                logger.error(msg)
                return 1

        if args.stop:
            try:
                cluster.stop(cluster.find(filters=args.only), int(args.stop))
            except boto.exception.EC2ResponseError as msg:
                logger.error(msg)
                return 1

        if args.terminate:
            try:
                cluster.terminate(cluster.find(filters=args.only), int(args.terminate))
            except boto.exception.EC2ResponseError as msg:
                logger.error(msg)
                return 1

        if args.status:
            try:
                for i in cluster.find(filters=args.only):
                    logger.info('%s is %s at %s - tags: %s', i.id, i.state, i.ip_address, i.tags)
            except boto.exception.EC2ResponseError as msg:
                logger.error(msg)
                return 1

        if args.run:
            ssh = settings.get('SSH')
            if not ssh:
                logger.error('No SSH settings defined in %s', args.settings.name)
                return 1

            identity = ssh.get('identity')
            if not identity:
                logger.error('Key for SSH is not defined.')
                return 1
            identity = os.path.expanduser(identity)

            username = ssh.get('username')
            if not username:
                logger.error('User for SSH is not defined.')
                return 1

            logger.info('Bucketing available instances.')
            hosts = []
            try:
                for host in cluster.find(filters=args.only):
                    hosts.append(host)
            except boto.exception.EC2ResponseError as msg:
                logger.error(msg)
                return 1
            logger.info('Executing remote commands on %d instances.', len(hosts))
