# tidb-aws-benchmark

Deploy TiDB cluster on AWS EC2, and benchmark with go-tpc.


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
