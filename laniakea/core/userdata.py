# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import re
import os
import logging

from laniakea.core.common import String

logger = logging.getLogger("laniakea")


class UserDataException(Exception):
    """Exception class for Packet Manager."""

    def __init(self, message):
        super().__init__(message)


class UserData (object):
    """Utility functions for dealing with UserData scripts.
    """
    @staticmethod
    def convert_pair_to_dict(arg):
        """Utility function which transform k=v strings from the command-line into a dict.
        """
        return dict(kv.split('=', 1) for kv in arg)

    @staticmethod
    def parse_only_criterias(conditions):
        result = {}
        for kv in conditions:
            k, v = kv.split('=', 1)
            if "," in v:
                result[k] = v.split(',', 1)
            else:
                result[k] = [v]
        return result

    @staticmethod
    def convert_str_to_int(arg):
        """
        """
        # Todo: Convert certain values of keys from images.json to ints.
        for k, v in list(arg.items()):
            try:
                arg[String(k)] = int(v)
            except ValueError as e: # noqa: ignore=F841
                # Let's assume it is a str and move on.
                pass
        return arg

    @staticmethod
    def list_tags(userdata):
        """
        """
        macros = re.findall('@(.*?)@', userdata)
        logging.info('List of available macros:')
        for m in macros:
            logging.info('\t%r', m)

    @staticmethod
    def handle_tags(userdata, macros):
        """
        """
        macro_vars = re.findall('@(.*?)@', userdata)
        for macro_var in macro_vars:
            if macro_var == '!all_macros_export':
                macro_var_export_list = []
                for defined_macro in macros:
                    macro_var_export_list.append('export %s="%s"' % (defined_macro, macros[defined_macro]))
                macro_var_exports = "\n".join(macro_var_export_list)

                userdata = userdata.replace('@%s@' % macro_var, macro_var_exports)
            elif macro_var == "!all_macros_docker":
                macro_var_export_list = []
                for defined_macro in macros:
                    macro_var_export_list.append("-e '%s=%s'" % (defined_macro, macros[defined_macro]))
                macro_var_exports = " ".join(macro_var_export_list)

                userdata = userdata.replace('@%s@' % macro_var, macro_var_exports)
            elif macro_var not in macros:
                logging.error('Undefined variable @%s@ in UserData script', macro_var)
                return
            else:
                userdata = userdata.replace('@%s@' % macro_var, macros[macro_var])

        return userdata

    @staticmethod
    def handle_import_tags(userdata, import_root):
        """Handle @import(filepath)@ tags in a UserData script.

        :param userdata: UserData script content.
        :type userdata: str
        :return: UserData script with the contents of the imported files.
        :rtype: str
        """
        imports = re.findall('@import\((.*?)\)@', userdata)
        if not imports:
            return userdata

        for filepath in imports:
            logger.info('Processing "import" of %s', filepath)
            import_path = os.path.join(import_root, filepath)
            try:
                with open(import_path) as fo:
                    content = fo.read()
                    userdata = userdata.replace('@import(%s)@' % filepath, content)
            except FileNotFoundError:
                raise UserDataException('Import path {} not found.'.format(import_path))

        return userdata
