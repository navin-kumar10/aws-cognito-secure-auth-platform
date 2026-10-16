variable "project_name" {
  description = "Resource name prefix (lowercase, hyphenated)."
  type        = string
  default     = "secure-auth"
}

variable "aws_region" {
  description = "Deploy region."
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment label (dev/stage/prod)."
  type        = string
  default     = "dev"
}

variable "cognito_domain_prefix" {
  description = "Globally unique Cognito hosted domain prefix."
  type        = string
}

variable "callback_urls" {
  description = "Allowed Cognito callback URLs (CloudFront URL + localhost for dev)."
  type        = list(string)
  default     = ["http://localhost:8000/"]
}

variable "logout_urls" {
  description = "Allowed Cognito sign-out URLs."
  type        = list(string)
  default     = ["http://localhost:8000/"]
}

variable "google_client_id" {
  description = "Google OAuth client ID. Empty disables the Google IdP."
  type        = string
  default     = ""
  sensitive   = true
}

variable "google_client_secret" {
  description = "Google OAuth client secret. Empty disables the Google IdP."
  type        = string
  default     = ""
  sensitive   = true
}

variable "enable_waf" {
  description = "Attach AWS WAF (rate limit + managed rules) to CloudFront and the HTTP API."
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Custom domain for CloudFront (e.g. app.example.com). Empty = CloudFront default domain."
  type        = string
  default     = ""
}

variable "hosted_zone_id" {
  description = "Route53 hosted zone ID for domain_name. Required when domain_name is set."
  type        = string
  default     = ""
}

variable "admin_emails" {
  description = "Emails auto-added to the Cognito admins group after first sign-in (managed manually)."
  type        = list(string)
  default     = []
}
