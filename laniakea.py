#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import ast
import sys
import time
import json
import logging
import argparse
import threading

from boto.ec2 import connect_to_region


class LaniakeaEngine(object):

    def __init__(self, images):
        self.ec2 = None
        self.instances = []
        self.images = images

    def connect(self, region="us-west-2", **kw_params):
        self.ec2 = connect_to_region(region, **kw_params)

    def create(self, instance_type='default', tags=None):
        reservation = self.ec2.run_instances(**self.images[instance_type])
        instance = reservation.instances[0]
        self.ec2.create_tags([instance.id], tags or {})
        while instance.state == 'pending':
            time.sleep(0.5)
            instance.update()
        logging.info("DNS: %s (%s)" % (instance.public_dns_name, instance.ip_address))
        self.instances.append(instance)

    def state(self, instances=None):
        instances = instances or self.instances
        if not instances:
            return
        [instance.update() for instance in instances]
        return [(instance.id, instance.state) for instance in instances]

    def stop(self, instances=None):
        instances = instances or self.instances
        if not instances:
            return
        self.ec2.stop_instances([instance.id for instance in instances])

    def terminate(self, instances=None):
        instances = instances or self.instances
        if not instances:
            return
        self.ec2.terminate_instances([instance.id for instance in instances])

    def find(self, filters=None):
        instances = []
        reservations = self.ec2.get_all_instances(filters=filters or {})
        for reservation in reservations:
            instances.extend(reservation.instances)
        return instances


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
        cluster = LaniakeaEngine(images)
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
                logging.info("%s - %s" % (cluster.state([instance]), instance.tags))
        return 0


if __name__ == "__main__":
    sys.exit(Laniakea.main())
