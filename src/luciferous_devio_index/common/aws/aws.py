from typing import Optional

import boto3
from boto3.resources.base import ServiceResource
from botocore.client import BaseClient
from botocore.config import Config

CONFIG_DEFAULT = Config(connect_timeout=5, read_timeout=5, retries={"mode": "standard"})


def create_client(
    name: str, *, config: Optional[Config] = None, **kwargs
) -> BaseClient:
    return boto3.client(
        name, config=CONFIG_DEFAULT if config is None else config, **kwargs
    )


def create_resource(
    name: str, *, config: Optional[Config] = None, **kwargs
) -> ServiceResource:
    return boto3.resource(
        name, config=CONFIG_DEFAULT if config is None else config, **kwargs
    )
