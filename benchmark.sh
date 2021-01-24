#!/bin/bash

set -e

./main.py --create_key
./main.py --create_ec2 --ec2_template ./aws-cloudformation.json
./main.py --install_tidb --tidb_template ./tidb-topology.yaml
./main.py --tpc_warehouses 100 --tpc_parts 11 --prepare_data
./main.py --tpc_warehouses 100 --tpc_threads 25 --tpc_time 120 --benchmark
./main.py --delete_ec2
./main.py --delete_key
