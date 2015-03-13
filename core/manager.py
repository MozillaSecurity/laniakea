# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import sys
import time
import logging

try:
    import boto.ec2
    import boto.exception
except ImportError as msg:
    logging.error(msg)
    sys.exit(-1)


def retry_on_ec2_error(method):
    """Decorator to use with EC2 methods that can temporarily fail.
    """
    def decorator(self, *args, **options):
        exception_retry_count = 3
        while True:
            try:
                return method(self, *args, **options)
            except boto.exception.EC2ResponseError as e:
                exception_retry_count -= 1
                if exception_retry_count <= 0:
                    raise e
                time.sleep(1)
    return decorator 


class Laniakea(object):
    """
    Laniakea managing class.
    """

    def __init__(self, images):
        self.ec2 = None
        self.images = images

    @retry_on_ec2_error
    def __create_tags(self, instance, tags):
        return self.ec2.create_tags([instance.id], tags or {})

    @retry_on_ec2_error
    def __update(self, instance):
        return instance.update()

    def connect(self, region, **kw_params):
        """Connect to a EC2.

        :param region: The name of the region to connect to.
        :type region: str
        :param kw_params:
        :type kw_params: dict
        """
        self.ec2 = boto.ec2.connect_to_region(region, **kw_params)
        if not self.ec2:
            raise Exception("Unable to connect to region '%s'" % region)

    def create_on_demand(self, instance_type='default', tags=None):
        """Create one or more EC2 on-demand instances.

        :param instance_type: A section name in images.json
        :type instance_type: str
        :param tags:
        :type tags: dict
        """
        reservation = self.ec2.run_instances(**self.images[instance_type])

        logging.info('Creating requested tags...')
        for i in reservation.instances:
            self.__create_tags(i, tags)

        logging.info('Waiting for instances to become ready...')
        while len(reservation.instances):
            for i in reservation.instances:
                if i.state == 'running':
                    reservation.instances.pop(reservation.instances.index(i))
                    logging.info('%s is %s at %s (%s)',
                                 i.id,
                                 i.state,
                                 i.public_dns_name,
                                 i.ip_address)
                else:
                    self.__update(i)

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

    def _scale_down(self, instances, count):
        """Return a list of |count| last created instances by launch time.

        :param instances: A list of instances.
        :type instances: list
        :param count: Number of instances to scale down.
        :type count: integer
        :return: List of instances to be scaled down.
        :rtype: list
        """
        i = sorted(instances, key=lambda i: i.launch_time, reverse=True)
        if not i:
            return []
        running = len(i)
        logging.info("%d instance/s are running." % running)
        logging.info("Scaling down %d instances of those." % count)
        if count > running:
            logging.info("Scale-down value is > than running instance/s - using maximum of %d!" % running)
            count = running
        return i[0:count]

    def stop(self, instances, count=0):
        """Stop each provided running instance.

        :param instances: A list of instances.
        :type instances: list
        """
        if not instances:
            return
        if count > 0:
            instances = self._scale_down(instances, count)
        self.ec2.stop_instances([i.id for i in instances])

    def terminate(self, instances, count=0):
        """Terminate each provided running or stopped instance.

        :param instances: A list of instances.
        :type instances: list
        """
        if not instances:
            return
        if count > 0:
            instances = self._scale_down(instances, count)
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
