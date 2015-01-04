# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import sys
import time
import logging

try:
    import boto.ec2
except ImportError as msg:
    logging.error(msg)
    sys.exit(-1)


class Laniakea(object):
    """
    Laniakea managing class.
    """

    def __init__(self, images):
        self.ec2 = None
        self.images = images

    def connect(self, region='us-west-2', **kw_params):
        """Connect to a EC2.

        :param region: The name of the region to connect to.
        :type region: str
        :param kw_params:
        :type kw_params: dict
        """
        self.ec2 = boto.ec2.connect_to_region(region, **kw_params)

    def create_on_demand(self, instance_type='default', tags=None):
        """Create one or more EC2 on-demand instances.

        :param instance_type: A section name in images.json
        :type instance_type: str
        :param tags:
        :type tags: dict
        """
        reservation = self.ec2.run_instances(**self.images[instance_type])
        self.ec2.create_tags([i.id for i in reservation.instances], tags or {})
        while len(reservation.instances):
            for i in reservation.instances:
                if i.state == 'pending':
                    i.update()
                else:
                    reservation.instances.pop(reservation.instances.index(i))
                    logging.info('%s is %s at %s (%s)',
                                 i.id,
                                 i.state,
                                 i.public_dns_name,
                                 i.ip_address)

    def create_spot(self, price, instance_type='default', tags=None):
        """Create one or more EC2 spot instances.

        :param price: Max price to pay for spot instance per hour.
        :type price: float
        :param instance_type: A section name in images.json
        :type instance_type: str
        :param tags:
        :type tags: dict
        """
        requests = self.ec2.request_spot_instances(price, **self.images[instance_type])
        request_ids = [r.id for r in requests]
        logging.info("Waiting on fulfillment of requested spot instances.")
        while len(request_ids):
            time.sleep(5.0)
            pending = self.ec2.get_all_spot_instance_requests(request_ids=request_ids)
            for r in pending:
                if r.status.code == 'fulfilled':
                    instance = self.ec2.get_only_instances(r.instance_id)[0]
                    self.ec2.create_tags([instance.id], tags or {})
                    instance.update()
                    logging.info('Request %s is %s and %s.',
                                 r.id,
                                 r.status.code,
                                 r.state)
                    logging.info('%s is %s at %s (%s)',
                                 instance.id,
                                 instance.state,
                                 instance.public_dns_name,
                                 instance.ip_address)
                    request_ids.pop(request_ids.index(r.id))

    def stop(self, instances):
        """Stop each provided running instances.

        :param instances: A list of instances.
        :type instances: list
        """
        if not instances:
            return
        self.ec2.stop_instances([i.id for i in instances])

    def terminate(self, instances):
        """Terminate each provided running or stopped instances.

        :param instances: A list of instances.
        :type instances: list
        """
        if not instances:
            return
        self.ec2.terminate_instances([i.id for i in instances])

    def find(self, filters=None):
        """Flatten list of reservations to a list of instances.

        :param filters: A dict of |Filter.N| values defined in http://goo.gl/jYNej9
        :type filters: dict
        :return: A flattened list of filtered instances.
        :rtype: list
        """
        instances = []
        reservations = self.ec2.get_all_instances(filters=filters or {})
        for reservation in reservations:
            instances.extend(reservation.instances)
        return instances
