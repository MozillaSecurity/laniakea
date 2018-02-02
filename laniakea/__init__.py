# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Laniakea is a utility for managing EC2 instances at AWS and aids in setting up a fuzzing cluster.
"""
import appdirs
import argparse
import boto.exception
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys

from .core.common import Focus, String
from .core.manager import Laniakea


class LaniakeaCommandLine(object):
    """
    Command-line interface for Laniakea.
    """
    HOME = os.path.dirname(os.path.abspath(__file__))
    VERSION = 0.6

    @classmethod
    def parse_args(cls):
        parser = argparse.ArgumentParser(description='Laniakea Runtime',
                                         prog='laniakea',
                                         add_help=False,
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                         epilog='The exit status is 0 for non-failures and 1 for failures.')

        dirs = appdirs.AppDirs("laniakea", "Mozilla Security")
        if not os.path.isdir(dirs.user_config_dir):
            shutil.copytree(os.path.join(cls.HOME, 'examples'), dirs.user_config_dir)

        m = parser.add_argument_group('Mandatory Arguments')

        g = m.add_mutually_exclusive_group(required=True)
        g.add_argument('-create-on-demand', action='store_true', help='Create on-demand instances')
        g.add_argument('-create-spot', action='store_true', help='Create spot instances')
        g.add_argument('-stop', nargs='?', const=-1, metavar='n', help='Stop active instances')
        g.add_argument('-terminate', nargs='?', const=-1, metavar='n', help='Terminate active instances')
        g.add_argument('-status', action='store_true', help='List current state of instances')
        g.add_argument('-run', metavar='cmd', type=str, default='', help='Execute commands via SSH')
        g.add_argument('-list-userdata-macros', action='store_true', help='List available macros')
        g.add_argument('-print-userdata', action='store_true', help='Print the UserData script to stdout')

        u = parser.add_argument_group('UserData Arguments')
        u.add_argument('-userdata', metavar='path', type=argparse.FileType(),
                       default=os.path.join(cls.HOME, 'userdata', 'default.sh'),
                       help='UserData script for cloud-init')
        u.add_argument('-userdata-macros', metavar='k=v', nargs='+', type=str, help='Custom macros')

        o = parser.add_argument_group('Optional Arguments')
        o.add_argument('-tags', metavar='k=v', nargs='+', type=str, help='Assign tags to instances')
        o.add_argument('-only', metavar='k=v', nargs='+', type=str, help='Filter instances')
        o.add_argument('-images', metavar='path', type=argparse.FileType(),
                       default=os.path.join(dirs.user_config_dir, 'images.json'),
                       help='EC2 image definitions')
        o.add_argument('-image-name', metavar='str', type=str, default='default', help='Name of image definition')
        o.add_argument('-image-args', metavar='k=v', nargs='+', type=str, help='Custom image arguments')
        o.add_argument('-profile', metavar='str', type=str, default='laniakea', help='AWS profile name in .boto')
        o.add_argument('-max-spot-price', metavar='#', type=float, default=0.05, help='Max price for spot instances')
        o.add_argument('-region', type=str, default='us-west-2', help='EC2 region')
        o.add_argument('-zone', type=str, default=None, help='EC2 placement zone')
        o.add_argument('-root-device-type', type=str, default='ebs', choices=['ebs', 'instance_store'],
                       help='EC2 placement zone')
        o.add_argument('-ebs-size', type=int, default=None, help='Sets the root disk space size. If unset, the EC2 default is used.')
        o.add_argument('-ebs-volume-type', type=str, default='gp2', choices=['gp2', 'io1', 'standard'],
                       help='Sets the root disk volume type.')
        o.add_argument('-ebs-volume-delete-on-termination', action='store_true', default=False,
                       help='Set this to delete the root EBS volume on termination.')
        o.add_argument('-verbosity', default=2, type=int, choices=list(range(1, 6, 1)),
                       help='Log level for the logging module')
        o.add_argument('-focus', action='store_true', default=False, help=argparse.SUPPRESS)
        o.add_argument('-settings', metavar='path', type=argparse.FileType(),
                       default=os.path.join(dirs.user_config_dir, 'laniakea.json'), help='Laniakea settings')
        o.add_argument('-h', '-help', '--help', action='help', help=argparse.SUPPRESS)
        o.add_argument('-version', action='version', version='%(prog)s {}'.format(cls.VERSION),
                       help=argparse.SUPPRESS)

        return parser.parse_args()

    @staticmethod
    def _convert_pair_to_dict(arg):
        """Utility function which transform k=v strings from the command-line into a dict."""
        return dict(kv.split('=', 1) for kv in arg)

    @staticmethod
    def _convert_str_to_int(arg):
        # FIXME: Convert certain values of keys from images.json to ints.
        for k, v in list(arg.items()):
            try:
                arg[String(k)] = int(v)
            except ValueError as e:
                # Let's assume it is a str and move on.
                pass
        return arg

    @staticmethod
    def list_tags(userdata):
        macros = re.findall("@(.*?)@", userdata)
        logging.info("List of available macros:")
        for m in macros:
            logging.info('\t%r', m)

    @staticmethod
    def handle_tags(userdata, macros):
        macro_vars = re.findall("@(.*?)@", userdata)
        for macro_var in macro_vars:
            if macro_var == "!all_macros_export":
                macro_var_export_list = []
                for defined_macro in macros:
                    macro_var_export_list.append("export %s='%s'" % (defined_macro, macros[defined_macro]))
                macro_var_exports = "\n".join(macro_var_export_list)

                userdata = userdata.replace('@%s@' % macro_var, macro_var_exports)
            elif macro_var not in macros:
                logging.error('Undefined variable @%s@ in UserData script', macro_var)
                return
            else:
                userdata = userdata.replace('@%s@' % macro_var, macros[macro_var])

        return userdata

    @staticmethod
    def handle_import_tags(userdata):
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
            logging.info('Processing "import" of %s', filepath)
            with open(filepath) as fp:
                content = fp.read()
                userdata = userdata.replace("@import(%s)@" % filepath, content)
        return userdata

    @classmethod
    def main(cls):
        args = cls.parse_args()

        logging.basicConfig(format='[Laniakea] %(asctime)s %(levelname)s: %(message)s',
                            level=args.verbosity * 10,
                            datefmt='%Y-%m-%d %H:%M:%S')

        logging.info('Loading Laniakea configuration from %s', args.settings.name)
        try:
            settings = json.loads(args.settings.read())
        except ValueError as msg:
            logging.error('Unable to parse %s: %s', args.settings.name, msg)
            return 1

        Focus.init() if args.focus else Focus.disable()

        args.only = cls._convert_pair_to_dict(args.only or "")
        args.tags = cls._convert_pair_to_dict(args.tags or "")
        args.image_args = cls._convert_str_to_int(cls._convert_pair_to_dict(args.image_args or {}))

        logging.info('Using image definition "%s" from %s', Focus.info(args.image_name), Focus.info(args.images.name))
        try:
            images = json.loads(args.images.read())
        except ValueError as msg:
            logging.error('Unable to parse %s: %s', args.images.name, msg)
            return 1

        logging.info('Reading user data script content from %s', Focus.info(args.userdata.name))
        userdata = args.userdata.read()
        if args.list_userdata_macros:
            cls.list_tags(userdata)
            return 0
        userdata = cls.handle_import_tags(userdata)

        args.userdata_macros = cls._convert_pair_to_dict(args.userdata_macros or "")
        userdata = cls.handle_tags(userdata, args.userdata_macros)

        if args.print_userdata:
            logging.info("Combined user-data script:")
            print(userdata)
            return 0

        if not userdata:
            return 1

        images[args.image_name]['user_data'] = userdata

        if args.image_args:
            logging.info("Setting custom image parameters for upcoming instances: %r ", args.image_args)
            images[args.image_name].update(args.image_args)

        logging.info('Using Boto configuration profile "%s"', Focus.info(args.profile))

        # If a zone has been specified on the command line, use that for all of our images
        if args.zone:
            for image_name in images:
                images[image_name]['placement'] = args.zone

        cluster = Laniakea(images)
        try:
            cluster.connect(profile_name=args.profile, region=args.region)
        except Exception as msg:
            logging.error(msg)
            return 1

        if args.create_on_demand:
            try:
                cluster.create_on_demand(args.image_name, args.tags, args.root_device_type, args.ebs_size,
                                         args.ebs_volume_type, args.ebs_volume_delete_on_termination)
            except boto.exception.EC2ResponseError as msg:
                logging.error(msg)
                return 1

        if args.create_spot:
            try:
                cluster.create_spot(args.max_spot_price, args.image_name, args.tags, args.root_device_type, args.ebs_size,
                                    args.ebs_volume_type, args.ebs_volume_delete_on_termination)
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

        if args.run:
            ssh = settings.get('SSH')
            if not ssh:
                logging.error('No SSH settings defined in %s', args.settings.name)
                return 1

            identity = ssh.get('identity')
            if not identity:
                logging.error('Key for SSH is not defined.')
                return 1
            identity = os.path.expanduser(identity)

            username = ssh.get('username')
            if not username:
                logging.error('User for SSH is not defined.')
                return 1

            logging.info("Bucketing available instances.")
            hosts = []
            try:
                for host in cluster.find(filters=args.only):
                    hosts.append(host)
            except boto.exception.EC2ResponseError as msg:
                logging.error(msg)
                return 1
            logging.info("Executing remote commands on %d instances.", len(hosts))

            # Be able to extend ssh_command from settings.json
            ssh_command = ['ssh',
                           '-o' 'UserKnownHostsFile=/dev/null',
                           '-o' 'StrictHostKeyChecking=no',
                           '-o' 'LogLevel=error',
                           '-i', '%s' % identity]

            for host in hosts:
                command = []
                command.extend(ssh_command)
                command.append('%s@%s' % (username, host.ip_address))
                command.extend(shlex.split(args.run))
                logging.info('Running remote command [%s]: %s', host.ip_address, args.run)
                try:
                    print(subprocess.check_output(command))
                except subprocess.CalledProcessError as msg:
                    logging.error(msg)

        return 0
