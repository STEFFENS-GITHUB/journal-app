ephemeral "random_password" "api_jwt_signing_key" {
  length  = 64
  special = false
}

resource "aws_secretsmanager_secret" "api_jwt_signing_key" {
  name                    = "${var.env}/journal/api-jwt-signing-key"
  recovery_window_in_days = 0

  tags = {
    Environment = var.env
  }
}

resource "aws_secretsmanager_secret_version" "api_jwt_signing_key" {
  secret_id                = aws_secretsmanager_secret.api_jwt_signing_key.id
  secret_string_wo         = ephemeral.random_password.api_jwt_signing_key.result
  secret_string_wo_version = 1
}
