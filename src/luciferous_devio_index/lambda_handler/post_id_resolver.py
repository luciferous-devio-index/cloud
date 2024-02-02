import json
from dataclasses import dataclass
from typing import List

from luciferous_devio_index.common.dataclasses import load_environment
from luciferous_devio_index.common.http import http_client_sec3
from luciferous_devio_index.common.logger import MyLogger


@dataclass
class EnvironmentVariables:
    url_post: str
    table_post_id: str


logger = MyLogger(__name__)


@logger.logging_handler(with_return=False)
def handler(event: dict, _context):
    env = load_environment(class_dataclass=EnvironmentVariables)
    url = parse_url(event=event)
    slug = parse_slug(url=url)
    post_id = get_post_id(slug=slug, url_post=env.url_post)
    logger.info("url, slug, and post_id", url=url, slug=slug, post_id=post_id)


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
def get_post_id(*, slug: str, url_post: str) -> List[int]:
    resp = http_client_sec3(f"{url_post}?slug={slug}")
    data = json.load(resp)
    return [x["id"] for x in data]
