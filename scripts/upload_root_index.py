import json
import subprocess
from sys import argv


def main():
    stack_name = argv[1]
    bucket_name = get_bucket_name(stack_name=stack_name)
    upload(bucket_name=bucket_name)


def get_bucket_name(*, stack_name: str) -> str:
    resp = subprocess.run(
        f"aws cloudformation describe-stacks --stack-name {stack_name} --query Stacks[0].Outputs --output json",
        shell=True,
        capture_output=True,
    )
    outputs = json.loads(resp.stdout)
    for x in outputs:
        if x["OutputKey"] == "BucketNameDevioData":
            return x["OutputValue"]


def upload(*, bucket_name: str):
    subprocess.run(
        f"aws s3 cp assets/root_index.html s3://{bucket_name}/index.html", shell=True
    )


if __name__ == "__main__":
    main()
