from dataclasses import dataclass

from mypy_boto3_glue import GlueClient

from luciferous_devio_index.common.aws import create_client
from luciferous_devio_index.common.dataclasses import load_environment
from luciferous_devio_index.common.logger import MyLogger


@dataclass()
class EnvironmentVariables:
    target_job_name: str


logger = MyLogger(__name__)


@logger.logging_handler()
def handler(event, context, glue_client: GlueClient = create_client("glue")):
    env = load_environment(class_dataclass=EnvironmentVariables)
    call_job(job_name=env.target_job_name, glue_client=glue_client)


@logger.logging_function()
def call_job(*, job_name: str, glue_client: GlueClient):
    glue_client.start_job_run(JobName=job_name)
