# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Amazon Elastic Cloud Computing API"""
import datetime
import logging
import ssl
import sys
import time

logger = logging.getLogger('laniakea')

try:
    import boto.ec2
    import boto.exception
except ImportError as msg:
    logger.error(msg)
    sys.exit(-1)


class EC2ManagerException(Exception):
    """Exception class for Azure Manager."""

    def __init(self, message):
        super().__init__(message)


class EC2Manager:
    """
    Amazon Elastic Cloud Computing manager class.
    """

    def __init__(self, images):
        self.ec2 = None
        self.images = images
        self.remote_images = {}

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
            except (boto.exception.EC2ResponseError, ssl.SSLError) as msg:
                exception_retry_count -= 1
                if exception_retry_count <= 0:
                    raise msg
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
            raise EC2ManagerException('Unable to connect to region "%s"' % region)
        self.remote_images.clear()

        if self.images and any(('image_name' in img and 'image_id' not in img) for img in self.images.values()):
            for img in self.images.values():
                if 'image_name' in img and 'image_id' not in img:
                    img['image_id'] = self.resolve_image_name(img.pop('image_name'))

    def resolve_image_name(self, image_name):
        """Look up an AMI for the connected region based on an image name.

        :param image_name: The name of the image to resolve.
        :type image_name: str
        :return: The AMI for the given image.
        :rtype: str
        """
        # look at each scope in order of size
        scopes = ['self', 'amazon', 'aws-marketplace']
        if image_name in self.remote_images:
            return self.remote_images[image_name]
        for scope in scopes:
            logger.info('Retrieving available AMIs owned by %s...', scope)
            remote_images = self.ec2.get_all_images(owners=[scope], filters={'name': image_name})
            self.remote_images.update({ri.name: ri.id for ri in remote_images})
            if image_name in self.remote_images:
                return self.remote_images[image_name]
        raise EC2ManagerException('Failed to resolve AMI name "%s" to an AMI' % image_name)

    def create_on_demand(self,
                         instance_type='default',
                         tags=None,
                         root_device_type='ebs',
                         size='default',
                         vol_type='gp2',
                         delete_on_termination=False):
        """Create one or more EC2 on-demand instances.

        :param size: Size of root device
        :type size: int
        :param delete_on_termination:
        :type delete_on_termination: boolean
        :param vol_type:
        :type vol_type: str
        :param root_device_type: The type of the root device.
        :type root_device_type: str
        :param instance_type: A section name in amazon.json
        :type instance_type: str
        :param tags:
        :type tags: dict
        :return: List of instances created
        :rtype: list
        """
        name, size = self._get_default_name_size(instance_type, size)

        if root_device_type == 'ebs':
            self.images[instance_type]['block_device_map'] = \
                self._configure_ebs_volume(vol_type, name, size, delete_on_termination)

        reservation = self.ec2.run_instances(**self.images[instance_type])

        logger.info('Creating requested tags...')
        for i in reservation.instances:
            self.retry_on_ec2_error(self.ec2.create_tags, [i.id], tags or {})

        instances = []
        logger.info('Waiting for instances to become ready...')
        while len(reservation.instances): # pylint: disable=len-as-condition
            for i in reservation.instances:
                if i.state == 'running':
                    instances.append(i)
                    reservation.instances.pop(reservation.instances.index(i))
                    logger.info('%s is %s at %s (%s)',
                                i.id,
                                i.state,
                                i.public_dns_name,
                                i.ip_address)
                else:
                    self.retry_on_ec2_error(i.update)
        return instances

    def create_spot_requests(self,
                             price,
                             instance_type='default',
                             root_device_type='ebs',
                             size='default',
                             vol_type='gp2',
                             delete_on_termination=False,
                             timeout=None):
        """Request creation of one or more EC2 spot instances.

        :param size:
        :param vol_type:
        :param delete_on_termination:
        :param root_device_type: The type of the root device.
        :type root_device_type: str
        :param price: Max price to pay for spot instance per hour.
        :type price: float
        :param instance_type: A section name in amazon.json
        :type instance_type: str
        :param timeout: Seconds to keep the request open (cancelled if not fulfilled).
        :type timeout: int
        :return: List of requests created
        :rtype: list
        """
        name, size = self._get_default_name_size(instance_type, size)

        if root_device_type == 'ebs':
            self.images[instance_type]['block_device_map'] = \
                self._configure_ebs_volume(vol_type, name, size, delete_on_termination)

        valid_until = None
        if timeout is not None:
            valid_until = (datetime.datetime.now() + datetime.timedelta(seconds=timeout)).isoformat()

        requests = self.ec2.request_spot_instances(price, valid_until=valid_until, **self.images[instance_type])
        return [r.id for r in requests]

    def check_spot_requests(self, requests, tags=None):
        """Check status of one or more EC2 spot instance requests.

        :param requests: List of EC2 spot instance request IDs.
        :type requests: list
        :param tags:
        :type tags: dict
        :return: List of boto.ec2.instance.Instance's created, order corresponding to requests param (None if request
                 still open, boto.ec2.instance.Reservation if request is no longer open)
        :rtype: list
        """
        instances = [None] * len(requests)
        ec2_requests = self.retry_on_ec2_error(self.ec2.get_all_spot_instance_requests, request_ids=requests)

        for req in ec2_requests:
            if req.instance_id:
                instance = self.retry_on_ec2_error(self.ec2.get_only_instances, req.instance_id)[0]

                if not instance:
                    raise EC2ManagerException('Failed to get instance with id %s for %s request %s'
                                              % (req.instance_id, req.status.code, req.id))

                instances[requests.index(req.id)] = instance

                self.retry_on_ec2_error(self.ec2.create_tags, [instance.id], tags or {})
                logger.info('Request %s is %s and %s.',
                            req.id,
                            req.status.code,
                            req.state)
                logger.info('%s is %s at %s (%s)',
                            instance.id,
                            instance.state,
                            instance.public_dns_name,
                            instance.ip_address)
            elif req.state != "open":
                # return the request so we don't try again
                instances[requests.index(req.id)] = req

        return instances

    def cancel_spot_requests(self, requests):
        """Cancel one or more EC2 spot instance requests.

        :param requests: List of EC2 spot instance request IDs.
        :type requests: list
        """
        ec2_requests = self.retry_on_ec2_error(self.ec2.get_all_spot_instance_requests, request_ids=requests)

        for req in ec2_requests:
            req.cancel()

    def create_spot(self,
                    price,
                    instance_type='default',
                    tags=None,
                    root_device_type='ebs',
                    size='default',
                    vol_type='gp2',
                    delete_on_termination=False,
                    timeout=None):
        """Create one or more EC2 spot instances.

        :param root_device_type:
        :param size:
        :param vol_type:
        :param delete_on_termination:
        :param timeout:
        :param price: Max price to pay for spot instance per hour.
        :type price: float
        :param instance_type: A section name in amazon.json
        :type instance_type: str
        :param tags:
        :type tags: dict
        :return: List of instances created
        :rtype: list
        """
        request_ids = self.create_spot_requests(price,
                                                instance_type=instance_type,
                                                root_device_type=root_device_type,
                                                size=size,
                                                vol_type=vol_type,
                                                delete_on_termination=delete_on_termination)
        instances = []
        logger.info('Waiting on fulfillment of requested spot instances.')
        poll_resolution = 5.0
        time_exceeded = False
        while request_ids:
            time.sleep(poll_resolution)

            new_instances = self.check_spot_requests(request_ids, tags=tags)

            if timeout is not None:
                timeout -= poll_resolution
                time_exceeded = timeout <= 0

            fulfilled = []
            for idx, instance in enumerate(new_instances):
                if instance is not None:
                    fulfilled.append(idx)
                if isinstance(instance, boto.ec2.instance.Instance):
                    instances.append(instance)
            for idx in reversed(fulfilled):
                request_ids.pop(idx)

            if request_ids and time_exceeded:
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
        logger.info('%d instance/s are running.', running)
        logger.info('Scaling down %d instances of those.', count)
        if count > running:
            logger.info('Scale-down value is > than running instance/s - using maximum of %d!', running)
            count = running
        return i[:count]

    def _get_default_name_size(self, instance_type, size):
        """Checks if root device name/size were specified in the image definition.

        :param instance_type: A section name in amazon.json.
        :type instance_type: str
        :param size:
        :type size: int
        :return: Root device name and size
        :rtype: tuple(str, int)
        """
        if 'root_size' in self.images[instance_type]:
            size = self.images[instance_type].pop('root_size')

        if 'root_device' in self.images[instance_type]:
            name = self.images[instance_type].pop('root_device')
        else:
            name = '/dev/sda1'

        return name, size

    def _configure_ebs_volume(self, vol_type, name, size, delete_on_termination):
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
        root_dev = boto.ec2.blockdevicemapping.BlockDeviceType()
        root_dev.delete_on_termination = delete_on_termination
        root_dev.volume_type = vol_type
        if size != 'default':
            root_dev.size = size  # change root volume to desired size
        bdm = boto.ec2.blockdevicemapping.BlockDeviceMapping()
        bdm[name] = root_dev
        return bdm

    def stop(self, instances, count=0):
        """Stop each provided running instance.

        :param count:
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

        :param count:
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
