# aws-cognito-secure-auth-platform

[![Terraform](https://img.shields.io/badge/IaC-Terraform%20%2F%20OpenTofu-blue)](infra/terraform) [![AWS](https://img.shields.io/badge/AWS-Cognito%20%7C%20API%20GW%20%7C%20Lambda-orange)](infra/terraform) [![CI](https://img.shields.io/badge/CI-GitHub%20Actions%20OIDC-green)](.github/workflows/deploy.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Production-quality starter for a secure serverless auth platform: **S3 + CloudFront** web app, **Cognito User Pool** (email/password, verification, password reset, optional Google IdP), **API Gateway HTTP API with JWT authorizer**, **Lambda (Python 3.12) + DynamoDB** protected APIs with RBAC group checks.

## Architecture

```text
                    ┌────────────────────┐
                    │  Route53 (optional) │
                    │  + ACM + WAF (opt)  │
                    └─────────┬──────────┘
                              │ HTTPS
                    ┌─────────▼──────────┐
                    │    CloudFront      │◄── OAC ── S3 (web/ static)
                    │  (SPA + WAF ACL)   │
                    └────────────────────┘
                              │
                    ┌─────────▼──────────┐     ┌──────────────────┐
                    │  Cognito Hosted UI │────►│   User Pool      │
                    │ /oauth2/authorize  │     │ email verify,    │
                    │ PKCE code flow     │◄────│ reset, Google IdP│
                    └─────────┬──────────┘     │ Groups: admins   │
                              │ ID/JWT         └──────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │ API Gateway HTTP   │
                    │ JWT authorizer     │── validates iss/aud/exp
                    └─────────┬──────────┘
                              │ requestContext.authorizer.jwt.claims
                    ┌─────────▼──────────┐     ┌──────────────────┐
                    │ Lambda Python 3.12 │────►│    DynamoDB      │
                    │ /me /admin + RBAC  │     │  profiles table  │
                    └─────────┬──────────┘     └──────────────────┘
                              │ logs / metrics
                    ┌─────────▼──────────┐
                    │ CloudWatch Logs +  │
                    │ Alarms (5xx, errs) │
                    └────────────────────┘
```

## Features

- Email/password sign-up with verification code, sign-in via Hosted UI (PKCE, no client secret), sign-out, password reset.
- Optional Google IdP (`var.google_client_id/secret` — empty = disabled).
- JWT authorizer on API Gateway; Lambda re-checks `cognito:groups` for `/admin` RBAC.
- Least-privilege IAM for Lambda (DynamoDB scoped to one table + CloudWatch Logs only).
- Private S3 + CloudFront OAC, optional WAF (`var.enable_waf`) and custom domain (`var.domain_name` + `var.hosted_zone_id`).
- CloudWatch log groups + alarms for Lambda errors and API 5xx.
- OIDC CI: no long-lived AWS keys. `pytest` + `terraform plan/apply` + S3 sync + CloudFront invalidation.
- One-command teardown (Terraform destroy + empty S3 bucket).

## Free-tier note

Cognito offers up to **10k MAU free for Lite/Essential pools**, but **API GW/Lambda/DynamoDB/CloudFront/WAF/DNS/logging/SMS cost extra**. See [docs/COSTS.md](docs/COSTS.md). SMS/MFA and WAF/Route53/ACM usage can dominate a "free" bill — keep them off unless needed.

## Quickstart

```bash
# 1. Configure
cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars 2>/dev/null || true
# edit infra/terraform/terraform.tfvars: project_name, region, cognito_domain_prefix (globally unique)

# 2. Deploy everything
./scripts/deploy.sh dev ap-south-1

# 3. Wire the web app
# Copy outputs into web/config.js (deploy.sh prints them):
#   terraform output -raw api_endpoint, cognito_domain, user_pool_client_id
cp web/config.example.js web/config.js  # then edit values
# Or serve locally with injected config (see web/app.js WINDOW.APP_CONFIG).

# 4. Test
python -m pytest tests/ -v
curl -i "$API_ENDPOINT/health"
curl -i -H "Authorization: Bearer $ID_TOKEN" "$API_ENDPOINT/me"
```

Get an `ID_TOKEN` by opening the CloudFront URL, clicking Sign in (Hosted UI), then the app stores tokens in `sessionStorage` and shows them on the page.

## Deploy

CI (recommended): set repo Variables/Secrets `AWS_ROLE_TO_ASSUME`, `AWS_REGION`, `TF_STATE_BUCKET`, `TF_STATE_LOCK_TABLE` (or update workflow backend), then push to `main`. See [.github/workflows/deploy.yml](.github/workflows/deploy.yml).

Manual:

```bash
cd infra/terraform
terraform init
terraform plan -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
aws s3 sync ../../web s3://$(terraform output -raw web_bucket) --delete --exclude "config.example.js"
aws cloudfront create-invalidation --distribution-id $(terraform output -raw cloudfront_distribution_id) --paths "/*"
```

`scripts/deploy.sh [env] [region]` wraps init/plan/apply + web sync + invalidation.

## Test

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/lambda/requirements.txt -r tests/requirements.txt 2>/dev/null || pip install pytest boto3
python -m pytest tests/ -v
```

Tests cover JWT claim shape, `cognito:groups` RBAC helper, and Lambda route behaviour with mocked DynamoDB (no AWS needed).

## Teardown

```bash
./scripts/teardown.sh dev ap-south-1
```

Destroys Terraform, empties the web S3 bucket first (required), and verifies no leftover WAF/ACM/DynamoDB resources. Full checklist: [docs/TEARDOWN.md](docs/TEARDOWN.md).

## Custom domain + WAF

```hcl
# infra/terraform/terraform.tfvars
domain_name    = "app.example.com"
hosted_zone_id = "Z0123456789ABCDEF"
enable_waf     = true
```

1. Request ACM cert (CloudFront requires `us-east-1`): the module creates/validates it via Route53 when `domain_name` is set.
2. `terraform apply` creates `A`/`AAAA` alias records to CloudFront and attaches the WAF ACL (rate-limit + AWS managed rules) to both CloudFront and the HTTP API.
3. Point Cognito callback/logout URLs at `https://app.example.com/` (output `hosted_ui_url` updates automatically).

Turn WAF on without a domain: `enable_waf = true` alone still protects CloudFront + API GW (uses default CloudFront cert).

## Repo layout

```text
web/                  SPA (Hosted UI PKCE + JWT fetch)
backend/lambda/       Python 3.12: app.py (/me, /admin, /health), authorizer_check.py (RBAC), requirements.txt
infra/terraform/      OpenTofu-compatible HCL (Cognito, API GW+JWT, Lambda, DDB, S3+CloudFront OAC, WAF, Route53, alarms)
tests/                pytest: JWT structure, RBAC, Lambda routes (mocked)
scripts/              deploy.sh, teardown.sh
docs/                 COSTS.md, TEARDOWN.md
.github/workflows/   OIDC deploy pipeline
```
