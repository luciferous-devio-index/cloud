from dataclasses import asdict, dataclass
from datetime import datetime
from typing import AnyStr, Iterator

from boto3.dynamodb.conditions import Attr, Or
from bs4 import BeautifulSoup, Tag
from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource
from mypy_boto3_dynamodb.service_resource import Table

from luciferous_devio_index.common.aws import create_client, create_resource
from luciferous_devio_index.common.dataclasses import load_environment
from luciferous_devio_index.common.http import http_client_sec3
from luciferous_devio_index.common.logger import MyLogger


@dataclass(frozen=True)
class EnvironmentVariables:
    dynamodb_table_name: str
    sitemap_url: str
    target_prefix: str


@dataclass(frozen=True)
class Sitemap:
    url: str
    updated_at: int


logger = MyLogger(__name__)


@logger.logging_handler()
def handler(
    event,
    context,
    ddb_client: DynamoDBClient = create_client("dynamodb"),
    ddb_resource: DynamoDBServiceResource = create_resource("dynamodb"),
):
    env = load_environment(class_dataclass=EnvironmentVariables)
    table = ddb_resource.Table(env.dynamodb_table_name)
    text = get_sitemap(url=env.sitemap_url)
    for sitemap in parse_root_sitemap(text=text, prefix=env.target_prefix):
        put_item(sitemap=sitemap, table=table, ddb_client=ddb_client)


@logger.logging_function()
def get_sitemap(*, url: str) -> AnyStr:
    resp = http_client_sec3(url)
    return resp.read()


@logger.logging_function()
def parse_root_sitemap(*, text: AnyStr, prefix: str) -> Iterator[Sitemap]:
    bs = BeautifulSoup(text, "xml")
    for tag in bs.select("sitemap"):
        tag: Tag

        url = tag.select_one("loc").text
        if url.find(prefix) == -1:
            continue

        lastmod = tag.select_one("lastmod").text
        yield Sitemap(
            url=url,
            updated_at=int(
                datetime.strptime(lastmod, "%Y-%m-%dT%H:%M:%S%z").timestamp() * 1000
            ),
        )


@logger.logging_function()
def put_item(*, sitemap: Sitemap, table: Table, ddb_client: DynamoDBClient):
    try:
        table.put_item(
            Item=asdict(sitemap),
            ConditionExpression=Or(
                Attr("url").not_exists(), Attr("updated_at").lt(sitemap.updated_at)
            ),
        )
    except ddb_client.exceptions.ConditionalCheckFailedException:
        pass
