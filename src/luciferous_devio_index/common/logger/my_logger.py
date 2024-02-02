import os
import sys
from datetime import datetime
from functools import wraps
from logging import DEBUG
from typing import Callable
from uuid import uuid4

import boto3
import botocore
from aws_lambda_powertools import Logger

from .function_stats_borg import FunctionDurationStatsBorg
from .json_log_formatter import LAMBDA_REQUEST_ID_ENVIRONMENT_VALUE_NAME, default

ENVIRONMENT_VARIABLES_NOT_LOGGING = [
    "AWS_ACCESS_KEY_ID",
    "AWS_DEFAULT_REGION",
    "AWS_LAMBDA_LOG_GROUP_NAME",
    "AWS_LAMBDA_LOG_STREAM_NAME",
    "AWS_REGION",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SECURITY_TOKEN",
    "AWS_SESSION_TOKEN",
    "_AWS_XRAY_DAEMON_ADDRESS",
    "_AWS_XRAY_DAEMON_PORT",
    "AWS_XRAY_DAEMON_ADDRESS",
]

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)


class LambdaContextDummy(object):
    aws_request_id: str


class MyLogger(object):
    """ログのJSON整形などを設定したロガー

    ログをJSON整形したりさせるためのロガー。また任意の情報を名前付き引数でログに残すこともできる。
    """

    name: str
    logger: Logger
    measure: FunctionDurationStatsBorg

    def __init__(self, name: str):
        self.name = name
        self.logger = Logger(
            service=name,
            level=DEBUG,
            json_default=default,
            use_rfc3339=True,
        )
        self.measure = FunctionDurationStatsBorg()

    def debug(self, msg, *args, exc_info: bool = False, **kwargs) -> None:
        self.logger.debug(
            msg, *args, exc_info=exc_info, extra={"additional_data": kwargs}
        )

    def info(self, msg, *args, exc_info: bool = False, **kwargs) -> None:
        self.logger.info(
            msg, *args, exc_info=exc_info, extra={"additional_data": kwargs}
        )

    def warning(self, msg, *args, exc_info: bool = False, **kwargs) -> None:
        self.logger.warning(
            msg, *args, exc_info=exc_info, extra={"additional_data": kwargs}
        )

    def error(self, msg, *args, exc_info: bool = True, **kwargs) -> None:
        self.logger.error(
            msg, *args, exc_info=exc_info, extra={"additional_data": kwargs}
        )

    def logging_function(
        self, with_arg: bool = True, with_return: bool = True, write_log: bool = False
    ) -> Callable:
        def wrapper(func):
            @wraps(func)
            def process(*args, **kwargs):
                func_id = str(uuid4())
                name = func.__name__

                start_kwargs = {"func_id": func_id, "function_name": name}
                if with_arg:
                    start_kwargs["args"] = args
                    start_kwargs["kwargs"] = kwargs
                before = datetime.now()
                if write_log:
                    self.debug(f"function {name} start ({func_id})", **start_kwargs)

                result = None
                is_succeed = True
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception:
                    is_succeed = False
                    raise
                finally:
                    after = datetime.now()
                    delta = after - before
                    self.measure.append(self.name, name, delta.total_seconds())

                    status = "success" if is_succeed else "failed"
                    end_kwargs = {
                        "func_id": func_id,
                        "function_name": name,
                        "duration": str(delta),
                        "duration_sec": delta.total_seconds(),
                        "is_succeed": is_succeed,
                    }
                    if with_return and is_succeed:
                        end_kwargs["return"] = result
                    if write_log or not is_succeed:
                        mess = f"function {name} end ({status}) ({func_id}) (Duration: {delta})"
                        if is_succeed:
                            self.debug(mess, **end_kwargs)
                        else:
                            end_kwargs["args"] = args
                            end_kwargs["kwargs"] = kwargs
                            self.debug(mess, **end_kwargs)

            return process

        return wrapper

    def logging_handler(self, with_return: bool = True) -> Callable:
        """Lambdaのハンドラーのロギングを行うデコレーター

        Args:
            with_return: ログにハンドラーの返り値を含めるかどうか

        Returns:
            Lambdaのハンドラーのロギングを行う関数
        """

        def wrapper(handler):
            @wraps(handler)
            @self.logger.inject_lambda_context()
            def process(event, context: LambdaContextDummy, *args, **kwargs):
                try:
                    # LambdaのRequest IDを環境変数に保存する (LogFormatterで使用するため)
                    os.environ[
                        LAMBDA_REQUEST_ID_ENVIRONMENT_VALUE_NAME
                    ] = context.aws_request_id
                except Exception as e:
                    self.warning(
                        f"exception occurred in set environ lambda request id: {e}"
                    )

                try:
                    # Lambdaのeventの内容やpython, boto3などのバージョン、環境変数を記録する
                    self.debug(
                        "event, python/boto3/botocore version, environment variables",
                        event=event,
                        version={
                            "python": sys.version,
                            "boto3": boto3.__version__,
                            "botocore": botocore.__version__,
                        },
                        environments={
                            k: v
                            for k, v in os.environ.items()
                            if k not in ENVIRONMENT_VARIABLES_NOT_LOGGING
                        },
                    )
                except Exception as e:
                    self.warning(
                        f"Exception occurred in logging event and version and environment variables: {e}"
                    )

                try:
                    result = handler(event, context, *args, **kwargs)
                    if with_return:
                        self.debug("handler result", result=result)
                    return result
                except Exception as e:
                    self.error(f"Exception occurred in handler: {e}")
                    raise
                finally:
                    self.debug("function stats", stats=self.measure.get_stats())

            return process

        return wrapper

    def logging_main(self) -> Callable:
        def wrapper(handler):
            @wraps(handler)
            def process(*args, **kwargs):
                try:
                    self.debug("argv", argv=sys.argv)
                except Exception as e:
                    self.warning(f"Exception occurred in logging argv: [{type(e)}] {e}")

                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    self.error(f"Exception occurred in main: [{type(e)}] {e}")
                    raise
                finally:
                    self.debug("function stats", stats=self.measure.get_stats())

            return process

        return wrapper
