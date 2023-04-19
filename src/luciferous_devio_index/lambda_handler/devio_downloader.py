import json
from dataclasses import dataclass
from typing import AnyStr
from zlib import compress

from mypy_boto3_s3 import S3Client

from luciferous_devio_index.common.aws import create_client
from luciferous_devio_index.common.dataclasses import load_environment
from luciferous_devio_index.common.http import http_client_sec3
from luciferous_devio_index.common.logger import MyLogger


@dataclass
class EnvironmentVariables:
    s3_bucket: str
    s3_prefix: str
    url_devio_posts: str


logger = MyLogger(__name__)


@logger.logging_handler(with_return=False)
def handler(event: dict, context, s3_client: S3Client = create_client("s3")):
    env = load_environment(class_dataclass=EnvironmentVariables)
    post_id = parse_post_id(event=event)
    post_data = http_client_sec3(url=f"{env.url_devio_posts}/{post_id}")
    save_to_s3(
        post_id=post_id,
        post_data=post_data,
        s3_bucket=env.s3_bucket,
        s3_prefix=env.s3_prefix,
        s3_client=s3_client,
    )


@logger.logging_function(with_arg=False)
def parse_post_id(*, event: dict) -> str:
    if (post_id := event.get("post_id")) is not None:
        return post_id
    raw_ddb_event = event["Records"][0]["body"]
    ddb_event = json.loads(raw_ddb_event)
    return ddb_event["dynamodb"]["Keys"]["post_id"]["S"]


@logger.logging_function(with_arg=False)
def save_to_s3(
    *,
    post_id: str,
    post_data: AnyStr,
    s3_bucket: str,
    s3_prefix: str,
    s3_client: S3Client,
):
    if isinstance(post_data, str):
        post_data = post_data.encode()
    s3_client.put_object(
        Bucket=s3_bucket,
        Key=f"{s3_prefix}/{post_id}.json.zip",
        Body=compress(post_data, level=9),
    )
