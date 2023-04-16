from dataclasses import dataclass
from typing import List

import feedparser
from boto3.dynamodb.conditions import Attr
from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource

from luciferous_devio_index.common.aws import create_client, create_resource
from luciferous_devio_index.common.dataclasses import load_environment
from luciferous_devio_index.common.logger import MyLogger


@dataclass
class EnvironmentVariables:
    url_feed: str
    ddb_table_name: str


logger = MyLogger(__name__)


@logger.logging_handler(with_return=False)
def handler(
    _event: dict,
    _context,
    ddb_client: DynamoDBClient = create_client("dynamodb"),
    ddb_resource: DynamoDBServiceResource = create_resource("dynamodb"),
):
    env = load_environment(class_dataclass=EnvironmentVariables)
    entries = get_feed_entries(url=env.url_feed)
    list_post_id = parse_post_id(entries=entries)
    for post_id in list_post_id:
        put_post_id(
            post_id=post_id,
            table_name=env.ddb_table_name,
            ddb_client=ddb_client,
            ddb_resource=ddb_resource,
        )


@logger.logging_function()
def get_feed_entries(*, url: str) -> List[dict]:
    return feedparser.parse(url)["entries"]


@logger.logging_function(write_log=False)
def parse_post_id(*, entries: List[dict]) -> List[str]:
    return [str(x["post-id"]) for x in entries]


@logger.logging_function()
def put_post_id(
    *,
    post_id: str,
    table_name: str,
    ddb_client: DynamoDBClient,
    ddb_resource: DynamoDBServiceResource
):
    try:
        table = ddb_resource.Table(table_name)
        table.put_item(
            Item={"post_id": post_id}, ConditionExpression=Attr("post_id").not_exists()
        )
    except ddb_client.exceptions.ConditionalCheckFailedException:
        pass
