"""JWT claim + RBAC helpers. API Gateway JWT authorizer already validates
signature/iss/exp; these helpers enforce app-level group checks in Lambda."""
from __future__ import annotations

from typing import Any, Mapping


def get_claims(event: Mapping[str, Any]) -> dict:
    """Extract JWT claims from an API GW HTTP API (v2 payload) event."""
    try:
        return dict(
            event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
        )
    except AttributeError:
        return {}


def get_groups(claims: Mapping[str, Any]) -> list[str]:
    """Return cognito:groups as a list (handles str, list, or missing)."""
    raw = claims.get("cognito:groups", [])
    if isinstance(raw, str):
        return [g.strip() for g in raw.split(",") if g.strip()]
    if isinstance(raw, (list, tuple)):
        return [str(g) for g in raw]
    return []


def is_in_group(claims: Mapping[str, Any], group: str) -> bool:
    return group in get_groups(claims)


def require_groups(claims: Mapping[str, Any], *groups: str) -> None:
    """Raise PermissionError unless caller is in at least one group."""
    if not groups:
        raise ValueError("require_groups needs at least one group")
    if not any(is_in_group(claims, g) for g in groups):
        raise PermissionError(f"Forbidden: requires group {groups!r}")


def validate_claims_shape(claims: Mapping[str, Any]) -> list[str]:
    """Return list of problems with required JWT claim shape (empty = OK)."""
    problems: list[str] = []
    for field in ("sub", "iss", "aud", "token_use", "exp"):
        if field not in claims:
            problems.append(f"missing claim: {field}")
    if claims.get("token_use") not in (None, "id", "access"):
        problems.append("token_use must be 'id' or 'access'")
    return problems
