#!/usr/bin/env python3

"""Deploys ICL cluster to AWS.

Uses Terraform to create a new EKS cluster and deploy infractl workloads
"""

import logging

import click

from infractl.plugins.aws_infrastructure import vpc

logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Tool to manage ICL deployments in AWS."""


@cli.command()
def print_vpc_tfvars(max_subnets: int = 2):
    """Print AWS VPC configuration in Terraform HCL format."""
    account_id = vpc.get_account_id()
    region_name = vpc.get_region_name()
    vpc_id = vpc.get_default_vpc_id()
    if not vpc_id:
        raise click.ClickException(f'Default VPC is not found in {region_name}, {account_id}')
    subnet_ids = vpc.get_subnets_ids(vpc_id, max_subnets)
    if not subnet_ids:
        raise click.ClickException(
            f'Subnets are not found in VPC {vpc_id} in {region_name}, {account_id}'
        )
    subnet_ids_str = '"' + '","'.join(subnet_ids) + '"'
    click.echo(f'vpc_id = "{vpc_id}"')
    click.echo(f'subnet_ids = [{subnet_ids_str}]')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    cli()
