import json
import logging
import os
from collections import UserList
from decimal import Decimal
from enum import Enum

from boto3.dynamodb.conditions import AttributeBase, ConditionBase

LAMBDA_REQUEST_ID_ENVIRONMENT_VALUE_NAME = "LAMBDA_REQUEST_ID"
import dataclasses


def default(obj):
    if isinstance(obj, Decimal):
        return int(obj) if int(obj) == obj else float(obj)
    elif isinstance(obj, (set, UserList)):
        return list(obj)
    elif isinstance(obj, ConditionBase):
        return obj.get_expression()
    elif isinstance(obj, AttributeBase):
        return obj.name
    elif isinstance(obj, Enum):
        return obj.value
    elif dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    try:
        return {"type": str(type(obj)), "value": str(obj)}
    except Exception:
        return {"type": str(type(obj)), "value": None}


class JsonLogFormatter(logging.Formatter):
    def format(self, record):
        result = {
            "lambda_request_id": os.environ.get(
                LAMBDA_REQUEST_ID_ENVIRONMENT_VALUE_NAME
            )
        }

        for attr, value in record.__dict__.items():
            # 不要な列を削除
            if attr in [
                "pathname",
                "filename",
                "module",
                "funcName",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            ]:
                continue
            if attr == "asctime":
                value = self.formatTime(record)
            if attr == "exc_info" and value is not None:
                value = self.formatException(value)
                if isinstance(value, str):
                    value = value.split("\n")
            if attr == "stack_info" and value is not None:
                value = self.formatStack(value)
            if attr == "msg":
                try:
                    value = record.getMessage().split("\n")
                except Exception:
                    pass

            result[attr] = value
        return json.dumps(result, default=default, ensure_ascii=False)
