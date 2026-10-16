# Costs

## Free-tier note

Cognito offers up to **10k MAU free for Lite/Essential pools**, but **API GW/Lambda/DynamoDB/CloudFront/WAF/DNS/logging/SMS cost extra**.

## What costs what (directional, check current AWS pricing)

| Component | Pricing driver | Notes |
|---|---|---|
| Cognito User Pool | MAU | Lite/Essential free to 10k MAU; SMS/MFA messages billed separately |
| Cognito SMS/MFA | per message | Can dominate the bill — prefer email OTP / TOTP unless SMS required |
| API Gateway HTTP API | per million requests | Cheapest GW option; REST APIs + usage plans cost more |
| Lambda | requests + GB-s | Tiny auth handlers usually stay in free tier |
| DynamoDB | on-demand R/W + storage | PAY_PER_REQUEST in this starter; GSIs/storage extra |
| S3 + CloudFront | storage + requests + egress | SPA is small; invalidations ~free at this scale |
| WAF (`enable_waf`) | per ACL + per rule + per M req | ~$5/mo base + rules even idle — keep off for dev |
| Route53 + ACM | per zone + per query | Hosted zone ~$0.50/mo; cert itself free |
| CloudWatch Logs/Alarms | GB ingested + alarms | 14-day retention set here; verbose Lambda logging adds up |

## Keep dev cheap

- `enable_waf = false`, no custom domain, no SMS MFA.
- Use `PAY_PER_REQUEST` DynamoDB (default here) and short log retention.
- `terraform destroy` idle dev stacks — see [TEARDOWN.md](TEARDOWN.md).
- Set a billing alarm / AWS Budget on first deploy.
