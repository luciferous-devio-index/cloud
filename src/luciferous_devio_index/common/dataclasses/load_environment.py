import os
from dataclasses import fields
from typing import Type, TypeVar

from luciferous_devio_index.common.logger import MyLogger

logger = MyLogger(__name__)

T = TypeVar("T")


@logger.logging_function()
def load_environment(*, class_dataclass: Type[T]) -> T:
    return class_dataclass(
        **{k.name: os.environ[k.name.upper()] for k in fields(class_dataclass)}
    )
