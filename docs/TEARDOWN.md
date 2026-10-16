# Teardown

Full cleanup — run in this order. Everything was created by Terraform, so destroy is clean as long as the S3 web bucket is emptied first (AWS refuses to delete non-empty buckets).

```bash
./scripts/teardown.sh dev ap-south-1
```

## What the script does

1. `terraform destroy` the environment (with the same `-var-file`/vars used to apply).
2. Empties `s3://<web-bucket>` first (`aws s3 rm --recursive`) — required before bucket delete.
3. Verifies leftovers:
   - `aws dynamodb describe-table`
   - `aws wafv2 list-web-acls --scope CLOUDFRONT --region us-east-1`
   - `aws acm list-certificates --region us-east-1`
   - `aws route53 list-resource-record-sets --hosted-zone-id <id>` (if custom domain)
   - CloudWatch log groups `/aws/lambda/...` and `/aws/apigateway/...`

## Manual fallback

```bash
BUCKET=$(terraform -chdir=infra/terraform output -raw web_bucket)
aws s3 rm "s3://$BUCKET" --recursive
terraform -chdir=infra/terraform destroy
```

## Notes

- Cognito User Pools and DynamoDB tables hold user data — `destroy` deletes them. Export anything you need first.
- CloudFront distributions can take 10–20 min to fully delete; `destroy` waits for disable+delete automatically.
- If destroy fails on the S3 bucket, re-run the `aws s3 rm` step (versioned/left-over objects) and retry.
- CI state bucket (`TF_STATE_BUCKET`) is intentionally **not** deleted.
