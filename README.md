# tidb-aws-benchmark

Deploy TiDB cluster on AWS EC2, and benchmark with [go-tpc](https://github.com/pingcap/go-tpc#prepare).

**!!! Notice: remember to delete the AWS Cloudformation stack after test! The stack costs about $4 per hour.**

# Requirements

The script requires the following library:

```sh
pip3 install boto3 paramiko
```

Create an IAM user on AWS, with `Programmatic access` type and the following permissions:

- AmazonEC2FullAccess
- AWSCloudFormationFullAccess

Save the access key to file `~/.aws/credentials`, for example:

```
[default]
region=us-east-2
aws_access_key_id=fakeid
aws_secret_access_key=fakekey
```


# Usage

Execute `benchmark.sh` to run a full cycle of benchmark test. The script will:

- creates a Cloudformation stack on AWS
- deploy an TiDB cluster
- do the benchmark with specified arguments
- delete the AWS stack

Or you can run the `main.py` with arguments according to your needs.

```sh
$ ./main.py -h
usage: main.py [-h] [--debug] [--create_key] [--delete_key] [--create_ec2]
               [--ec2_template EC2_TEMPLATE] [--delete_ec2] [--install_tidb]
               [--tidb_version TIDB_VERSION] [--tidb_template TIDB_TEMPLATE]
               [--prepare_data] [--clean_data] [--benchmark]
               [--tpc_warehouses TPC_WAREHOUSES] [--tpc_parts TPC_PARTS]
               [--tpc_time TPC_TIME] [--tpc_threads TPC_THREADS]

Deploy TiDB on AWS and benchmark.

optional arguments:
  -h, --help            show this help message and exit
  --debug               Set loglevel (default INFO) to DEBUG
  --create_key          Create SSH key pair
  --delete_key          Delete SSH key pair
  --create_ec2          Create Cloudformation stack
  --ec2_template EC2_TEMPLATE
                        EC2 Cloudformation template
  --delete_ec2          Delete Cloudformation stack
  --install_tidb        Install TiUP, TiDB, go-tpc
  --tidb_version TIDB_VERSION
                        TiDB version, default 4.0.10
  --tidb_template TIDB_TEMPLATE
                        TiDB topology template, should match Cloudformation
                        template
  --prepare_data        Install go-tpc and insert data into TiDB
  --clean_data          Clean the benchmark data
  --benchmark           Benchmark with go-tpc
  --tpc_warehouses TPC_WAREHOUSES
                        go-tpc warehouses, default 4
  --tpc_parts TPC_PARTS
                        go-tpc partitions, default 4
  --tpc_time TPC_TIME   go-tpc duration in seconds, default 60
  --tpc_threads TPC_THREADS
                        go-tpc threads, default 10
```


# Configuration tuning

Edit `aws-cloudformation.json` and `tidb-topology.yaml` for different configurations.

Different EC2 instance types may have different performances. Current Cloudformation template chooses a cluster of EC2 instances according to [Software and Hardware Recommendations for Development and test environments](https://docs.pingcap.com/tidb/dev/hardware-and-software-requirements#development-and-test-environments) and [Minimal Deployment Topology](https://docs.pingcap.com/tidb/dev/minimal-deployment-topology).

The OS image in the Cloudformation template is Ubuntu 20.04. The image IDs come from [Amazon EC2 AMI Locator](https://cloud-images.ubuntu.com/locator/ec2/). You can also change the OS image in the Cloudformation template.


# Sample result

The sample template uses the following configuration:

| Component              | InstanceType | Description       | vCPU | Memory | Storage        |
| ---------------------- | ------------ | ----------------- | ---- | ------ | -------------- |
| ControlServer (go-tpc) | t3.2xlarge   | general purpose   | 8    | 32G    | 8G             |
| Monitoring & Grafana   | t3.2xlarge   | general purpose   | 8    | 32G    | 8G             |
| PD                     | t3.2xlarge   | general purpose   | 8    | 32G    | 8G             |
| TiDB                   | c5.2xlarge   | compute optimized | 8    | 16G    | 8G             |
| TiKV-1                 | i3.2xlarge   | storage optimized | 8    | 61G    | 200G Optimized |
| TiKV-2                 | i3.2xlarge   | storage optimized | 8    | 61G    | 200G Optimized |
| TiKV-3                 | i3.2xlarge   | storage optimized | 8    | 61G    | 200G Optimized |

The result is:

`./go-tpc tpcc -H 10.0.1.11 -T 256 --time 300s --warehouses 100 run`

```
[Summary] DELIVERY - Takes(s): 298.1, Count: 10981, TPM: 2210.5, Sum(ms): 10385643.5, Avg(ms): 945.7, 50th(ms): 805.3, 90th(ms): 1409.3, 95th(ms): 1677.7, 99th(ms): 2684.4, 99.9th(ms): 4563.4, Max(ms): 6174.0
[Summary] DELIVERY_ERR - Takes(s): 298.1, Count: 36, TPM: 7.2, Sum(ms): 17696.5, Avg(ms): 491.4, 50th(ms): 385.9, 90th(ms): 906.0, 95th(ms): 1006.6, 99th(ms): 1409.3, 99.9th(ms): 1409.3, Max(ms): 1409.3
[Summary] NEW_ORDER - Takes(s): 298.7, Count: 125218, TPM: 25151.6, Sum(ms): 32664826.2, Avg(ms): 261.0, 50th(ms): 234.9, 90th(ms): 385.9, 95th(ms): 469.8, 99th(ms): 805.3, 99.9th(ms): 1744.8, Max(ms): 4563.4
[Summary] NEW_ORDER_ERR - Takes(s): 298.7, Count: 98, TPM: 19.7, Sum(ms): 14678.1, Avg(ms): 149.8, 50th(ms): 142.6, 90th(ms): 302.0, 95th(ms): 352.3, 99th(ms): 536.9, 99.9th(ms): 637.5, Max(ms): 637.5
[Summary] ORDER_STATUS - Takes(s): 298.7, Count: 10992, TPM: 2207.7, Sum(ms): 576520.7, Avg(ms): 52.5, 50th(ms): 39.8, 90th(ms): 109.1, 95th(ms): 121.6, 99th(ms): 142.6, 99.9th(ms): 167.8, Max(ms): 218.1
[Summary] ORDER_STATUS_ERR - Takes(s): 298.7, Count: 3, TPM: 0.6, Sum(ms): 91.6, Avg(ms): 30.5, 50th(ms): 35.7, 90th(ms): 54.5, 95th(ms): 54.5, 99th(ms): 54.5, 99.9th(ms): 54.5, Max(ms): 54.5
[Summary] PAYMENT - Takes(s): 298.7, Count: 119261, TPM: 23953.5, Sum(ms): 32197418.4, Avg(ms): 270.1, 50th(ms): 218.1, 90th(ms): 469.8, 95th(ms): 604.0, 99th(ms): 906.0, 99.9th(ms): 2281.7, Max(ms): 5100.3
[Summary] PAYMENT_ERR - Takes(s): 298.7, Count: 83, TPM: 16.7, Sum(ms): 12788.4, Avg(ms): 154.2, 50th(ms): 130.0, 90th(ms): 318.8, 95th(ms): 385.9, 99th(ms): 520.1, 99.9th(ms): 637.5, Max(ms): 637.5
[Summary] STOCK_LEVEL - Takes(s): 298.7, Count: 11228, TPM: 2255.0, Sum(ms): 629304.1, Avg(ms): 56.1, 50th(ms): 48.2, 90th(ms): 96.5, 95th(ms): 104.9, 99th(ms): 121.6, 99.9th(ms): 151.0, Max(ms): 939.5
[Summary] STOCK_LEVEL_ERR - Takes(s): 298.7, Count: 3, TPM: 0.6, Sum(ms): 104.0, Avg(ms): 35.0, 50th(ms): 37.7, 90th(ms): 60.8, 95th(ms): 60.8, 99th(ms): 60.8, 99.9th(ms): 60.8, Max(ms): 60.8
tpmC: 25151.6, efficiency: 1955.8%
```
