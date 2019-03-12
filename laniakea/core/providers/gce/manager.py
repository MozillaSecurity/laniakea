# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Google Compute Engine API"""
import sys
import logging

from laniakea.core.common import Common

logger = logging.getLogger('laniakea')

try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    from libcloud.common.google import InvalidRequestError
except ImportError as msg:
    logger.error(msg)
    sys.exit(-1)


class Filter:
    """Chainable filter class for Node objects.
    """

    def __init__(self, nodes=None):
        self.nodes = nodes

    def tags(self, tags=None):
        """Filter by tags.

        :param  tags: Tags to filter.
        :type   tags: ``list``

        :return: A list of Node objects.
        :rtype:  ``list`` of :class:`Node`
        """
        if tags is None or not tags:
            return self
        nodes = []
        for node in self.nodes:
            if any(tag in node.extra['tags'] for tag in tags):
                nodes.append(node)
        self.nodes = nodes
        return self

    def state(self, states=None):
        """Filter by state.

        :param  tags: States to filter.
        :type   tags: ``list``

        :return: A list of Node objects.
        :rtype:  ``list`` of :class:`Node`
        """
        if states is None or not states:
            return self
        nodes = []
        for node in self.nodes:
            if any(state.lower() == node.state.lower() for state in states):
                nodes.append(node)
        self.nodes = nodes
        return self

    def name(self, names=None):
        """Filter by node name.

        :param  names: Node names to filter.
        :type   names: ``list``

        :return: A list of Node objects.
        :rtype:  ``list`` of :class:`Node`
        """
        if names is None or not names:
            return self
        nodes = []
        for node in self.nodes:
            if any(name == node.name for name in names):
                nodes.append(node)
        self.nodes = nodes
        return self

    def is_preemptible(self):
        """Filter by preemptible scheduling.

        :return: A list of Node objects.
        :rtype:  ``list`` of :class:`Node`
        """
        nodes = []
        for node in self.nodes:
            if Kurz.is_preemtible(node):
                nodes.append(node)
        return self

    def expr(self, callback):
        """Filter by custom expression.

        :param  callback: Callback for custom expression.
        :type   name: ``function``

        :return: A list of Node objects.
        :rtype:  ``list`` of :class:`Node`
        """
        nodes = []
        for node in self.nodes:
            if callback(node):
                nodes.append(node)
        self.nodes = nodes
        return self


class Kurz:
    @staticmethod
    def is_preemtible(node):
        return node.extra['scheduling']['preemptible']

    @staticmethod
    def ips(node):
        if node.public_ips == [None]:
            return "N/A"
        return ','.join(node.public_ips)

    @staticmethod
    def zone(node):
        zone = node.extra.get('zone')
        if not zone:
            return "N/A"
        return zone.name


class ComputeEngineManagerException(Exception):
    """Exception class for Google Compute Engine Manager."""


class ComputeEngineManager:
    """Google Compute Engine Manager base class.
    """

    def __init__(self, user_id, key, project):
        """Initialize Compute Engine Manager

        :param   user_id: Email address (Service Accounts) or Client ID
        :type    user_id: ``str``

        :param   key: Key file path (Service Accounts) or Client Secret
        :type    key: ``str``

        :param   project: GCE project name
        :type    project: ``str``
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.user_id = user_id
        self.key = key
        self.project = project
        self.gce = None
        self.nodes = []

    def connect(self, **kwargs):
        """Connect to Google Compute Engine.
        """
        try:
            self.gce = get_driver(Provider.GCE)(
                self.user_id,
                self.key,
                project=self.project,
                **kwargs)
        except:
            raise ComputeEngineManagerException("Unable to connect to Google Compute Engine.")

    def assure_connection(self):
        """Reconnect if required.
        """
        if self.gce is None:
            self.connect()

    def create(self, size, number, meta, name=None, image=None):
        """Create container VM nodes. Uses a container declaration which is undocumented.

        :param   size: The machine type to use.
        :type    size: ``str`` or :class:`GCENodeSize`

        :param   number: Amount of nodes to be spawned.
        :type    number: ``int``

        :param   meta: Metadata dictionary for the nodes.
        :type    meta: ``dict`` or ``None``

        :param   name: The name of the node to create.
        :type    name: ``str``

        :param   image: The image used to create the disk - optional for multiple nodes.
        :type    image: ``str`` or :class:`GCENodeImage` or ``None``

        :return: A list of newly created Node objects for the new nodes.
        :rtype:  ``list`` of :class:`Node`
        """
        if name is None:
            name = Common.get_random_hostname()

        if image is None and number == 1:
            raise ComputeEngineManagerException("Base image not provided.")

        nodes = None
        try:
            if number == 1:
                # Used because of suffix naming scheme in ex_create_multiple_nodes() for a single node.
                nodes = [self.gce.create_node(name, size, image, **meta)]
            else:
                nodes = self.gce.ex_create_multiple_nodes(name, size, None, number,
                                                          ignore_errors=False,
                                                          poll_interval=1,
                                                          **meta)
        except Exception as err:
            raise ComputeEngineManagerException("Failed to create node: {}".format(err))

        self.nodes += nodes
        return nodes

    def stop(self, nodes=None):
        """Stop one or many nodes.

        :param   nodes: Nodes to be stopped.
        :type    nodes: ``list``
        """
        self.assure_connection()

        if nodes is None:
            nodes = []

        result = []
        for node in nodes:
            if node.state == 'stopped':
                logging.warning('Node %s is already "stopped".', node.name)
                continue
            try:
                status = self.gce.ex_stop_node(node)
                if status:
                    result.append(node)
            except InvalidRequestError as err:
                raise ComputeEngineManagerException(err)

        return result

    def start(self, nodes=None):
        """Start one or many nodes.

        :param   nodes: Nodes to be started.
        :type    nodes: ``list``
        """
        self.assure_connection()

        if nodes is None:
            nodes = []

        result = []
        for node in nodes:
            if node.state == 'running':
                logging.warning('Node %s is already "running".', node.name)
                continue
            try:
                status = self.gce.ex_start_node(node)
                if status:
                    result.append(node)
            except InvalidRequestError as err:
                raise ComputeEngineManagerException(err)

        return result

    def reboot(self, nodes=None):
        """Reboot one or many nodes.

        :param   nodes: Nodes to be rebooted.
        :type    nodes: ``list``
        """
        self.assure_connection()

        if nodes is None:
            nodes = []

        result = []
        for node in nodes:
            if node.state == 'stopped':
                logging.warning('Node %s is "stopped" and can not be rebooted.', node.name)
                continue
            try:
                status = self.gce.reboot_node(node)
                if status:
                    result.append(node)
            except InvalidRequestError as err:
                raise ComputeEngineManagerException(err)

        return result

    def terminate(self, nodes=None):
        """Destroy one or many nodes.

        :param   nodes: Nodes to be destroyed.
        :type    nodes: ``list``
        """
        self.assure_connection()

        if nodes is None:
            nodes = []
        result = self.gce.ex_destroy_multiple_nodes(nodes or self.nodes,
                                                    poll_interval=1,
                                                    ignore_errors=False)
        for i, success in enumerate(result):
            if success:
                logging.info('Destroyed: %s', nodes[i].name)
            else:
                logging.error('Failed to destroy: %s', nodes[i].name)

    def build_bootdisk(self, image, size=10, auto_delete=True):
        """Buid a disk struct.

        :param  image: Base image name.
        :type   image: ``str``

        :param  size: Persistent disk size.
        :type   size: ``int``

        :param  auto_delete: Wether to auto delete disk on instance termination.
        :type   auto_delete: ``bool``
        """
        if image is None:
            raise ComputeEngineManagerException("Image must not be None.")
        return {
            'boot': True,
            'autoDelete': auto_delete,
            'initializeParams': {
                'sourceImage': "projects/cos-cloud/global/images/{}".format(image),
                'diskSizeGb': size,
            }
        }

    def build_container_vm(self, container, disk, zone="us-east1-b", tags=None, preemptible=True):
        """Build kwargs for a container VM.

        :param   container: Container declaration.
        :type    container: ``dict``

        :param   disk: Disk definition structure.
        :type    disk: ``dict``

        :param   zone: The zone in which the instance should run.
        :type    zone: ``str``

        :param   tags: Tags associated with the instance.
        :type    tags: ``dict``

        :param   preemptible: Wether the instance is a preemtible or not.
        :type    preemptible: ``bool``
        """
        if tags is None:
            tags = []
        if container is None:
            raise ComputeEngineManagerException("Container declaration must not be None.")
        if disk is None:
            raise ComputeEngineManagerException("Disk structure must not be None.")
        return {
            'ex_metadata': {
                "gce-container-declaration": container,
                "google-logging-enabled": "true"
            },
            'location': zone,
            'ex_tags': tags,
            'ex_disks_gce_struct': [disk],
            'ex_preemptible': preemptible
        }

    def filter(self, zone='all'):
        """Filter nodes by their attributes.

        :param  zone: A zone containing nodes.
        :type   zone: ``str``

        :return: A chainable filter object.
        :rtype:  ``object`` of :class:`Filter`
        """
        self.assure_connection()

        nodes = self.gce.list_nodes(zone)
        return Filter(nodes)
