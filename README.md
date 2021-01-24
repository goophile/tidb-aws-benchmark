# tidb-aws-benchmark

Deploy TiDB cluster on AWS EC2, and benchmark with go-tpc.

**!!! Notice: remember to delete the EC2 stack after test! The default Cloudformation template is expensive.**

# Requirements

The script requires the following library:

```sh
pip3 install boto3 paramiko
```

Create an IAM role on AWS, with the following permissions:

- AmazonEC2FullAccess
- AWSCloudFormationFullAccess

Save the access key to file `~/.aws/credentials`, for example:

```
[default]
region=us-east-2
aws_access_key_id=fakeid
aws_secret_access_key=fakekey
```

You may also need to request AWS to increase your vCPU limit, otherwise the Cloudformation stack may fail to create.


# Usage

The easist way is to run the `benchmark.sh` script. It creates a Cloudformation stack on AWS, deploy an TiDB cluster, do the benchmark, and delete the AWS stack.

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


# Configuration tune

Edit `aws-cloudformation.json` and `tidb-topology.yaml` for different configurations.

Different EC2 instances may have different performances. Current Cloudformation template chooses a cluster of EC2 instances according to [Software and Hardware Recommendations for Development and test environments](https://docs.pingcap.com/tidb/dev/hardware-and-software-requirements#development-and-test-environments) and [Minimal Deployment Topology](https://docs.pingcap.com/tidb/dev/minimal-deployment-topology).

The OS image in the Cloudformation template is Ubuntu 20.04. The image IDs come from [Amazon EC2 AMI Locator](https://cloud-images.ubuntu.com/locator/ec2/). You can also change the OS system in the Cloudformation template.
