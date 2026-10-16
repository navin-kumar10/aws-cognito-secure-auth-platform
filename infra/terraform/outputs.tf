output "api_endpoint" {
  description = "HTTP API base URL."
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "user_pool_id" {
  value = aws_cognito_user_pool.main.id
}

output "user_pool_client_id" {
  value = aws_cognito_user_pool_client.web.id
}

output "cognito_domain" {
  description = "Hosted UI domain (configure in web/config.js)."
  value       = "${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com"
}

output "hosted_ui_url" {
  description = "Full Hosted UI login URL."
  value       = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com/login?client_id=${aws_cognito_user_pool_client.web.id}&response_type=code&scope=openid+email+profile&redirect_uri=${urlencode(local.first_callback)}"
}

output "cloudfront_url" {
  value = "https://${aws_cloudfront_distribution.web.domain_name}"
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.web.id
}

output "web_bucket" {
  value = aws_s3_bucket.web.id
}

output "dynamodb_table" {
  value = aws_dynamodb_table.profiles.name
}
