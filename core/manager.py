# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging
import ssl
import sys
import time


try:
    import boto.ec2
    import boto.exception
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

    def retry_on_ec2_error(self, func, *args, **kwargs):
        """
        Call the given method with the given arguments, retrying if the call
        failed due to an EC2ResponseError. This method will wait at most 30
        seconds and perform up to 6 retries. If the method still fails, it will
        propagate the error.

        :param func: Function to call
        :type func: function
        """
        exception_retry_count = 6
        while True:
            try:
                return func(*args, **kwargs)
            except (boto.exception.EC2ResponseError, ssl.SSLError) as e:
                exception_retry_count -= 1
                if exception_retry_count <= 0:
                    raise e
                time.sleep(5)

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

        if self.images:
            # Resolve AMI names in our configuration to their IDs
            logging.info('Retrieving available AMIs...')
            remote_images = self.ec2.get_all_images(owners=['self', 'amazon', 'aws-marketplace'])
            for i in self.images:
                if "image_name" in self.images[i] and not 'image_id' in self.images[i]:
                    image_name = self.images[i]['image_name']
                    for ri in remote_images:
                        if ri.name == image_name:
                            if 'image_id' in self.images[i]:
                                raise Exception("Ambiguous AMI name '%s' resolves to multiple IDs" % image_name)
                            self.images[i]['image_id'] = ri.id
                            del self.images[i]['image_name']
                    if not 'image_id' in self.images[i]:
                        raise Exception("Failed to resolve AMI name '%s' to an AMI ID" % image_name)

    def create_on_demand(self, instance_type='default', tags=None, root_device_type='ebs',
                         size='default', vol_type='gp2', delete_on_termination=False):
        """Create one or more EC2 on-demand instances.

        :param instance_type: A section name in images.json
        :type instance_type: str
        :param tags:
        :type tags: dict
        :return: List of instances created
        :rtype: list
        """
        if root_device_type == 'ebs':
            self.images[instance_type]['block_device_map'] = self._configure_ebs_volume(vol_type, size, delete_on_termination)

        reservation = self.ec2.run_instances(**self.images[instance_type])

        logging.info('Creating requested tags...')
        for i in reservation.instances:
            self.retry_on_ec2_error(self.ec2.create_tags, [i.id], tags or {})

        instances = []
        logging.info('Waiting for instances to become ready...')
        while len(reservation.instances):
            for i in reservation.instances:
                if i.state == 'running':
                    instances.append(i)
                    reservation.instances.pop(reservation.instances.index(i))
                    logging.info('%s is %s at %s (%s)',
                                 i.id,
                                 i.state,
                                 i.public_dns_name,
                                 i.ip_address)
                else:
                    self.retry_on_ec2_error(i.update)
        return instances

    def create_spot_requests(self, price, instance_type='default', root_device_type='ebs',
                             size='default', vol_type='gp2', delete_on_termination=False):
        """Request creation of one or more EC2 spot instances.

        :param price: Max price to pay for spot instance per hour.
        :type price: float
        :param instance_type: A section name in images.json
        :type instance_type: str
        :param tags:
        :type tags: dict
        :return: List of requests created
        :rtype: list
        """
        if root_device_type == 'ebs':
            self.images[instance_type]['block_device_map'] = self._configure_ebs_volume(vol_type, size, delete_on_termination)

        requests = self.ec2.request_spot_instances(price, **self.images[instance_type])
        return [r.id for r in requests]

    def check_spot_requests(self, requests, tags=None):
        """Check status of one or more EC2 spot instance requests.

        :param requests: List of EC2 spot instance request IDs.
        :type requests: list
        :param tags:
        :type tags: dict
        :return: List of instances created, order corresponding to requests param (None if request still pending)
        :rtype: list
        """
        instances = [None] * len(requests)
        pending = self.retry_on_ec2_error(self.ec2.get_all_spot_instance_requests, request_ids=requests)

        for r in pending:
            if r.status.code == 'fulfilled':
                instance = None
                instance = self.retry_on_ec2_error(self.ec2.get_only_instances, r.instance_id)[0]

                if not instance:
                    raise Exception("Failed to get instance with id %s for fulfilled request %s" % (r.instance_id, r.id))

                instances[requests.index(r.id)] = instance
                self.retry_on_ec2_error(self.ec2.create_tags, [instance.id], tags or {})
                logging.info('Request %s is %s and %s.',
                             r.id,
                             r.status.code,
                             r.state)
                logging.info('%s is %s at %s (%s)',
                             instance.id,
                             instance.state,
                             instance.public_dns_name,
                             instance.ip_address)

        return instances

    def cancel_spot_requests(self, requests):
        """Cancel one or more EC2 spot instance requests.

        :param requests: List of EC2 spot instance request IDs.
        :type requests: list
        """
        pending = self.retry_on_ec2_error(self.ec2.get_all_spot_instance_requests, request_ids=requests)

        for r in pending:
            r.cancel()

    def create_spot(self, price, instance_type='default', tags=None, root_device_type='ebs',
                    size='default', vol_type='gp2', delete_on_termination=False, timeout=None):
        """Create one or more EC2 spot instances.

        :param price: Max price to pay for spot instance per hour.
        :type price: float
        :param instance_type: A section name in images.json
        :type instance_type: str
        :param tags:
        :type tags: dict
        :return: List of instances created
        :rtype: list
        """
        request_ids = self.create_spot_requests(price, instance_type=instance_type, root_device_type=root_device_type,
                                                size=size, vol_type=vol_type, delete_on_termination=delete_on_termination)
        instances = []
        logging.info("Waiting on fulfillment of requested spot instances.")
        poll_resolution = 5.0
        while request_ids:
            time.sleep(poll_resolution)

            new_instances = self.check_spot_requests(request_ids, tags=tags)

            if timeout is not None:
                timeout -= poll_resolution
                time_exceeded = timeout <= 0

            for idx, instance in reversed(enumerate(new_instances)):
                if instance is not None:
                    instances.append(instance)
                    request_ids.pop(idx)

            if request_ids and timeout_exceeded:
                self.cancel_spot_requests(request_ids)
                break

        return instances

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
        logging.info("%d instance/s are running.", running)
        logging.info("Scaling down %d instances of those.", count)
        if count > running:
            logging.info("Scale-down value is > than running instance/s - using maximum of %d!", running)
            count = running
        return i[:count]

    def _configure_ebs_volume(self, vol_type, size, delete_on_termination):
        """Sets the desired root EBS size, otherwise the default EC2 value is used.

        :param vol_type: Type of EBS storage - gp2 (SSD), io1 or standard (magnetic)
        :type vol_type: str
        :param size: Desired root EBS size.
        :type size: int
        :param delete_on_termination: Toggle this flag to delete EBS volume on termination.
        :type delete_on_termination: bool
        :return: A BlockDeviceMapping object.
        :rtype: object
        """
        # From GitHub boto docs: http://git.io/veyDv
        dev_sda1 = boto.ec2.blockdevicemapping.BlockDeviceType()
        dev_sda1.delete_on_termination = delete_on_termination
        dev_sda1.volume_type = vol_type
        if size != 'default':
            dev_sda1.size = size  # change root volume to desired size
        bdm = boto.ec2.blockdevicemapping.BlockDeviceMapping()
        bdm['/dev/sda1'] = dev_sda1
        return bdm

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

    def find(self, instance_ids=None, filters=None):
        """Flatten list of reservations to a list of instances.

        :param instance_ids: A list of instance ids to filter by
        :type instance_ids: list
        :param filters: A dict of |Filter.N| values defined in http://goo.gl/jYNej9
        :type filters: dict
        :return: A flattened list of filtered instances.
        :rtype: list
        """
        instances = []
        reservations = self.retry_on_ec2_error(self.ec2.get_all_instances, instance_ids=instance_ids, filters=filters)
        for reservation in reservations:
            instances.extend(reservation.instances)
        return instances
