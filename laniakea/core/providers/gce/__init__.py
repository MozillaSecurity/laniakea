# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Google Compute Engine CLI"""
import os
import json
import logging
import argparse

from laniakea.core.common import Focus, Common
from laniakea.core.userdata import UserData
from .manager import ComputeEngineManager, ComputeEngineManagerException, Kurz

logger = logging.getLogger('laniakea')


class GceCommandLine:
    """
    Sub command-line interface for the Google Compute Engine provider.
    """
    HOME = os.path.dirname(os.path.abspath(__file__))
    VERSION = 0.1

    @classmethod
    def add_arguments(cls, subparsers, dirs):
        """Argument parser of this module.
        """
        parser = subparsers.add_parser(
            'gce',
            help='Google Compute Engine',
            formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=40, width=120))

        m = parser.add_argument_group('Mandatory Compute Engine Parameters')  # pylint: disable=invalid-name

        g = m.add_mutually_exclusive_group(required=False)  # pylint: disable=invalid-name
        g.add_argument('-create',
                       action='store_true',
                       help='Create Compute Engine VMs.')

        g.add_argument('-start',
                       action='store_true',
                       help='Start stopped instances.')

        g.add_argument('-reboot',
                       action='store_true',
                       help='Reboot running instances.')

        g.add_argument('-stop',
                       action='store_true',
                       help='Stop running instances.')

        g.add_argument('-terminate',
                       action='store_true',
                       help='Terminate instances.')

        o = parser.add_argument_group('Optional Parameters')  # pylint: disable=invalid-name
        o.add_argument('-conf',
                       metavar='path',
                       type=argparse.FileType(),
                       default=os.path.join(dirs.user_config_dir, 'examples', 'gce.json'),
                       help='Google Compute configuration')

        o.add_argument('-declaration',
                       metavar='path',
                       type=argparse.FileType(),
                       default=os.path.join(dirs.user_config_dir, 'userdata', 'gce', 'fuzzos.yml'),
                       help='Google Compute configuration')

        o.add_argument('-tags',
                       metavar='seq',
                       nargs='+',
                       default=[],
                       help='Tags associated with an instance.')

        o.add_argument('-zone',
                       metavar='zone',
                       type=str,
                       default='us-east1-b',
                       help='Where the instance is going to run. "all" for some operations.')

        o.add_argument('-size',
                       metavar='name',
                       type=str,
                       default="n1-standard-8",
                       help='The instance size for the created VM.')

        o.add_argument('-image',
                       metavar='name',
                       type=str,
                       default='cos-stable-71-11151-71-0',
                       help='The operating system for the created instance.')

        o.add_argument('-count',
                       metavar='#',
                       type=int,
                       default='1',
                       help='The amount of nodes to be spawned.')

        o.add_argument('-disk-size',
                       metavar='#',
                       type=int,
                       default='10',
                       help='Persistent boot disk size.')

        o.add_argument('-disk-auto-delete',
                       action='store_true',
                       default=True,
                       help='Automatically delete the disk on VM termination.')

        o.add_argument('-preemptible',
                       action='store_true',
                       default=False,
                       help='Use preemptible instances (max 24h runtime).')

        o.add_argument('-list',
                       action='store_true',
                       default=False,
                       help='List instances.')

        o.add_argument('-states',
                       metavar='seq',
                       nargs='+',
                       default=[],
                       help='States used for filtering.')

        o.add_argument('-names',
                       metavar='seq',
                       nargs='+',
                       default=[],
                       help='Names used for filtering.')

        o.add_argument('-version',
                       action='version',
                       version='%(prog)s {}'.format(cls.VERSION),
                       help=argparse.SUPPRESS)

    def list(self, cluster, zone, states, names, tags):
        logger.info("Collecting nodes ...")
        nodes = cluster.filter(zone).state(states).name(names).tags(tags).nodes
        logger.info("Found %d matching node%s.", len(nodes), Common.pluralize(nodes))
        return nodes

    @classmethod
    def main(cls, args, settings=None, userdata=None):  # pylint: disable=too-many-branches,too-many-statements
        """Main entry point of this module.
        """
        # The command-line client uses Service Account authentication.
        logger.info('Using Compute Engine credentials from %s', Focus.info(args.conf.name))
        try:
            key = json.loads(args.conf.read())
        except ValueError as msg:
            logger.error('Unable to parse %s: %s', args.conf.name, msg)
            return 1

        # Compute Engine Manager
        try:
            cluster = ComputeEngineManager(key['client_email'], args.conf.name, key['project_id'])
            cluster.connect()
            # Remove read |key| from memory which contains the private key.
            del key
        except ComputeEngineManagerException as msg:
            logger.error(msg)
            return 1

        # Create one or many compute VMs.
        if args.create:
            if args.tags:
                logger.info('Assigning the following tags to the instance: %r', args.tags)

            container_declaration = args.declaration.read()
            try:
                disk = cluster.build_bootdisk(args.image, args.disk_size, args.disk_auto_delete)
                conf = cluster.build_container_vm(container_declaration, disk,
                                                  zone=args.zone,
                                                  tags=args.tags,
                                                  preemptible=args.preemptible)
            except ComputeEngineManagerException as msg:
                logging.error(msg)
                return 1

            logging.debug('VM Configuration: %r', conf)
            try:
                logging.info('Creating %d VM%s of type "%s" ...',
                             args.count, Common.pluralize(args.count), args.size)
                nodes = cluster.create(args.size, args.count, conf, image=args.image)
                for node in nodes:
                    logging.info('Node %s created and %s.', node.name, node.state)
            except ComputeEngineManagerException as msg:
                logging.error(msg)
                return 1

        # Run filters before dealing with any state routine.
        nodes = []
        if any([args.stop, args.start, args.reboot, args.terminate]):
            nodes = cls.list(cls, cluster, args.zone, args.states, args.names, args.tags)

        # Routines for other VM states.
        if args.start:
            try:
                logger.info("Starting %d node%s ...", len(nodes), Common.pluralize(nodes))
                cluster.start(nodes)
            except ComputeEngineManagerException as msg:
                logger.error(msg)
                return 1

        if args.stop:
            try:
                logger.info("Stopping %d node%s ...", len(nodes), Common.pluralize(nodes))
                cluster.stop(nodes)
            except ComputeEngineManagerException as msg:
                logger.error(msg)
                return 1

        if args.reboot:
            try:
                logger.info("Rebooting %d node%s ...", len(nodes), Common.pluralize(nodes))
                cluster.reboot(nodes)
            except ComputeEngineManagerException as msg:
                logger.error(msg)
                return 1

        if args.terminate:
            try:
                logger.info("Terminating %d node%s ...", len(nodes), Common.pluralize(nodes))
                cluster.terminate(nodes)
            except ComputeEngineManagerException as msg:
                logger.error(msg)
                return 1

        if args.list:
            try:
                nodes = cls.list(cls, cluster, args.zone, args.states, args.names, args.tags)
                for node in nodes:
                    logging.info('Node: %s is %s; IP: %s (%s); Preemtible: %s',
                                 node.name, node.state,
                                 Kurz.ips(node), Kurz.zone(node), Kurz.is_preemtible(node))
            except ComputeEngineManagerException as msg:
                logger.error(msg)
                return 1

        return 0
