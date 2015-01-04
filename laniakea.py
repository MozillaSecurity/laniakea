#!/usr/bin/env python
# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Laniakea is a utility for managing EC2 instances at AWS and aids in setting up a fuzzing cluster.
"""
import os
import ast
import sys
import json
import logging
import argparse

from core.common import Focus
from core.manager import Laniakea


class LaniakeaCommandLine(object):
    """
    Command-line interface for Laniakea.
    """
    HOME = os.path.dirname(os.path.abspath(__file__))

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(description='Laniakea Runtime',
                                         prog=__file__,
                                         add_help=False,
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                         epilog='The exit status is 0 for non-failures and -1 for failures.')
        m = parser.add_argument_group('mandatory arguments')
        g = m.add_mutually_exclusive_group(required=True)
        g.add_argument('-create', action='store_true', help='create on-demand instance/s')
        g.add_argument('-create-spot', action='store_true', help='create spot instance/s')
        g.add_argument('-stop', action='store_true', help='stop instance/s')
        g.add_argument('-terminate', action='store_true', help='terminate instance/s')
        g.add_argument('-status', action='store_true', help='list current state of instance/s')
        o = parser.add_argument_group('optional arguments')
        o.add_argument('-tags', metavar='dict', type=ast.literal_eval, default={}, help='tag instance/s')
        o.add_argument('-only', metavar='dict', type=ast.literal_eval, default={}, help='filter instance/s')
        o.add_argument('-image-name', metavar='str', type=str, default="default", help='name of image definition')
        o.add_argument('-images', metavar='path', type=argparse.FileType(),
                       default=os.path.relpath(os.path.join(LaniakeaCommandLine.HOME, "images.json")),
                       help='EC2 image definitions')
        o.add_argument('-profile', metavar='str', type=str, default='laniakea', help='AWS profile name in .boto')
        o.add_argument('-user-data', metavar='path', type=argparse.FileType(),
                       default=os.path.relpath(os.path.join(LaniakeaCommandLine.HOME, 'user_data', 'default.sh')),
                       help='data script for cloud-init')
        o.add_argument('-max-spot-price', metavar='#', type=float, default=0.100, help='max price for spot instances')
        o.add_argument('-logging', metavar='#', default=20, type=int, choices=range(10, 60, 10),
                       help='verbosity level of the logging module')
        o.add_argument('-focus', action='store_true', default=False, help='colorized output')
        o.add_argument('-h', '-help', '--help', action='help', help=argparse.SUPPRESS)
        o.add_argument('-version', action='version', version='%(prog)s 0.2', help=argparse.SUPPRESS)
        return parser.parse_args()

    @classmethod
    def main(cls):
        args = cls.parse_args()
        logging.basicConfig(format='[Laniakea] %(asctime)s %(levelname)s: %(message)s',
                            level=args.logging,
                            datefmt="%Y-%m-%d %H:%M:%S")
        Focus.init() if args.focus else Focus.disable()
        logging.info('Using image definition "%s" from %s.', Focus.info(args.image_name), Focus.info(args.images.name))
        images = json.loads(args.images.read())
        logging.info('Adding user data script content from %s.', Focus.info(args.user_data.name))
        images[args.image_name]['user_data'] = args.user_data.read()
        cluster = Laniakea(images)
        logging.info('Using Boto configuration profile "%s".' % Focus.info(args.profile))
        cluster.connect(profile_name=args.profile)
        if args.create:
            cluster.create_on_demand(args.image_name, args.tags)
        if args.create_spot:
            cluster.create_spot(args.max_spot_price, args.image_name, args.tags)
        if args.stop:
            cluster.stop(cluster.find(filters=args.only))
        if args.terminate:
            cluster.terminate(cluster.find(filters=args.only))
        if args.status:
            for i in cluster.find(filters=args.only):
                logging.info('%s is %s at %s - tags: %s', i.id, i.state, i.ip_address, i.tags)
        return 0


if __name__ == '__main__':
    sys.exit(LaniakeaCommandLine.main())
