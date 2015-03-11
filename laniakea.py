#!/usr/bin/env python
# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Laniakea is a utility for managing EC2 instances at AWS and aids in setting up a fuzzing cluster.
"""
import os
import re
import sys
import json
import logging
import argparse

from core.common import Focus
from core.manager import Laniakea

import boto.exception


class LaniakeaCommandLine(object):
    """
    Command-line interface for Laniakea.
    """
    HOME = os.path.dirname(os.path.abspath(__file__))
    VERSION = 0.4

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Laniakea Runtime',
                                         prog=__file__,
                                         add_help=False,
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                         epilog='The exit status is 0 for non-failures and 1 for failures.')

        m = parser.add_argument_group('Mandatory Arguments')

        g = m.add_mutually_exclusive_group(required=True)
        g.add_argument('-create-on-demand', action='store_true', help='Create on-demand instances')
        g.add_argument('-create-spot', action='store_true', help='Create spot instances')
        g.add_argument('-stop', nargs='?', const=0, metavar='n', help='Stop active instances')
        g.add_argument('-terminate', nargs='?', const=0, metavar='n', help='Terminate active instances')
        g.add_argument('-status', action='store_true', help='List current state of instances')

        u = parser.add_argument_group('UserData Arguments')
        u.add_argument('-userdata', metavar='path', type=argparse.FileType(),
                       default=os.path.relpath(os.path.join(self.HOME, 'userdata', 'default.sh')),
                       help='UserData script for cloud-init')
        u.add_argument('-list-userdata-macros', action='store_true', help='List available macros')
        u.add_argument('-userdata-macros', metavar='k=v', nargs='+', type=str, help='Custom macros')

        o = parser.add_argument_group('Optional Arguments')
        o.add_argument('-tags', metavar='k=v', nargs='+', type=str, help='Assign tags to instances')
        o.add_argument('-only', metavar='k=v', nargs='+', type=str, help='Filter instances')
        o.add_argument('-images', metavar='path', type=argparse.FileType(),
                       default=os.path.relpath(os.path.join(self.HOME, 'images.json')),
                       help='EC2 image definitions')
        o.add_argument('-image-name', metavar='str', type=str, default='default', help='Name of image definition')
        o.add_argument('-image-args', metavar='k=v', nargs='+', type=str, help='Custom image arguments')
        o.add_argument('-profile', metavar='str', type=str, default='laniakea', help='AWS profile name in .boto')
        o.add_argument('-max-spot-price', metavar='#', type=float, default=0.05, help='Max price for spot instances')
        o.add_argument('-region', type=str, default='us-west-2', help='EC2 region')
        o.add_argument('-verbosity', default=2, type=int, choices=range(1, 6, 1),
                       help='Log level for the logging module')
        o.add_argument('-focus', action='store_true', default=False, help=argparse.SUPPRESS)
        o.add_argument('-h', '-help', '--help', action='help', help=argparse.SUPPRESS)
        o.add_argument('-version', action='version', version='%(prog)s {}'.format(self.VERSION),
                       help=argparse.SUPPRESS)

        return parser.parse_args()

    def _convert_pair_to_dict(self, arg):
        """Utility function which transform k=v strings from the command-line into a dict.
        """
        return dict(kv.split('=', 1) for kv in arg)

    def _convert_str_to_int(self, arg):
        # FIXME: Convert certain values of keys from images.json to ints.
        for k, v in arg.items():
            try:
                arg[unicode(k)] = int(v)
            except ValueError as e:
                # Let's assume it is a str.
                pass
        return arg

    def list_tags(self, userdata):
        macros = re.findall("@(.*?)@", userdata)
        logging.info('List of available macros: %r', macros)

    def handle_tags(self, userdata, raw_macros):
        macros = {}
        if raw_macros:
            macros = self._convert_pair_to_dict(raw_macros)

        macro_vars = re.findall("@([a-zA-Z0-9]+)@", userdata)
        for macro_var in macro_vars:
            if macro_var not in macros:
                logging.error('Undefined variable @%s@ in UserData script', macro_var)
                return
            userdata = userdata.replace('@%s@' % macro_var, macros[macro_var])

        return userdata

    def handle_import_tags(self, userdata):
        """Handle @import(filepath)@ tags in a UserData script.

        :param userdata: UserData script content.
        :type userdata: str
        :return: UserData script with the contents of the imported files.
        :rtype: str
        """
        imports = re.findall("@import\((.*?)\)@", userdata)
        if not imports:
            return userdata

        for filepath in imports:
            logging.info('Processing "import" of %s' % filepath)
            with open(filepath) as fp:
                content = fp.read()
                userdata = userdata.replace("@import(%s)@" % filepath, content)
        return userdata

    def main(self):
        args = self.parse_args()

        logging.basicConfig(format='[Laniakea] %(asctime)s %(levelname)s: %(message)s',
                            level=args.verbosity * 10,
                            datefmt='%Y-%m-%d %H:%M:%S')

        Focus.init() if args.focus else Focus.disable()

        args.only = self._convert_pair_to_dict(args.only or "")
        args.tags = self._convert_pair_to_dict(args.tags or "")
        args.image_args = self._convert_str_to_int(self._convert_pair_to_dict(args.image_args or {}))

        logging.info('Using image definition "%s" from %s', Focus.info(args.image_name), Focus.info(args.images.name))
        try:
            images = json.loads(args.images.read())
        except ValueError as msg:
            logging.error('Unable to parse %s: %s', args.images.name, msg)
            return 1

        logging.info('Reading user data script content from %s', Focus.info(args.userdata.name))
        userdata = args.userdata.read()
        if args.list_userdata_macros:
            self.list_tags(userdata)
            return 0
        userdata = self.handle_import_tags(userdata)
        userdata = self.handle_tags(userdata, args.userdata_macros)
        logging.debug("*** UserData ***\n%s" % userdata)
        if not userdata:
            return 1
        images[args.image_name]['user_data'] = userdata

        if args.image_args:
            logging.info("Setting custom image parameters for upcoming instances: %r " % args.image_args)
            images[args.image_name].update(args.image_args)

        logging.info('Using Boto configuration profile "%s"', Focus.info(args.profile))

        cluster = Laniakea(images)
        try:
            cluster.connect(profile_name=args.profile, region=args.region)
        except Exception as msg:
            logging.error(msg)
            return 1

        if args.create_on_demand:
            try:
                cluster.create_on_demand(args.image_name, args.tags)
            except boto.exception.EC2ResponseError as msg:
                logging.error(msg)
                return 1

        if args.create_spot:
            try:
                cluster.create_spot(args.max_spot_price, args.image_name, args.tags)
            except boto.exception.EC2ResponseError as msg:
                logging.error(msg)
                return 1

        if args.stop:
            try:
                cluster.stop(cluster.find(filters=args.only), int(args.stop))
            except boto.exception.EC2ResponseError as msg:
                logging.error(msg)
                return 1

        if args.terminate:
            try:
                cluster.terminate(cluster.find(filters=args.only), int(args.terminate))
            except boto.exception.EC2ResponseError as msg:
                logging.error(msg)
                return 1

        if args.status:
            try:
                for i in cluster.find(filters=args.only):
                    logging.info('%s is %s at %s - tags: %s', i.id, i.state, i.ip_address, i.tags)
            except boto.exception.EC2ResponseError as msg:
                logging.error(msg)
                return 1

        return 0


if __name__ == '__main__':
    sys.exit(LaniakeaCommandLine().main())
