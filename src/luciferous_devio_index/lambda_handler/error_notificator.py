import json
from base64 import b64decode
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from gzip import decompress
from typing import Optional
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from mypy_boto3_ssm import SSMClient

from luciferous_devio_index.common.aws import create_client
from luciferous_devio_index.common.dataclasses import load_environment
from luciferous_devio_index.common.logger import MyLogger
from luciferous_devio_index.common.ssm import get_parameter_slack_incoming_webhook_url

jst = timezone(offset=timedelta(hours=+9), name="JST")


@dataclass()
class EnvironmentVariables:
    aws_default_region: str


@dataclass()
class LogData:
    log_group: str
    log_stream: str
    message: str
    timestamp: int


logger = MyLogger(__name__)


@logger.logging_handler(with_return=False)
def handler(event: dict, context, ssm_client: SSMClient = create_client("ssm")):
    log = parse_event(event=event)
    env = load_environment(class_dataclass=EnvironmentVariables)
    message = create_message(log=log, region=env.aws_default_region)
    url = get_parameter_slack_incoming_webhook_url(ssm_client)
    post_message(message=message, url=url)


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


@logger.logging_function()
def create_url_cw_logs(
    *,
    name_log_group: str,
    name_log_stream: str,
    timestamp: int,
    lambda_request_id: Optional[str],
    region: str,
) -> str:
    part = [
        "https://",
        region,
        ".console.aws.amazon.com/cloudwatch/home?region=",
        region,
        "#logsV2:log-groups/log-group/",
        quote_plus(quote_plus(name_log_group)).replace("%", "$"),
        "/log-events/",
        quote_plus(quote_plus(name_log_stream)).replace("%", "$"),
    ]
    if lambda_request_id is None:
        part.append(
            quote_plus(quote_plus(f"?start={timestamp}")).replace("%", "$"),
        )
    else:
        part.append(
            quote_plus(quote_plus(f'?filterPattern="{lambda_request_id}"')).replace(
                "%", "$"
            )
        )
    return "".join(part)


@logger.logging_function()
def create_url_lambda(*, name_log_group: str, region: str) -> str:
    return "".join(
        [
            "https://",
            region,
            ".console.aws.amazon.com/lambda/home?region=",
            region,
            "#/functions/",
            name_log_group.replace("/aws/lambda/", ""),
        ]
    )


@logger.logging_function()
def create_message(*, log: LogData, region: str) -> str:
    lines = [
        f"<!here> ERROR ({datetime.now(jst)})",
        f"LogGroup: `{log.log_group}`",
        f"LogStream: `{log.log_stream}`",
        f"timestamp: `{log.timestamp}`",
        f"datetime: `{datetime.fromtimestamp(log.timestamp / 1000, jst)}`",
    ]

    request_id = None
    try:
        data = json.loads(log.message)
        if (request_id := data.get("lambda_request_id")) is not None:
            lines.append(f"request id: `{request_id}`")

        message = "\n".join(data.get("msg", []))
    except Exception:
        message = log.message

    lines += [
        "CloudWatch Logs: <{}|Link>".format(
            create_url_cw_logs(
                name_log_group=log.log_group,
                name_log_stream=log.log_stream,
                timestamp=log.timestamp,
                lambda_request_id=request_id,
                region=region,
            )
        ),
        "Lambda: <{}|Link>".format(
            create_url_lambda(name_log_group=log.log_group, region=region)
        ),
    ]

    if len(message) < 100:
        lines += ["message:", "```", message, "```"]
    else:
        lines += ["message (too long):", "```", message[:100], "```"]

    return "\n".join(lines)


@logger.logging_function()
def post_message(*, message: str, url: str):
    req = Request(
        url=url,
        method="POST",
        headers={
            "Content-Type": "application/json",
        },
        data=json.dumps({"text": message}).encode(),
    )
    urlopen(req)
