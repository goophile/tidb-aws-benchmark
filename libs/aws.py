"""
EC2 SSH key and Cloudformation stack.
"""
import logging
from pathlib import Path
import time
import boto3

logger = logging.getLogger(__name__)


class AWS:
    def __init__(self):
        self.ssh_key = 'tidb-benchmark'
        self.private_key_path = Path.home() / '.ssh/tidb-benchmark.pem'
        self.ec2_stack = 'tidb-benchmark'
        self.ec2 = boto3.client('ec2')
        self.cloudformation = boto3.client('cloudformation')

    def _ssh_key_exists(self) -> bool:
        for key in self.ec2.describe_key_pairs()['KeyPairs']:
            if key['KeyName'] == self.ssh_key:
                return True
        return False

    def create_ssh_key(self):
        """
        Create EC2 SSH key pair, store private key in self.private_key_path.
        """
        if self.private_key_path.exists():
            logger.info('SSH Private key already exists, skip creating')
            return
        response = self.ec2.create_key_pair(KeyName=self.ssh_key)

        with open(str(self.private_key_path), 'w') as f:
            f.write(response['KeyMaterial'])
        self.private_key_path.chmod(0o600)

        logger.info(f'Created new SSH key pair, stored to {self.private_key_path}')

    def delete_ssh_key(self):
        """
        Delete a SSH key pair on AWS EC2, also delete local private key self.private_key_path.
        """
        if self._ssh_key_exists():
            self.ec2.delete_key_pair(KeyName=self.ssh_key)
            logger.info(f'Deleted the SSH key {self.ssh_key} on AWS')

        if self.private_key_path.exists():
            self.private_key_path.unlink()
            logger.info(f'Deleted local SSH private key {self.private_key_path}')

        logger.info('The SSH key pair no longer exists')

    def _is_stack_exists(self) -> bool:
        response = self.cloudformation.list_stacks()
        for stack in response['StackSummaries']:
            if stack['StackStatus'] != 'DELETE_COMPLETE' and stack['StackName'] == self.ec2_stack:
                return True
        return False

    def _wait_ec2_stack_complete(self):
        while True:
            response = self.cloudformation.describe_stacks(StackName=self.ec2_stack)
            stack = response['Stacks'][0]
            if stack['StackStatus'] == 'CREATE_COMPLETE':
                return
            logger.info(f"The stack status is {stack['StackStatus']}, wait it CREATE_COMPLETE...")
            time.sleep(10)

    def create_ec2_stack(self, template_path: str):
        """
        Create an Cloudformation stack on AWS if not exists.
        """
        if self._is_stack_exists():
            logger.info(f'The Cloudformation stack {self.ec2_stack} already exists, skip creating')
            return

        with open(template_path) as f:
            template_body = f.read()

        self.cloudformation.create_stack(
            StackName=self.ec2_stack,
            TemplateBody=template_body,
            Parameters=[
                {
                    'ParameterKey': 'KeyName',
                    'ParameterValue': self.ssh_key,
                }
            ]
        )

        self._wait_ec2_stack_complete()
        logger.info(f'Created Cloudformation stack on AWS: {self.ec2_stack}')

    def delete_ec2_stack(self):
        """
        Delete the Cloudformation stack from AWS.
        """
        if not self._is_stack_exists():
            logger.info('The Cloudformation stack does not exist')
            return

        self.cloudformation.delete_stack(StackName=self.ec2_stack)
        logger.info('Deleted the Cloudformation stack from AWS')
