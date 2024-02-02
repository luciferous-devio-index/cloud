import json
from dataclasses import dataclass
from datetime import datetime
from typing import AnyStr, Iterator, List, Optional

from bs4 import BeautifulSoup, Tag
from mypy_boto3_dynamodb import DynamoDBServiceResource
from mypy_boto3_dynamodb.service_resource import Table

from luciferous_devio_index.common.aws import create_resource
from luciferous_devio_index.common.dataclasses import load_environment
from luciferous_devio_index.common.http import http_client_sec3
from luciferous_devio_index.common.logger import MyLogger
from luciferous_devio_index.common.models import SlugMappingData


@dataclass(frozen=True)
class EnvironmentVariables:
    devio_posts_url: str
    table_slug_mapping: str
    table_post_id: str


@dataclass(frozen=True)
class SitemapData:
    slug: str
    updated_at: int


logger = MyLogger(__name__)


@logger.logging_handler()
def handler(
    event: dict,
    context,
    ddb_resource: DynamoDBServiceResource = create_resource("dynamodb"),
):
    env = load_environment(class_dataclass=EnvironmentVariables)
    table_slug_mapping = ddb_resource.Table(env.table_slug_mapping)
    table_post_id = ddb_resource.Table(env.table_post_id)
    url = parse_url(event=event)
    text = get_sitemap(url=url)
    posts = [
        post_id
        for sitemap in parse_individual_sitemap(text=text)
        if (
            post_id := check_updated_post(
                sitemap=sitemap,
                url_devio_posts=env.devio_posts_url,
                table_slug_mapping=table_slug_mapping,
            )
        )
        is not None
    ]
    put_posts(posts=posts, table=table_post_id)


@logger.logging_function()
def parse_url(*, event: dict) -> str:
    if (url := event.get("url")) is not None:
        return url
    raw_ddb_event = event["Records"][0]["body"]
    ddb_event = json.loads(raw_ddb_event)
    return ddb_event["dynamodb"]["Keys"]["url"]["S"]


@logger.logging_function()
def get_sitemap(*, url: str) -> AnyStr:
    resp = http_client_sec3(url)
    return resp.read()


@logger.logging_function()
def parse_individual_sitemap(*, text: AnyStr) -> Iterator[SitemapData]:
    def parse_slug(url: str) -> str:
        for part in reversed(url.split("/")):
            if part:
                return part

    bs = BeautifulSoup(text, "xml")
    for tag in bs.select("url"):
        tag: Tag

        slug = parse_slug(tag.select_one("loc").text)
        lastmod = tag.select_one("lastmod").text
        yield SitemapData(
            slug=slug,
            updated_at=int(
                datetime.strptime(lastmod, "%Y-%m-%dT%H:%M:%S%z").timestamp() * 1000
            ),
        )


@logger.logging_function()
def get_slug_mapping_data(*, slug: str, table: Table) -> Optional[SlugMappingData]:
    resp = table.get_item(Key={"slug": slug})
    return None if (item := resp.get("Item")) is None else SlugMappingData(**item)


@logger.logging_function()
def search_post_id(*, posts_url: str, slug: str) -> Optional[str]:
    resp = http_client_sec3(f"{posts_url}?context=embed&slug={slug}")
    data = json.loads(resp.read())
    if len(data) == 0:
        return None
    return str(data[0]["id"])


@logger.logging_function()
def check_updated_post(
    *, sitemap: SitemapData, url_devio_posts: str, table_slug_mapping: Table
) -> Optional[str]:
    slug_mapping_data = get_slug_mapping_data(
        slug=sitemap.slug, table=table_slug_mapping
    )
    if slug_mapping_data is None:
        return search_post_id(posts_url=url_devio_posts, slug=sitemap.slug)
    elif slug_mapping_data.timestamp < sitemap.updated_at:
        return slug_mapping_data.post_id
    else:
        return None


@logger.logging_function()
def put_posts(*, posts: List[str], table: Table):
    with table.batch_writer() as batch:
        for post_id in posts:
            batch.delete_item(Key={"post_id": post_id})
    with table.batch_writer() as batch:
        for post_id in posts:
            batch.put_item(Item={"post_id": post_id})
