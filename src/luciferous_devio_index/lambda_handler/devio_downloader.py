import json
from dataclasses import dataclass
from io import BytesIO
from typing import AnyStr
from urllib.error import HTTPError
from zipfile import ZIP_DEFLATED, ZipFile
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
    try:
        response = http_client_sec3(url=f"{env.url_devio_posts}/{post_id}")
        post_data = response.read()
    except HTTPError as e:
        if e.status in [404, 401]:
            logger.warning(
                f"failed to get post data: post_id={post_id} status={e.status}, err={e}"
            )
            return
        raise
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
    data = json.loads(post_data)
    text = json.dumps(data, ensure_ascii=False)
    io = BytesIO()
    with ZipFile(file=io, mode="w", compression=ZIP_DEFLATED) as zf:
        zf.writestr(f"{post_id}.json", text)
    s3_client.put_object(
        Bucket=s3_bucket,
        Key=f"{s3_prefix}/{post_id}.json.zip",
        Body=io.getvalue(),
    )
