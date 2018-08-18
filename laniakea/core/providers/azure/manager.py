# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode

logger = logging.getLogger('laniakea')


class AzureManagerException(Exception):
    """Exception class for Azure Manager."""
    pass


class AzureManager:
    """
    Microsoft Azure manager class.
    """

    def __init__(self, settings):
        self.azure = None
        self.client = None
        self.settings = settings

    def create_parameters(self, args):
        if self.settings is None:
            raise Exception('No configuration attached.')

        parameters = {
            'location': args.region,
            'storageAccountName': '{}group'.format(args.storage_name),
            'adminUsername': self.settings['credentials']['username'],
            'adminPassword': self.settings['credentials']['password'],
            'aws_key_id': self.settings['aws-credentials']['aws_key_id'],
            'aws_secret': self.settings['aws-credentials']['aws_secret'],
            'count': args.count
        }
        return {k: {'value': v} for k, v in parameters.items()}

    def connect(self):
        if self.settings is None:
            raise AzureManagerException('No configuration attached.')

        credentials = ServicePrincipalCredentials(
            client_id=self.settings['keys']['client_id'],
            secret=self.settings['keys']['client_secret'],
            tenant=self.settings['keys']['tenant_id']
        )

        try:
            self.client = ResourceManagementClient(credentials, self.settings['keys']['subscription_id'])
        except Exception as msg:
            raise AzureManagerException(msg)

    def create(self, parameters, group_name, template):
        if self.client is None:
            raise Exception('No connected to a Resource Management Client.')

        deployment_properties = {
            'mode': DeploymentMode.incremental,
            'template': template,
            'parameters': parameters
        }

        group_name = "{}Grp".format(group_name)

        self.client.resource_groups.create_or_update(group_name, {
            'location': parameters['location']['value']
        })

        deployment_async_operation = self.client.deployments.create_or_update(
            group_name,
            '{}-deploy1'.format(group_name),
            deployment_properties
        )

        deployment_async_operation.wait()

    def stop(self):
        raise NotImplementedError

    def terminate(self, resource_group):
        if self.client is None:
            raise Exception('Not connected to a Resource Management Client.')
        delete_async_operation = self.client.resource_groups.delete(resource_group)
        delete_async_operation.wait()
