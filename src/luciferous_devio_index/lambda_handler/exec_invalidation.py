from dataclasses import dataclass
from uuid import uuid4

from mypy_boto3_cloudfront import CloudFrontClient

from luciferous_devio_index.common.aws import create_client
from luciferous_devio_index.common.dataclasses import load_environment
from luciferous_devio_index.common.logger import MyLogger


@dataclass(frozen=True)
class EnvironmentVariables:
    distribution_id: str


logger = MyLogger(__name__)


@logger.logging_handler()
def handler(
    event, context, client_cloudfront: CloudFrontClient = create_client("cloudfront")
):
    env = load_environment(class_dataclass=EnvironmentVariables)
    create_invalidation(
        distribution_id=env.distribution_id, cloudfront_client=client_cloudfront
    )


@logger.logging_function()
def create_invalidation(*, distribution_id: str, cloudfront_client: CloudFrontClient):
    cloudfront_client.create_invalidation(
        DistributionId=distribution_id,
        InvalidationBatch={
            "CallerReference": str(uuid4()),
            "Paths": {
                "Quantity": 2,
                "Items": ["/archives/index.html", f"/posts/index.html"],
            },
        },
    )
