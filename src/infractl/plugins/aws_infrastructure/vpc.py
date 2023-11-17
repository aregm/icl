"""AWS VPC tools."""

from __future__ import annotations

from typing import List, Optional

import boto3
import botocore


def get_ec2_client() -> botocore.client.EC2:
    """Creates AWS EC2 client.

    Uses the default credentials and region from the environment.
    """
    return boto3.client('ec2')


def get_sts_client() -> botocore.client.STS:
    """Creates AWS STS client.

    Uses the default credentials and region from the environment.
    """
    return boto3.client('sts')


def get_account_id() -> str:
    """Returns Current AWS account ID."""
    return get_sts_client().get_caller_identity()['Account']


def get_region_name() -> str:
    """Returns Current AWS region name, for example 'us-east-1'."""
    return boto3.session.Session().region_name


def get_default_vpc_id() -> Optional[str]:
    """Returns default VPC ID.

    Returns ID of the default VPC for the current AWS account and region, or None if VPC does not
    exist.
    """
    client = get_ec2_client()
    response = client.describe_vpcs(
        Filters=[
            {
                'Name': 'is-default',
                'Values': ['true'],
            },
        ],
    )
    vpcs = response.get('Vpcs', [])
    if len(vpcs) < 1:
        return None
    return vpcs[0]['VpcId']


def get_subnets_ids(vpc_id: str, max_subnets: int = 2) -> List[str]:
    """Returns a list of subnet IDs for a given VPC."""
    client = get_ec2_client()
    response = client.describe_subnets(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [vpc_id],
            },
        ],
    )
    subnets = response.get('Subnets', [])
    # Sort subnets by availability zone, because usually older AZs (such as 'us-east-1a') have more
    # capacity than the newer AZs (such az 'us-east-1e').
    subnets.sort(key=lambda subnet: subnet['AvailabilityZone'])
    subnet_ids = [item['SubnetId'] for item in subnets]
    if max_subnets >= len(subnet_ids):
        return subnet_ids
    return subnet_ids[:max_subnets]
