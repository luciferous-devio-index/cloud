import json
from luciferous_devio_index.common.aws import create_client, create_resource
from boto3.dynamodb.conditions import Attr
from dataclasses import dataclass
from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource
from mypy_boto3_dynamodb.service_resource import Table

from luciferous_devio_index.common.dataclasses import load_environment
from luciferous_devio_index.common.http import http_client_sec3
from luciferous_devio_index.common.logger import MyLogger


@dataclass
class EnvironmentVariables:
    url_post: str
    table_post_id: str


logger = MyLogger(__name__)


@logger.logging_handler(with_return=False)
def handler(
    event: dict,
    _context,
    client_dynamodb: DynamoDBClient = create_client("dynamodb"),
    resource_dynamodb: DynamoDBServiceResource = create_resource("dynamodb"),
):
    env = load_environment(class_dataclass=EnvironmentVariables)
    table = resource_dynamodb.Table(env.table_post_id)
    url = parse_url(event=event)
    slug = parse_slug(url=url)
    post_id = get_post_id(slug=slug, url_post=env.url_post)
    logger.info("url, slug, and post_id", url=url, slug=slug, post_id=post_id)
    put_post_id(post_id=post_id, client=client_dynamodb, table=table)


@logger.logging_function()
def parse_url(*, event: dict) -> str:
    if (url := event.get("url")) is not None:
        return url
    return event["Records"][0]["body"]


@logger.logging_function()
def parse_slug(*, url: str) -> str:
    part = url.split("/")
    if url[-1] == "/":
        return part[-2]
    else:
        return part[-1]


@logger.logging_function()
def get_post_id(*, slug: str, url_post: str) -> int:
    resp = http_client_sec3(f"{url_post}?slug={slug}")
    data = json.load(resp)
    return [x["id"] for x in data if x["slug"] == slug][0]


@logger.logging_function()
def put_post_id(*, post_id: int, client: DynamoDBClient, table: Table):
    try:
        table.put_item(
            Item={"post_id": str(post_id)},
            ConditionExpression=Attr("post_id").not_exists(),
        )
    except client.exceptions.ConditionalCheckFailedException:
        logger.debug("already exists")
