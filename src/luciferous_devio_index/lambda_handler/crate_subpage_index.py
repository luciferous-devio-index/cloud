from dataclasses import dataclass
from os.path import basename
from typing import List

from jinja2 import Template
from mypy_boto3_s3 import S3Client

from luciferous_devio_index.common.aws import create_client
from luciferous_devio_index.common.dataclasses import load_environment
from luciferous_devio_index.common.jinja_templates import TEMPLATE_SUBPAGE_INDEX
from luciferous_devio_index.common.logger import MyLogger


@dataclass()
class EnvironmentVariables:
    s3_bucket: str
    target_dir: str
    target_extension: str


@dataclass()
class Content:
    name: str
    last_modified_at: str
    size: int

    def get_number(self) -> int:
        index = self.name.find(".")
        return int(self.name[:index])


logger = MyLogger(__name__)


@logger.logging_handler()
def handler(event, context, s3_client: S3Client = create_client("s3")):
    env = load_environment(class_dataclass=EnvironmentVariables)
    contents = get_contents(env=env, s3_client=s3_client)
    contents = sort_contents(target_dir=env.target_dir, contents=contents)
    text = create_index_text(target_dir=env.target_dir, contents=contents)
    upload_index(env=env, text=text, s3_client=s3_client)


@logger.logging_function(with_return=False)
def get_contents(*, env: EnvironmentVariables, s3_client: S3Client) -> List[Content]:
    result: List[Content] = []
    for resp in s3_client.get_paginator("list_objects_v2").paginate(
        Bucket=env.s3_bucket, Prefix=f"{env.target_dir}/"
    ):
        result += [
            Content(
                name=basename(x["Key"]),
                last_modified_at=x["LastModified"].strftime("%Y-%m-%d %H:%M:%S"),
                size=x["Size"],
            )
            for x in resp.get("Contents", [])
            if x["Key"][-len(env.target_extension) :] == env.target_extension
        ]
    return result


@logger.logging_function()
def sort_contents(*, target_dir: str, contents: List[Content]) -> List[Content]:
    if target_dir == "posts":
        return sorted(contents, key=lambda x: x.get_number(), reverse=True)
    elif target_dir == "archives":
        return sorted(contents, reverse=True)
    else:
        raise ValueError('invalid target dir')


@logger.logging_function(with_arg=False)
def create_index_text(*, target_dir: str, contents: List[Content]) -> str:
    template = Template(TEMPLATE_SUBPAGE_INDEX)
    return template.render(path=target_dir, contents=contents)


@logger.logging_function(with_arg=False)
def upload_index(*, env: EnvironmentVariables, text: str, s3_client: S3Client):
    s3_client.put_object(
        Bucket=env.s3_bucket,
        Key=f"{env.target_dir}/index.html",
        ContentType="text/html",
        Body=text.encode(),
    )
