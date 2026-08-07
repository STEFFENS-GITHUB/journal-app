import asyncio
import json
import os

import boto3
from botocore.config import Config

from api.utils.logging import log_event

def create_sqs_client(connect_timeout: int = 3, read_timeout: int = 5, max_attempts: int = 2):
    return boto3.client(
        "sqs",
        endpoint_url=os.getenv("SQS_ENDPOINT_URL") or None,
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        config=Config(connect_timeout=connect_timeout, read_timeout=read_timeout,
                      retries={"max_attempts": max_attempts}),
    )

async def send_email_verification_message(sqs_client, user_id: int, email: str, token: str, request_id: str | None = None) -> None:
    queue_url = os.getenv("EMAIL_VERIFICATION_QUEUE_URL")
    body = json.dumps({"v": 1, "user_id": user_id, "email": email, "token": token, "request_id": request_id})
    try:
        await asyncio.to_thread(sqs_client.send_message, QueueUrl=queue_url, MessageBody=body)
    except Exception as e:
        # Registration must not fail because the queue is unavailable.
        log_event("ERROR", "email_verification_enqueue_failed",
                  user_id=user_id, request_id=request_id, error=str(e))
