# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import logging
import argparse

from laniakea.core.common import Focus, String

from .manager import AzureManager

logger = logging.getLogger("Laniakea")


class AzureCommandLine(object):
    """
    Sub command-line interface for the Microsoft Azure provider.
    """
    HOME = os.path.dirname(os.path.abspath(__file__))
    VERSION = 0.1

    @classmethod
    def add_arguments(cls, subparsers):
        parser = subparsers.add_parser('azure',
                                       help='Microsoft Azure',
                                       formatter_class=lambda prog:
                                           argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=30, width=100))

        parser.add_argument('-version', action='version', version='%(prog)s {}'.format(cls.VERSION),
                            help=argparse.SUPPRESS)

    @classmethod
    def main(self, args):
        cluster = AzureManager()
