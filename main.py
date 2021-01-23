#!/usr/bin/env python3
import logging
import argparse

from libs.aws import AWS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(filename)s:%(funcName)s] %(message)s')


def main():
    parser = argparse.ArgumentParser(description='Deploy TiDB on AWS and benchmark.')
    parser.add_argument('--create_key', action='store_true', help='Create SSH key pair')
    parser.add_argument('--delete_key', action='store_true', help='Delete SSH key pair')
    parser.add_argument('--create_ec2', action='store_true', help='Create Cloudformation stack')
    parser.add_argument('--ec2_template', default=None, help='EC2 Cloudformation template')
    parser.add_argument('--delete_ec2', action='store_true', help='Delete Cloudformation stack')

    args = parser.parse_args()

    aws = AWS()

    if args.create_key:
        aws.create_ssh_key()

    if args.delete_key:
        aws.delete_ssh_key()

    if args.create_ec2:
        assert args.ec2_template
        aws.create_ec2_stack(args.ec2_template)

    if args.delete_ec2:
        aws.delete_ec2_stack()


if __name__ == "__main__":
    main()
