#!/usr/bin/env bash
# Deploy or update one environment: terraform apply + sync web/ to S3 + invalidate CloudFront.
# Usage: ./scripts/deploy.sh [env=dev] [region=ap-south-1]
set -euo pipefail
ENV="${1:-dev}"
REGION="${2:-ap-south-1}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF="$ROOT/infra/terraform"

echo "==> pytest"
python -m pytest "$ROOT/tests/" -q

echo "==> terraform init/apply ($ENV, $REGION)"
terraform -chdir="$TF" init
terraform -chdir="$TF" validate
terraform -chdir="$TF" apply -var="environment=$ENV" -var="aws_region=$REGION" -auto-approve

BUCKET="$(terraform -chdir="$TF" output -raw web_bucket)"
DIST_ID="$(terraform -chdir="$TF" output -raw cloudfront_distribution_id)"
API="$(terraform -chdir="$TF" output -raw api_endpoint)"
CLIENT_ID="$(terraform -chdir="$TF" output -raw user_pool_client_id)"
DOMAIN="$(terraform -chdir="$TF" output -raw cognito_domain)"

echo "==> sync web/ to s3://$BUCKET"
aws s3 sync "$ROOT/web" "s3://$BUCKET" --delete --exclude "config.js" --exclude "config.example.js"
aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*"

cat <<EOF
Done.
  API:        $API
  CloudFront: $(terraform -chdir="$TF" output -raw cloudfront_url)
Next: create web/config.js with apiEndpoint=$API, userPoolClientId=$CLIENT_ID, cognitoDomain=$DOMAIN
EOF
