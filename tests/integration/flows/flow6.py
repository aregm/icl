"""Prefect flows for testing purpose."""

from prefect import flow


@flow
def flow6():
    raise RuntimeError("Something went wrong")
