provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1" # CloudFront certs + CLOUDFRONT-scope WAF must live here
}
