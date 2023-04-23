import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from shutil import make_archive

from luciferous_devio_index.common.logger import MyLogger


@dataclass()
class Arguments:
    s3_bucket: str
    s3_posts_prefix: str
    s3_archives_prefix: str


logger = MyLogger(__name__)


@logger.logging_main()
def main():
    args = parse_args()
    download_posts(bucket=args.s3_bucket, prefix=args.s3_posts_prefix)
    name = create_archive(prefix=args.s3_posts_prefix)
    put_s3(file_name=name, bucket=args.s3_bucket, prefix=args.s3_archives_prefix)


@logger.logging_function()
def parse_args() -> Arguments:
    target_mapping = {
        "s3_bucket": "--s3-bucket",
        "s3_posts_prefix": "--s3-posts-prefix",
        "s3_archives_prefix": "--s3-archives-prefix",
    }
    options = {}
    key = None
    for arg in sys.argv:
        if key is not None:
            options[key] = arg
            key = None
        else:
            for k, v in target_mapping.items():
                if arg == v:
                    key = k

    return Arguments(**options)


@logger.logging_function()
def download_posts(*, bucket: str, prefix: str):
    subprocess.run(
        f"aws s3 cp --recursive s3://{bucket}/{prefix}/ {prefix}", shell=True
    )


@logger.logging_function()
def create_archive(prefix: str):
    now = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%Z")
    name = f"devio-posts-{now}"
    return make_archive(name, format="zip", root_dir=".", base_dir=prefix)


@logger.logging_function()
def put_s3(file_name: str, bucket: str, prefix: str):
    subprocess.run(
        f"aws s3 cp {file_name} s3://{bucket}/{prefix}/{file_name}", shell=True
    )


if __name__ == "__main__":
    main()
