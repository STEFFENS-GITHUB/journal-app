import json
import os

import boto3

VERIFY_API_URL = os.getenv("VERIFY_API_URL", "http://localhost:8000/verify-email")
QUEUE_URL = os.environ["EMAIL_VERIFICATION_QUEUE_URL"]
DLQ_URL = os.environ["EMAIL_VERIFICATION_DLQ_URL"]


def move_to_dlq(sqs_client, message, reason):
    print(f"Dead-lettering message {message['MessageId']}: {reason}", flush=True)
    sqs_client.send_message(QueueUrl=DLQ_URL, MessageBody=message["Body"])
    sqs_client.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=message["ReceiptHandle"])


def main():
    sqs_client = boto3.client(
        "sqs",
        endpoint_url=os.getenv("SQS_ENDPOINT_URL") or None,
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )
    while True:
        result = sqs_client.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=10, WaitTimeSeconds=20)
        for message in result.get("Messages", []):
            try:
                body = json.loads(message["Body"])
            except json.JSONDecodeError as e:
                move_to_dlq(sqs_client, message, f"malformed body: {e}")
                continue
            try:
                token = body["token"]
            except (KeyError, TypeError):
                move_to_dlq(sqs_client, message, "missing token")
                continue
            # TODO: send this URL to body["email"] instead of printing it
            print(f"{VERIFY_API_URL}?token={token}", flush=True)
            sqs_client.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=message["ReceiptHandle"])


if __name__ == "__main__":
    main()
