"""Lambda handler for HTTP API routes: /health, /me, /admin.

API Gateway JWT authorizer guarantees a valid token; /admin additionally
requires membership in the `admins` Cognito group (see authorizer_check).
/me demonstrates a DynamoDB-backed profile lookup (table from TABLE_NAME).
"""
from __future__ import annotations

import json
import os

import boto3

from authorizer_check import get_claims, get_groups, require_groups

ADMIN_GROUP = os.environ.get("ADMIN_GROUP", "admins")
TABLE_NAME = os.environ.get("TABLE_NAME", "")

_ddb = None


def _table():
    global _ddb
    if TABLE_NAME == "":
        return None
    if _ddb is None:
        _ddb = boto3.resource("dynamodb").Table(TABLE_NAME)
    return _ddb


def _resp(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event, context):  # noqa: ANN001, ANN202 — Lambda entrypoint
    route = event.get("routeKey") or f"{event.get('httpMethod', 'GET')} {event.get('path', '/')}"
    method, _, path = route.partition(" ")

    if path == "/health" or route == "$default":
        if path not in ("/health", "/", "$default"):
            return _resp(404, {"error": "not found", "route": route})
        return _resp(200, {"ok": True, "service": "secure-auth-platform"})

    claims = get_claims(event)
    if not claims or "sub" not in claims:
        return _resp(401, {"error": "unauthorized: missing JWT claims"})

    if path == "/me":
        profile: dict = {}
        table = _table()
        if table is not None:
            try:
                item = table.get_item(Key={"pk": f"user#{claims['sub']}"}).get("Item", {})
                profile = item
            except Exception as exc:  # surface as 502, don't leak internals
                return _resp(502, {"error": f"profile lookup failed: {type(exc).__name__}"})
        return _resp(200, {
            "sub": claims.get("sub"),
            "email": claims.get("email"),
            "username": claims.get("username") or claims.get("cognito:username"),
            "groups": get_groups(claims),
            "profile": profile,
        })

    if path == "/admin":
        try:
            require_groups(claims, ADMIN_GROUP)
        except PermissionError as exc:
            return _resp(403, {"error": str(exc)})
        return _resp(200, {
            "message": f"hello admin {claims.get('email') or claims.get('sub')}",
            "group": ADMIN_GROUP,
        })

    return _resp(404, {"error": "not found", "route": route})
