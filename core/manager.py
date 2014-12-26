# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import time
import logging

from boto.ec2 import connect_to_region


class LaniakeaManager(object):

    def __init__(self, images):
        self.ec2 = None
        self.instances = []
        self.images = images

    def connect(self, region="us-west-2", **kw_params):
        self.ec2 = connect_to_region(region, **kw_params)

    def create(self, instance_type='default', tags=None):
        reservation = self.ec2.run_instances(**self.images[instance_type])
        instance = reservation.instances[0]
        self.ec2.create_tags([instance.id], tags or {})
        while instance.state == 'pending':
            time.sleep(2.5)
            instance.update()
        logging.info("DNS: %s (%s)" % (instance.public_dns_name, instance.ip_address))
        self.instances.append(instance)

    def state(self, instances=None):
        instances = instances or self.instances
        if not instances:
            return
        [instance.update() for instance in instances]
        return [(instance.id, instance.state) for instance in instances]

    def stop(self, instances=None):
        instances = instances or self.instances
        if not instances:
            return
        self.ec2.stop_instances([instance.id for instance in instances])

    def terminate(self, instances=None):
        instances = instances or self.instances
        if not instances:
            return
        self.ec2.terminate_instances([instance.id for instance in instances])

    def find(self, filters=None):
        instances = []
        reservations = self.ec2.get_all_instances(filters=filters or {})
        for reservation in reservations:
            instances.extend(reservation.instances)
        return instances
