from datetime import datetime
from http.client import HTTPResponse
from time import sleep
from typing import Callable, Optional
from urllib.request import urlopen

from luciferous_devio_index.common.logger import MyLogger

logger = MyLogger(__name__)


def create_http_client(sec: int) -> Callable[[str], HTTPResponse]:
    dt_prev: Optional[datetime] = None

    @logger.logging_function()
    def process(url: str) -> HTTPResponse:
        nonlocal dt_prev
        if dt_prev is not None:
            delta = datetime.now() - dt_prev
            wait = sec - delta.total_seconds()
            if wait > 0:
                sleep(wait)

        resp = urlopen(url)
        dt_prev = datetime.now()
        return resp

    return process
