SHELL = /usr/bin/env bash -xeuo pipefail

stack_name:=luciferous-devio-index-cloud

isort:
	poetry run isort --profile=black src/ scripts/

black:
	poetry run black src/ scripts/

format: isort black

install:
	poetry install

pyright:
	poetry run pyright src

ipython:
	poetry run ipython

test-unit:
	PYTHONPATH=src:tests/unit/libs_for_test \
	AWS_ACCESS_KEY_ID=dummy \
	AWS_SECRET_ACCESS_KEY=dummy \
	AWS_DEFAULT_REGION=ap-northeast-1 \
	AWS_REGION=ap-northeast-1 \
		poetry run python -m pytest -vv --cov=src tests/unit

test:
	PYTHONPATH=src:tests/unit/libs_for_test \
	AWS_ACCESS_KEY_ID=dummy \
	AWS_SECRET_ACCESS_KEY=dummy \
	AWS_DEFAULT_REGION=ap-northeast-1 \
	AWS_REGION=ap-northeast-1 \
		poetry run python -m pytest -vv --cov=src tests/unit/handlers/test_get_information.py

check: pyright test-unit

package:
	uuidgen > src/uuid.txt
	poetry build --no-cache
	aws s3 cp dist/luciferous_devio_index-0.1.0-py3-none-any.whl s3://${SAM_ARTIFACT_BUCKET}/whl_cloud/
	sam package \
		--s3-bucket ${SAM_ARTIFACT_BUCKET} \
		--s3-prefix cloud \
		--template-file sam.yml \
		--output-template-file template.yml

deploy:
	sam deploy \
		--stack-name $(stack_name) \
		--template-file template.yml \
		--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
		--role-arn ${ROLE_ARN_CLOUDFORMATION_DEPLOY} \
		--no-fail-on-empty-changeset \
		--parameter-overrides \
			BucketArtifacts=${SAM_ARTIFACT_BUCKET}

dry-deploy:
	sam deploy \
		--stack-name $(stack_name) \
		--template-file template.yml \
		--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
		--no-execute-changeset \
		--no-fail-on-empty-changeset

describe:
	aws cloudformation describe-stacks \
		--stack-name $(stack_name) \
		--query Stacks[0].Outputs

upload-root-index:
	python scripts/upload_root_index.py $(stack_name)

.PHONY: \
	install \
	test-unit \
	build \
	package \
	pyright \
	deploy \
	dry-deploy \
	describe

