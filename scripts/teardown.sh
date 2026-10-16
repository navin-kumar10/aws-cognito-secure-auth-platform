#!/usr/bin/env bash
# Destroy one environment cleanly (empties S3 web bucket first, then terraform destroy).
# Usage: ./scripts/teardown.sh [env=dev] [region=ap-south-1]
set -euo pipefail
ENV="${1:-dev}"
REGION="${2:-ap-south-1}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF="$ROOT/infra/terraform"

BUCKET="$(terraform -chdir="$TF" output -raw web_bucket 2>/dev/null || true)"
if [[ -n "${BUCKET:-}" ]]; then
  echo "==> emptying s3://$BUCKET"
  aws s3 rm "s3://$BUCKET" --recursive || true
fi

echo "==> terraform destroy ($ENV, $REGION)"
terraform -chdir="$TF" destroy -var="environment=$ENV" -var="aws_region=$REGION" -auto-approve

echo "==> verify leftovers (expect ResourceNotFound / empty)"
aws dynamodb describe-table --table-name "secure-auth-$ENV-profiles" --region "$REGION" 2>&1 | head -3 || true
aws wafv2 list-web-acls --scope CLOUDFRONT --region us-east-1 2>&1 | head -5 || true
echo "Teardown complete. See docs/TEARDOWN.md for manual checks."
