from dataclasses import dataclass
from typing import List, Set
from uuid import uuid4

import feedparser
from boto3.dynamodb.conditions import Attr
from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource
from mypy_boto3_sqs import SQSClient

from luciferous_devio_index.common.aws import create_client, create_resource
from luciferous_devio_index.common.dataclasses import load_environment
from luciferous_devio_index.common.logger import MyLogger


@dataclass
class EnvironmentVariables:
    url_feed: str
    table_name: str
    queue_url: str


logger = MyLogger(__name__)


@logger.logging_handler(with_return=False)
def handler(
    _event: dict,
    _context,
    client_sqs: SQSClient = create_client("sqs"),
    client_ddb: DynamoDBClient = create_client("dynamodb"),
    resource_ddb: DynamoDBServiceResource = create_resource("dynamodb"),
):
    env = load_environment(class_dataclass=EnvironmentVariables)
    entries = get_feed_entries(url=env.url_feed)
    list_post_id = parse_post_id(entries)
    check_post_id(list_post_id=list_post_id)
    for post_id in list_post_id:
        put_post_id(
            post_id=post_id,
            table_name=env.table_name,
            ddb_client=client_ddb,
            ddb_resource=resource_ddb,
        )


@logger.logging_function()
def get_feed_entries(*, url: str) -> List[dict]:
    return feedparser.parse(url)["entries"]


@logger.logging_function(write_log=False)
def parse_post_id(*, entries: List[dict]) -> List[str]:
    return [str(x["post-id"]) for x in entries]


@logger.logging_function(write_log=True)
def check_post_id(*, list_post_id: list[str]):
    for post_id in list_post_id:
        int(post_id)


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


@logger.logging_function(write_log=False)
def parse_url(*, entries: List[dict]) -> List[str]:
    return [x["link"] for x in entries]


@logger.logging_function(write_log=True, with_arg=True)
def send_messages(*, list_url: List[str], queue_url: str, client: SQSClient):
    union_succeeded_id: Set[str] = set()
    map_url = {str(uuid4()): x for x in list_url}

    while len(union_succeeded_id) != len(map_url):
        entries = []
        for message_id, url in map_url.items():
            if len(entries) == 10:
                break
            if message_id in union_succeeded_id:
                continue
            entries.append({"Id": message_id, "MessageBody": url})

        option = {"QueueUrl": queue_url, "Entries": entries}
        logger.debug("send message batch", option=option)
        resp = client.send_message_batch(**option)

        union_succeeded_id |= set([x["Id"] for x in resp["Successful"]])

        for item in resp.get("Failed", []):
            logger.warning("send failed item", item=item)
