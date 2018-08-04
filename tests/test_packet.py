# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Tests for Packet.
"""
import os
import json
import pytest

from laniakea.core.providers.packet import PacketManager

#@pytest.fixture
#def packet():
#    with open(os.path.join(os.getcwd(), 'laniakea/examples/packet.json')) as fo:
#        conf = json.loads(fo.read())
#    return PacketManager(conf)


#def test_list_projects(packet):
#    for plan in packet.list_projects():
#        assert hasattr(plan, 'name')
#        assert hasattr(plan, 'id')
