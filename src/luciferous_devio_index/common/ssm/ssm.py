from mypy_boto3_ssm import SSMClient

NAME_OPEN_AI_API_KEY = "/LuciferousDevIoIndex/Secrets/OpenAiApiKey"
NAME_SLACK_INCOMING_WEBHOOK = "/LuciferousDevIoIndex/Secrets/SlackIncomingWebhook"


def get_parameter_open_ai_api_key(ssm_client: SSMClient) -> str:
    resp = ssm_client.get_parameter(Name=NAME_OPEN_AI_API_KEY, WithDecryption=True)
    return resp["Parameter"]["Value"]


def get_parameter_slack_incoming_webhook_url(ssm_client) -> str:
    resp = ssm_client.get_parameter(
        Name=NAME_SLACK_INCOMING_WEBHOOK, WithDecryption=True
    )
    return resp["Parameter"]["Value"]
