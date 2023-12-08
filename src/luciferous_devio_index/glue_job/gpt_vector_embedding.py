import json
from dataclasses import dataclass
from io import BytesIO
from os.path import basename
from zipfile import ZipFile

import boto3
from mypy_boto3_s3 import S3Client

from luciferous_devio_index.common.logger import MyLogger


@dataclass(frozen=True)
class Arguments:
    s3_bucket: str
    s3_prefix: str
    model_name: str


logger = MyLogger(__name__)


@logger.logging_main()
def main():
    pass


@logger.logging_function()
def create_index_key(*, s3_prefix: str, model_name: str) -> str:
    return f"{s3_prefix}/{model_name}/index-{model_name}.json.zip"


@logger.logging_function()
def get_saved_index(*, bucket: str, key: str, s3_client: S3Client) -> dict:
    resp = s3_client.get_object(Bucket=bucket, Key=key)
    io = BytesIO(resp["Body"].read())
    with ZipFile(io) as zf:
        with zf.open(basename(key).replace(".zip", "")) as f:
            return json.load(f)


if __name__ == "__main__":
    main()
