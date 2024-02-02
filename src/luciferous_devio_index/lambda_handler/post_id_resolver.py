from dataclasses import dataclass

from luciferous_devio_index.common.dataclasses import load_environment
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
    logger.info("url", url=url)


def parse_url(*, event: dict) -> str:
    if (url := event.get("url")) is not None:
        return url
    return event["Records"][0]["body"]
