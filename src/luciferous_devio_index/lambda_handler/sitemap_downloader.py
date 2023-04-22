from dataclasses import dataclass
from datetime import datetime, timezone
from http.client import HTTPResponse
from os.path import basename
from typing import AnyStr, List
from urllib.request import urlopen

from bs4 import BeautifulSoup
from mypy_boto3_s3 import S3Client

from luciferous_devio_index.common.aws import create_client
from luciferous_devio_index.common.dataclasses import load_environment
from luciferous_devio_index.common.logger import MyLogger


@dataclass()
class EnvironmentVariables:
    s3_bucket: str
    s3_prefix: str
    sitemap_url: str


logger = MyLogger(__name__)


@logger.logging_handler()
def handler(event, context, s3_client: S3Client = create_client("s3")):
    env = load_environment(class_dataclass=EnvironmentVariables)
    prefix = f"{env.s3_prefix}/{datetime.now(timezone.utc)}"
    root_sitemap = execute_xml(
        url=env.sitemap_url, bucket=env.s3_bucket, prefix=prefix, s3_client=s3_client
    )
    sub_sitemaps = parse_sub_sitemap_url(text=root_sitemap)
    for url_sub_sitemap in sub_sitemaps:
        execute_xml(
            url=url_sub_sitemap,
            bucket=env.s3_bucket,
            prefix=prefix,
            s3_client=s3_client,
        )


@logger.logging_function()
def get_xml(*, url: str) -> AnyStr:
    response: HTTPResponse = urlopen(url)
    return response.read()


@logger.logging_function()
def parse_sub_sitemap_url(*, text: AnyStr) -> List[str]:
    if isinstance(text, bytes):
        text = text.decode()
    bs = BeautifulSoup(text, "xml")
    locs = bs.select("loc")
    return [x.text for x in locs]


@logger.logging_function()
def save_xml(*, body: AnyStr, name: str, bucket: str, prefix: str, s3_client: S3Client):
    if isinstance(body, str):
        body = body.encode()
    s3_client.put_object(Bucket=bucket, Key=f"{prefix}/{name}", Body=body)


@logger.logging_function()
def execute_xml(*, url: str, bucket: str, prefix: str, s3_client: S3Client) -> AnyStr:
    name = basename(url)
    body = get_xml(url=url)
    save_xml(body=body, name=name, bucket=bucket, prefix=prefix, s3_client=s3_client)
    return body
