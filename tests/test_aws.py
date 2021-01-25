from unittest import mock
import pytest
import boto3

import sys
from pathlib import Path
sys.path.append(str(Path().resolve().parent))

from libs.aws import AWS


@pytest.fixture(scope='function')
def aws_mock():
    with mock.patch.object(boto3, 'client') as client:
        aws = AWS()
        aws.ec2 = client
        aws.cloudformation = client
        return aws


def test_ssh_key_exists(aws_mock):
    resp = {
        'KeyPairs': [
            {
                'KeyPairId': 'aaaaaaaaaaa',
                'KeyFingerprint': 'string',
                'KeyName': 'tidb-benchmark',
                'Tags': [
                    {
                        'Key': 'string',
                        'Value': 'string'
                    }
                ]
            }
        ]
    }

    with mock.patch.object(aws_mock.ec2, 'describe_key_pairs', return_value=resp):
        assert aws_mock._ssh_key_exists()


def test_is_stack_exists(aws_mock):
    resp = {
        'StackSummaries': [
            {
                'StackName': 'tidb-benchmark',
                'StackStatus': 'CREATE_IN_PROGRESS'
            }
        ]
    }

    with mock.patch.object(aws_mock.cloudformation, 'list_stacks', return_value=resp):
        assert aws_mock._is_stack_exists()


def test_wait_ec2_stack_complete(aws_mock):
    resp = {
        'Stacks': [{'StackStatus': 'CREATE_IN_PROGRESS'}]
    }

    with mock.patch.object(aws_mock.cloudformation, 'describe_stacks', return_value=resp):
        with mock.patch('time.sleep') as sleep:
            with pytest.raises(Exception):
                aws_mock._wait_ec2_stack_complete()
            assert sleep.called is True

    resp = {
        'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]
    }

    with mock.patch.object(aws_mock.cloudformation, 'describe_stacks', return_value=resp):
        with mock.patch('time.sleep') as sleep:
            aws_mock._wait_ec2_stack_complete()
            assert sleep.called is False


def test_get_ec2_ip(aws_mock):
    resp = {
        'Stacks': [
            {
                'Outputs': [
                    {
                        'OutputKey': 'IPAddress',
                        'OutputValue': '1.2.3.4'
                    }
                ]
            }
        ]
    }

    with mock.patch.object(aws_mock.cloudformation, 'describe_stacks', return_value=resp):
        assert aws_mock.get_ec2_ip() == '1.2.3.4'

