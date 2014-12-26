#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import ast
import sys
import json
import logging
import argparse
import threading

from core.manager import LaniakeaManager


class Laniakea(object):
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
        g.add_argument('-create', action='store_true', help='create instance/s')
        g.add_argument('-stop', action='store_true', help='stop instance/s')
        g.add_argument('-terminate', action='store_true', help='terminate instance/s')
        g.add_argument('-status', action='store_true', help='list current state of instance/s')
        o = parser.add_argument_group('optional arguments')
        o.add_argument('-tags', metavar='dict', type=ast.literal_eval, default={}, help='tag instance/s')
        o.add_argument('-only', metavar='dict', type=ast.literal_eval, default={}, help='filter instance/s')
        o.add_argument('-count', metavar='#', type=int, default=1, help='number of instances to launch')
        o.add_argument('-image-name', metavar='str', type=str, default="default", help='name of image definition')
        o.add_argument('-images', metavar='path', type=argparse.FileType('r'),
                       default=os.path.relpath(os.path.join(Laniakea.HOME, "images.json")),
                       help='EC2 image definitions')
        o.add_argument('-profile', metavar='str', type=str, default="laniakea", help='AWS profile name in .boto')
        o.add_argument('-user-data', metavar='path', type=argparse.FileType('r'),
                       default=os.path.relpath(os.path.join(Laniakea.HOME, 'user_data', 'default.sh')),
                       help='data script for cloud-init')
        o.add_argument('-logging', metavar='#', default=20, type=int, choices=range(10, 60, 10),
                       help='verbosity level of the logging module')
        o.add_argument('-h', '-help', '--help', action='help', help=argparse.SUPPRESS)
        o.add_argument('-version', action='version', version='%(prog)s 1.0', help=argparse.SUPPRESS)
        return parser.parse_args()

    @classmethod
    def main(cls):
        args = cls.parse_args()
        logging.basicConfig(format='[Laniakea] %(asctime)s %(levelname)s: %(message)s', level=args.logging)
        logging.info("Using image definition '%s' from %s" % (args.image_name, args.images.name))
        images = json.loads(args.images.read())
        logging.info("Adding user data script content from %s", args.user_data.name)
        images[args.image_name]["user_data"] = args.user_data.read()
        cluster = LaniakeaManager(images)
        logging.info("Using Boto configuration profile '%s'" % args.profile)
        cluster.connect(profile_name=args.profile)
        if args.create:
            bots = []
            for _ in range(args.count):
                bot = threading.Thread(target=cluster.create, args=(args.image_name, args.tags))
                bot.daemon = True
                bot.start()
                bots.append(bot)
                for bot in bots:
                    bot.join()
        if args.stop:
            cluster.stop(cluster.find(filters=args.only))
        if args.terminate:
            cluster.terminate(cluster.find(filters=args.only))
        if args.status:
            instances = cluster.find(filters=args.only)
            for instance in instances:
                logging.info("%s (%s) - %s" % (cluster.state([instance]), instance.ip_address, instance.tags))
        return 0


if __name__ == "__main__":
    sys.exit(Laniakea.main())
