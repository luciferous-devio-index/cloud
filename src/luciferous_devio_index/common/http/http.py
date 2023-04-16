from datetime import datetime
from time import sleep
from typing import AnyStr, Callable, Optional
from urllib.request import urlopen

from luciferous_devio_index.common.logger import MyLogger

logger = MyLogger(__name__)


def create_http_client(sec: int) -> Callable[[str], AnyStr]:
    dt_prev: Optional[datetime] = None

    @logger.logging_function()
    def process(url: str) -> AnyStr:
        nonlocal dt_prev
        if dt_prev is not None:
            delta = datetime.now() - dt_prev
            wait = sec - delta.total_seconds()
            if wait > 0:
                sleep(wait)

        resp = urlopen(url)
        dt_prev = datetime.now()
        return resp.read()

    return process
