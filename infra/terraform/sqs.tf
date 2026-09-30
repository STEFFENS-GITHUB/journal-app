resource "aws_sqs_queue" "journal_queue_dlq" {
  name = "${var.env}-journal-queue-dlq"

  tags = {
    Environment = var.env
  }
}

resource "aws_sqs_queue" "journal_queue" {
  name                       = "${var.env}-journal-queue"
  visibility_timeout_seconds = 30
  receive_wait_time_seconds  = 20

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.journal_queue_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Environment = var.env
  }
}
