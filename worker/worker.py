import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

import boto3

VERIFY_API_URL = os.getenv("VERIFY_API_URL", "http://localhost:8000/verify-email")
QUEUE_URL = os.environ["EMAIL_VERIFICATION_QUEUE_URL"]

logger = logging.getLogger("worker")
logger.setLevel(logging.INFO)
logger.propagate = False
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)


def log(level: str, event: str, **fields):
    logger.log(
        logging.getLevelNamesMapping()[level],
        json.dumps({
            "level": level,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "event": event,
            **fields,
        }),
    )


def main():
    sqs_client = boto3.client(
        "sqs",
        endpoint_url=os.getenv("SQS_ENDPOINT_URL") or None,
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )
    while True:
        try:
            result = sqs_client.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=10, WaitTimeSeconds=20)
            for message in result.get("Messages", []):
                body = json.loads(message["Body"])
                token = body["token"]
                # TODO: send this URL to body["email"] instead of logging it
                log("INFO", "verification_url",
                    message_id=message["MessageId"],
                    user_id=body.get("user_id"),
                    request_id=body.get("request_id"),
                    verify_url=f"{VERIFY_API_URL}?token={token}")
                sqs_client.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=message["ReceiptHandle"])
        except Exception as e:
            log("ERROR", "worker_error", error=repr(e))
            time.sleep(5)


if __name__ == "__main__":
    main()
