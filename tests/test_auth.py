"""pytest: JWT claim shape, RBAC helpers, Lambda route behaviour (mocked DDB)."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

LAMBDA_DIR = Path(__file__).resolve().parents[1] / "backend" / "lambda"
sys.path.insert(0, str(LAMBDA_DIR))

import app  # noqa: E402
import authorizer_check as ac  # noqa: E402


def _event(route="GET /me", claims=None):
    return {
        "routeKey": route,
        "requestContext": {"authorizer": {"jwt": {"claims": claims or {}}}},
    }


def _claims(**kw):
    base = {
        "sub": "user-123",
        "iss": "https://cognito-idp.ap-south-1.amazonaws.com/ap-south-1_ABC",
        "aud": "client123",
        "token_use": "id",
        "exp": 9999999999,
        "email": "dev@example.com",
    }
    base.update(kw)
    return base


# --- JWT structure ---
def test_validate_claims_shape_ok():
    assert ac.validate_claims_shape(_claims()) == []


def test_validate_claims_shape_reports_missing():
    problems = ac.validate_claims_shape({"sub": "x"})
    assert any("iss" in p for p in problems)
    assert any("aud" in p for p in problems)


def test_validate_claims_bad_token_use():
    assert any("token_use" in p for p in ac.validate_claims_shape(_claims(token_use="refresh")))


# --- RBAC helpers ---
def test_get_groups_handles_list_str_and_missing():
    assert ac.get_groups({"cognito:groups": ["admins", "dev"]}) == ["admins", "dev"]
    assert ac.get_groups({"cognito:groups": "admins, dev"}) == ["admins", "dev"]
    assert ac.get_groups({}) == []


def test_is_in_group_and_require_groups():
    claims = _claims(**{"cognito:groups": ["admins"]})
    assert ac.is_in_group(claims, "admins") is True
    assert ac.is_in_group(claims, "other") is False
    ac.require_groups(claims, "admins")  # no raise
    try:
        ac.require_groups(_claims(), "admins")
    except PermissionError:
        pass
    else:
        raise AssertionError("expected PermissionError")


# --- Lambda routes ---
def _body(res):
    assert res["headers"]["Content-Type"] == "application/json"
    return json.loads(res["body"])


def test_health_ok():
    res = app.handler(_event("GET /health", {}), None)
    assert res["statusCode"] == 200
    assert _body(res)["ok"] is True


def test_me_unauthorized_without_claims():
    res = app.handler(_event("GET /me", {}), None)
    assert res["statusCode"] == 401


def test_me_returns_claims_with_mocked_dynamodb(monkeypatch):
    fake_table = MagicMock()
    fake_table.get_item.return_value = {"Item": {"pk": "user#user-123", "nick": "nav"}}
    monkeypatch.setattr(app, "_table", lambda: fake_table)
    res = app.handler(_event("GET /me", _claims()), None)
    assert res["statusCode"] == 200
    data = _body(res)
    assert data["sub"] == "user-123"
    assert data["profile"]["nick"] == "nav"


def test_admin_allows_group_member():
    res = app.handler(_event("GET /admin", _claims(**{"cognito:groups": ["admins"]})), None)
    assert res["statusCode"] == 200


def test_admin_denies_non_member():
    res = app.handler(_event("GET /admin", _claims()), None)
    assert res["statusCode"] == 403


def test_unknown_route_404():
    res = app.handler(_event("GET /nope", _claims()), None)
    assert res["statusCode"] == 404
