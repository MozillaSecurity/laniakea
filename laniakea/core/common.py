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
    def __new__(self, u_or_str, encoding='utf-8'):
        return u_or_str if isinstance(u_or_str, str) else u_or_str.decode(encoding)


class FlatJSON():
    def __new__(self, y):
        out = dict()

        def flatten(x, name=''):
            if type(x) is dict:
                for a in x:
                    flatten(x[a], name + a + '.')
            elif type(x) is list:
                for i, a in enumerate(x):
                    flatten(a, name + str(i) + '.')
            else:
                out[name[:-1]] = x

        flatten(y)
        return out


class AttributeTree(dict):

    def __init__(self, value=None):
        if value is None:
            pass
        elif isinstance(value, dict):
            for key in value:
                self.__setitem__(key, value[key])
        else:
            raise TypeError('Expected dict()')

    def __setitem__(self, key, value):
        if '.' in key:
            my_key, rest_of_key = key.split('.', 1)
            target = self.setdefault(my_key, AttributeTree())
            if not isinstance(target, AttributeTree):
                raise KeyError('Can not set "%s" in "%s" (%s)' % (rest_of_key, my_key, repr(target)))
            target[rest_of_key] = value
        else:
            if isinstance(value, dict) and not isinstance(value, AttributeTree):
                value = AttributeTree(value)
            dict.__setitem__(self, key, value)

    def __getitem__(self, key):
        if '.' not in key:
            return dict.__getitem__(self, key)
        my_key, rest_of_key = key.split('.', 1)
        target = dict.__getitem__(self, my_key)
        if not isinstance(target, AttributeTree):
            raise KeyError('Can not get "%s" in "%s" (%s)' % (rest_of_key, my_key, repr(target)))
        return target[rest_of_key]

    def __contains__(self, key):
        if '.' not in key:
            return dict.__contains__(self, key)
        my_key, rest_of_key = key.split('.', 1)
        target = dict.__getitem__(self, my_key)
        if not isinstance(target, AttributeTree):
            return False
        return rest_of_key in target

    def setdefault(self, key, default):
        if key not in self:
            self[key] = default
        return self[key]

    __setattr__ = __setitem__
    __getattr__ = __getitem__
