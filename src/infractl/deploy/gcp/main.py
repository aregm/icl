#!/usr/bin/env python3

"""
Helper functions to deploy ICL cluster to GCP. These are called by scripts/deploy/gke.sh
Uses Terraform to create a new GKE cluster and deploy infractl workloads
"""

import os
import subprocess
import sys

import click


@click.group()
def cli():
    """Group to manage GPU settings validation and other operations."""
    pass


@cli.command(name="validate-gpu-settings")
@click.argument("gpu_model")
def validate_gpu_settings(gpu_model):
    supported_gpus_dict = {
        "a2-highgpu": ["nvidia-tesla-a100"],
        "a2-ultragpu": ["nvidia-a100-80gb"],
        "a3-highgpu": ["nvidia-h100-80gb"],
        "g2-standard": ["nvidia-l4"],
        "n1-standard": [
            "nvidia-tesla-t4",
            "nvidia-tesla-p4",
            "nvidia-tesla-v100",
            "nvidia-tesla-p100",
            "nvidia-tesla-k80",
        ],
        "n1-highmem": [
            "nvidia-tesla-t4",
            "nvidia-tesla-p4",
            "nvidia-tesla-v100",
            "nvidia-tesla-p100",
            "nvidia-tesla-k80",
        ],
        "n1-highcpu": [
            "nvidia-tesla-t4",
            "nvidia-tesla-p4",
            "nvidia-tesla-v100",
            "nvidia-tesla-p100",
            "nvidia-tesla-k80",
        ],
    }
    zone = os.environ["ICL_GCP_ZONE"]
    machine_type = os.environ["ICL_GCP_MACHINE_TYPE"]

    # Check machine type availability
    if machine_type:
        command = [
            "gcloud",
            "compute",
            "machine-types",
            "list",
            "--filter",
            f"name='{machine_type}'",
            "--format=value(name)",
            f"--zones={zone}",
        ]
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            if machine_type not in result.stdout:
                print(f"Error: {machine_type} is not available in {zone}.")
                print("Please try a different machine type or zone.")
                sys.exit(100)
            else:
                print("Machine is available")
        except subprocess.CalledProcessError:
            sys.exit(10)

        # Check GPU model availability
        command = ["gcloud", "compute", "accelerator-types", "list", "--verbosity=error"]
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            if gpu_model not in result.stdout:
                print(f"Error: {gpu_model} is not available in {zone}.")
                print("Please try a different gpu model or zone.")
                sys.exit(200)
            else:
                print("GPU is available")
        except subprocess.CalledProcessError:
            sys.exit(11)
    else:
        print("The 'machine_type' variable is empty")

    # Check machine type and gpu model compatibility
    # Simplify the machine type to match keys in supported_gpus_dict
    # For example, convert "n1-standard-8" to "n1-standard"
    simplified_machine_type = machine_type.rsplit("-", 1)[0]

    # Check if simplified_machine_type is a key in supported_gpus_dict
    if simplified_machine_type in supported_gpus_dict:
        # Check if gpu_model is in the list associated with the key
        if gpu_model in supported_gpus_dict[simplified_machine_type]:
            print(f"Machine type {machine_type} supports the {gpu_model} GPU.")
        else:
            print(f"Error: Machine type {machine_type} doesn't support the {gpu_model} GPU.")
            sys.exit(100)
    else:
        print(
            f"Error: Machine type \"{machine_type}\" "
            f"(simplified to {simplified_machine_type}) is not recognized."
        )
        sys.exit(300)


if __name__ == "__main__":
    cli()
