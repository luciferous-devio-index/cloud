import json
from dataclasses import asdict, dataclass
from datetime import datetime
from io import BytesIO
from os.path import basename
from zipfile import ZipFile

from mypy_boto3_dynamodb import DynamoDBServiceResource
from mypy_boto3_s3 import S3Client

from luciferous_devio_index.common.aws import create_client, create_resource
from luciferous_devio_index.common.dataclasses import load_environment
from luciferous_devio_index.common.logger import MyLogger
from luciferous_devio_index.common.models import SlugMappingData


@dataclass(frozen=True)
class EnvironmentVariables:
    dynamodb_table: str


@dataclass(frozen=True)
class S3Object:
    bucket: str
    key: str


logger = MyLogger(__name__)


@logger.logging_handler()
def handler(
    event,
    context,
    dynamodb_resource: DynamoDBServiceResource = create_resource("dynamodb"),
    s3_client: S3Client = create_client("s3"),
):
    env = load_environment(class_dataclass=EnvironmentVariables)
    obj = parse_event(event=event)
    post_data = get_post_data(obj=obj, s3_client=s3_client)
    put_item(
        post_data=post_data,
        table_name=env.dynamodb_table,
        dynamodb_resource=dynamodb_resource,
    )


@logger.logging_function()
def parse_event(*, event: dict) -> S3Object:
    body = event["Records"][0]["body"]
    data = json.loads(body)
    message = data["Message"]
    data = json.loads(message)
    return S3Object(
        bucket=data["Records"][0]["s3"]["bucket"]["name"],
        key=data["Records"][0]["s3"]["object"]["key"],
    )


@logger.logging_function()
def get_post_data(*, obj: S3Object, s3_client: S3Client) -> SlugMappingData:
    resp = s3_client.get_object(Bucket=obj.bucket, Key=obj.key)
    io = BytesIO(resp["Body"].read())
    with ZipFile(io) as zf:
        with zf.open(basename(obj.key.replace(".zip", ""))) as f:
            data = json.load(f)
    lastmod = data["modified_gmt"]
    return SlugMappingData(
        slug=data["slug"],
        post_id=str(data["id"]),
        timestamp=int(
            datetime.strptime(f"{lastmod}+0000", "%Y-%m-%dT%H:%M:%S%z").timestamp()
            * 1000
        ),
    )


@logger.logging_function()
def put_item(
    *,
    post_data: SlugMappingData,
    table_name: str,
    dynamodb_resource: DynamoDBServiceResource,
):
    dynamodb_resource.Table(table_name).put_item(Item=asdict(post_data))
