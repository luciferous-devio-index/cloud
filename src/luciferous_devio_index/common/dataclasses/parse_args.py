from dataclasses import fields
from sys import argv
from typing import Type, TypeVar

from luciferous_devio_index.common.logger import MyLogger

logger = MyLogger(__name__)

T = TypeVar("T")


@logger.logging_function()
def parse_args(*, class_dataclass: Type[T]) -> T:
    target_mapping = {x.name: f"--{x.name.replace('_', '-')}" for x in fields(T)}
    options = {}
    key = None
    for arg in argv:
        if key is not None:
            options[key] = arg
            key = None
        else:
            for k, v in target_mapping.items():
                if arg == v:
                    key = k
                    break
    return class_dataclass(**options)
