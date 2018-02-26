# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os


class Focus(type):
    """
    Utility class for colorizing output on stdout/err.
    """
    COLORS = {
        'info': '\033[1;37m',
        'okay': '\033[92m',
        'warn': '\033[93m',
        'fail': '\033[91m',
        'repr': '\033[35m',
        'data': '\033[92m',
        'none': '\033[0m'
    }

    @staticmethod
    def init():
        if os.sys.platform == 'win32':
            Focus.disable()

    @staticmethod
    def disable():
        Focus.COLORS = dict((k, '') for k, v in Focus.COLORS.items())

    @staticmethod
    def format(color, msg):
        return '{}{}{}'.format(Focus.COLORS[color], msg, Focus.COLORS['none'])

    @staticmethod
    def fail(msg):
        return Focus.format('fail', msg)

    @staticmethod
    def okay(msg):
        return Focus.format('okay', msg)

    @staticmethod
    def warn(msg):
        return Focus.format('warn', msg)

    @staticmethod
    def repr(msg):
        return Focus.format('repr', msg)

    @staticmethod
    def info(msg):
        return Focus.format('info', msg)

    @staticmethod
    def data(msg):
        return Focus.format('data', msg)

class String(object):
    def __new__(self, u_or_str, encoding="utf-8"):
        return u_or_str if isinstance(u_or_str, str) else u_or_str.decode(encoding)
