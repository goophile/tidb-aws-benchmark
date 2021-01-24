#!/usr/bin/env python3
import logging
import argparse

from libs.aws import AWS
from libs.tidb import ControlServer


def main():
    parser = argparse.ArgumentParser(description='Deploy TiDB on AWS and benchmark.')
    parser.add_argument('--debug', action='store_true', help='Set loglevel (default INFO) to DEBUG')
    parser.add_argument('--create_key', action='store_true', help='Create SSH key pair')
    parser.add_argument('--delete_key', action='store_true', help='Delete SSH key pair')
    parser.add_argument('--create_ec2', action='store_true', help='Create Cloudformation stack')
    parser.add_argument('--ec2_template', default=None, help='EC2 Cloudformation template')
    parser.add_argument('--delete_ec2', action='store_true', help='Delete Cloudformation stack')

    parser.add_argument('--install_tidb', action='store_true', help='Install TiUP, TiDB, go-tpc')
    parser.add_argument('--tidb_version', default='4.0.10', help='TiDB version, default 4.0.10')
    parser.add_argument('--tidb_template', default=None,
                        help='TiDB topology template, should match Cloudformation template')

    parser.add_argument('--prepare_data', action='store_true',
                        help='Install go-tpc and insert data into TiDB')
    parser.add_argument('--clean_data', action='store_true', help='Clean the benchmark data')
    parser.add_argument('--benchmark', action='store_true', help='Benchmark with go-tpc')
    parser.add_argument('--tpc_warehouses', default='4', help='go-tpc warehouses, default 4')
    parser.add_argument('--tpc_parts', default='4', help='go-tpc partitions, default 4')
    parser.add_argument('--tpc_time', default='60', help='go-tpc duration in seconds, default 60')
    parser.add_argument('--tpc_threads', default='10', help='go-tpc threads, default 10')

    args = parser.parse_args()

    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s %(levelname)s [%(filename)s:%(funcName)s] %(message)s')

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

    if args.install_tidb or args.prepare_data or args.clean_data or args.benchmark:
        ec2_ip = aws.get_ec2_ip()
        ctrl = ControlServer(ec2_ip, 'ubuntu', str(aws.private_key_path))

    if args.install_tidb:
        assert args.tidb_template
        ctrl.install_tiup()
        ctrl.install_tidb(args.tidb_template, args.tidb_version)
        ctrl.install_go_tpc()

    if args.prepare_data:
        ctrl.prepare_data(args.tpc_warehouses, args.tpc_parts)

    if args.clean_data:
        ctrl.clean_data(args.tpc_warehouses)

    if args.benchmark:
        ctrl.benchmark(args.tpc_threads, args.tpc_time, args.tpc_warehouses)


if __name__ == "__main__":
    main()
