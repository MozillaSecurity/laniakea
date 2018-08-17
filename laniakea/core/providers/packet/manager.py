# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Packet Bare Metal API"""
import logging
import sys
import pprint
import random

logger = logging.getLogger('laniakea')

try:
    import packet
except ImportError as msg:
    logger.error(msg)
    sys.exit(-1)


class PacketManagerException(Exception):
    """Exception class for Packet Manager."""

    def __init__(self, message):
        super().__init__(message)


class PacketConfiguration:
    """Packet configuration class.
    """

    def __init__(self, conf):
        self.conf = conf

    def validate(self):
        """Perform some basic configuration validation.
        """
        if not self.conf.get('auth_token'):
            raise PacketManagerException('The auth token for Packet is not defined but required.')
        if not self.conf.get('projects'):
            raise PacketManagerException('Required "projects" section is missing.')
        else:
            projects = self.conf.get('projects')
            if not projects.keys():
                raise PacketManagerException('At least one project at Packet is required.')
            else:
                failure = False
                for project, identifier in projects.items():
                    if not identifier:
                        failure = True
                        logging.error('Project "%s" has no valid identifier.', project)
                if failure:
                    raise PacketManagerException('One or more projects are not setup appropriately.')


class PacketManager:
    """PacketManager base class.
    """

    def __init__(self, conf):
        self.logger = logging.getLogger(self.__class__.__name__)
        PacketConfiguration(conf).validate()
        self.conf = conf
        self.auth_token = self.conf.get('auth_token')
        self.manager = packet.Manager(auth_token=self.auth_token)
        self.api = self.manager.call_api

    def pprint(self, data):
        """Pretty print JSON.
        """
        pprint.PrettyPrinter(indent=2).pprint(data)

    def list_projects(self, params=None):
        """Retrieve list of available projects.
        """
        if params is None:
            params = {}
        return self.manager.list_projects(params)

    def print_projects(self, projects):
        """Print method for projects.
        """
        for project in projects:
            print('{}: {}'.format(project.name, project.id))

    def list_operating_systems(self, params=None):
        """Retrieve list of available operating systems.
        """
        if params is None:
            params = {}
        return self.manager.list_operating_systems(params)

    def print_operating_systems(self, operating_systems):
        """Print method for operating systems.
        """
        for _os in operating_systems:
            print('{}: {}'.format(_os.name, _os.slug))

    def list_plans(self, params=None):
        """Retrieve list of available plans.
        """
        if params is None:
            params = {}
        return self.manager.list_plans(params)

    def print_plans(self, plans):
        """Print method for plans.
        """
        for plan in plans:
            print('Name: {} "{}" Price: {} USD'.format(plan.name, plan.slug, plan.pricing['hour']))
            self.pprint(plan.specs)
            print('\n')

    def list_facilities(self, params=None):
        """Retrieve list of available facilities.
        """
        if params is None:
            params = {}
        return self.manager.list_facilities(params)

    def print_facilities(self, facilities):
        """Print method for facilities.
        """
        for facility in facilities:
            print('{} - ({}): {}'.format(facility.code, facility.name, ",".join(facility.features)))

    def list_spot_prices(self):
        """Retrieve list of current spot market prices.
        """
        prices = self.api('market/spot/prices')
        return prices

    def print_spot_prices(self, spot_prices):
        """Print method for spot prices.
        """
        self.pprint(spot_prices)

    def list_devices(self, project_id, conditions=None, params=None):
        """Retrieve list of devices in a project by one of more conditions.
        """
        default_params = {'per_page': 1000}
        if params:
            default_params.update(params)
        data = self.api('projects/%s/devices' % project_id, params=default_params)
        devices = []
        for device in self.filter(conditions, data['devices']):
            devices.append(packet.Device(device, self.manager))
        return devices

    def print_devices(self, devices):
        """Print method for devices.
        """
        for device in devices:
            print('ID: {} OS: {} IP: {} State: {} ({}) Tags: {}' \
                  .format(device.id,
                          device.operating_system.slug,
                          self.get_public_ip(device.ip_addresses),
                          device.state,
                          'spot' if device.spot_instance else 'on-demand',
                          device.tags))

    @staticmethod
    def filter(criterias, devices): # pylint: disable=too-many-branches
        """Filter a device by criterias on the root level of the dictionary.
        """
        if not criterias:
            return devices
        result = []
        for device in devices: # pylint: disable=too-many-nested-blocks
            for criteria_name, criteria_values in criterias.items():
                if criteria_name in device.keys():
                    if isinstance(device[criteria_name], list):
                        for criteria_value in criteria_values:
                            if criteria_value in device[criteria_name]:
                                result.append(device)
                                break
                    elif isinstance(device[criteria_name], str):
                        for criteria_value in criteria_values:
                            if criteria_value == device[criteria_name]:
                                result.append(device)
                    elif isinstance(device[criteria_name], int):
                        for criteria_value in criteria_values:
                            if criteria_value == device[criteria_name]:
                                result.append(device)
                    else:
                        continue
        return result

    @staticmethod
    def get_random_hostname():
        """Unique identifier for hostnames.
        """
        return str(hex(random.SystemRandom().getrandbits(64))[2:])

    @staticmethod
    def get_public_ip(addresses, version=4):
        """Return either the devices public IPv4 or IPv6 address.
        """
        for addr in addresses:
            if addr['public'] and addr['address_family'] == version:
                return addr.get('address')
        return None # pylint would complain about inconsistent-return-statements.

    def validate_capacity(self, servers):
        """Validates if a deploy can be fulfilled.
        """
        try:
            return self.manager.validate_capacity(servers)
        except packet.baseapi.Error as msg:
            raise PacketManagerException(msg)

    def create_volume(self, project_id, plan, size, facility, label=""):
        """Creates a new volume.
        """
        try:
            return self.manager.create_volume(project_id, label, plan, size, facility)
        except packet.baseapi.Error as msg:
            raise PacketManagerException(msg)

    def attach_volume_to_device(self, volume_id, device_id):
        """Attaches the created Volume to a Device.
        """
        try:
            volume = self.manager.get_volume(volume_id)
            volume.attach(device_id)
        except packet.baseapi.Error as msg:
            raise PacketManagerException(msg)
        return volume

    def create_demand(self,
                      project_id,
                      facility,
                      plan,
                      operating_system,
                      tags=None,
                      userdata='',
                      hostname=None,
                      count=1):
        """Create a new on demand device under the given project.
        """
        tags = {} if tags is None else tags
        hostname = self.get_random_hostname() if hostname is None else hostname
        devices = []
        for i in range(1, count + 1):
            new_hostname = hostname if count == 1 else hostname + '-' + str(i)
            self.logger.info('Adding to project %s: %s, %s, %s, %s, %r',
                             project_id,
                             new_hostname,
                             facility,
                             plan,
                             operating_system,
                             tags)
            try:
                device = self.manager.create_device(project_id=project_id,
                                                    hostname=new_hostname,
                                                    facility=facility,
                                                    plan=plan,
                                                    tags=tags,
                                                    userdata=userdata,
                                                    operating_system=operating_system)
                devices.append(device)
            except packet.baseapi.Error as msg:
                raise PacketManagerException(msg)
        return devices

    def create_spot(self,
                    project_id,
                    facility,
                    plan,
                    operating_system=None,
                    spot_price_max=-1,
                    tags=None,
                    userdata='',
                    hostname=None,
                    count=1):
        """Create a new spot device under the given project.
        """
        tags = {} if tags is None else tags
        hostname = self.get_random_hostname() if hostname is None else hostname
        devices = []
        for i in range(1, count + 1):
            new_hostname = hostname if count == 1 else hostname + '-' + str(i)
            try:
                self.logger.info('Adding to project %s: %s, %s, %f, %s, %s, %r',
                                 project_id,
                                 new_hostname,
                                 facility,
                                 spot_price_max,
                                 plan,
                                 operating_system,
                                 tags)
                device = self.manager.create_device(project_id=project_id,
                                                    hostname=new_hostname,
                                                    facility=facility,
                                                    spot_price_max=spot_price_max,
                                                    spot_instance=True,
                                                    plan=plan,
                                                    tags=tags,
                                                    userdata=userdata,
                                                    operating_system=operating_system)
                devices.append(device)
            except packet.baseapi.Error as msg:
                raise PacketManagerException(msg)
        return devices

    def stop(self, devices):
        """Power-Off one or more running devices.
        """
        for device in devices:
            self.logger.info('Stopping: %s', device.id)
            try:
                device.power_off()
            except packet.baseapi.Error:
                raise PacketManagerException('Unable to stop instance "{}"'.format(device.id))

    def reboot(self, devices):
        """Reboot one or more devices.
        """
        for device in devices:
            self.logger.info('Rebooting: %s', device.id)
            try:
                device.reboot()
            except packet.baseapi.Error:
                raise PacketManagerException('Unable to reboot instance "{}"'.format(device.id))

    def terminate(self, devices):
        """Terminate one or more running or stopped instances.
        """
        for device in devices:
            self.logger.info('Terminating: %s', device.id)
            try:
                device.delete()
            except packet.baseapi.Error:
                raise PacketManagerException('Unable to terminate instance "{}"'.format(device.id))
