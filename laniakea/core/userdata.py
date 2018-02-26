# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import re
import logging

from laniakea.core.common import String

logger = logging.getLogger("laniakea")


class UserData (object):
    """Utility functions for dealing with UserData scripts.
    """
    @staticmethod
    def convert_pair_to_dict(arg):
        """Utility function which transform k=v strings from the command-line into a dict.
        """
        return dict(kv.split('=', 1) for kv in arg)

    @staticmethod
    def convert_str_to_int(arg):
        """
        """
        # Todo: Convert certain values of keys from images.json to ints.
        for k, v in list(arg.items()):
            try:
                arg[String(k)] = int(v)
            except ValueError as e:
                # Let's assume it is a str and move on.
                pass
        return arg

    @staticmethod
    def list_tags(userdata):
        """
        """
        macros = re.findall("@(.*?)@", userdata)
        logging.info("List of available macros:")
        for m in macros:
            logging.info('\t%r', m)

    @staticmethod
    def handle_tags(userdata, macros):
        """
        """
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
            logger.info('Processing "import" of %s', filepath)
            with open(filepath) as fp:
                content = fp.read()
                userdata = userdata.replace("@import(%s)@" % filepath, content)
        return userdata
