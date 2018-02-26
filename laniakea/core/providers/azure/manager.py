# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging


logger = logging.getLogger("laniakea")


class AzureManager(object):
    """
    Microsoft Azure manager class.
    """

    def __init__(self):
        self.azure = None

    def connect(self):
        raise NotImplementedError

    def create(self):
        raise NotImplementedError

    def create_spot(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def terminate(self):
        raise NotImplementedError
