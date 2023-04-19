import json
from base64 import b64decode
from dataclasses import dataclass
from gzip import decompress

from luciferous_devio_index.common.logger import MyLogger


@dataclass()
class LogData:
    log_group: str
    log_stream: str
    message: str
    timestamp: int


logger = MyLogger(__name__)


@logger.logging_handler(with_return=False)
def handler(event: dict, context):
    parse_event(event=event)


@logger.logging_function()
def parse_event(*, event: dict) -> LogData:
    data = event["awslogs"]["data"]
    raw_record = decompress(b64decode(data))
    record = json.loads(raw_record)
    return LogData(
        log_group=record["logGroup"],
        log_stream=record["logStream"],
        message=record["logEvents"][0]["message"],
        timestamp=record["logEvents"][0]["timestamp"],
    )
