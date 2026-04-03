"""Built-in test runner: API smoke-tests, CRUD checks, and i18n validation.

Runs via Flask test_client() — no external HTTP, no network dependency.
Endpoint: /api/tests/*
"""

from __future__ import annotations

import json
import os
import time
import traceback
import uuid
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required

bp_tests = Blueprint("tests_runner", __name__, url_prefix="/api/tests")

# ---------------------------------------------------------------------------
# Test registry
# ---------------------------------------------------------------------------
_registry: List[Dict[str, Any]] = []


def register_test(category: str, name: str):
    """Decorator that registers a test function."""
    def decorator(fn: Callable):
        _registry.append({"category": category, "name": name, "fn": fn})
        @wraps(fn)
        def wrapper(*a, **kw):
            return fn(*a, **kw)
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_TEST_EMAIL = f"__autotest_{uuid.uuid4().hex[:8]}@growboard.test"
_TEST_PASS = "AutoTest_Pwd_99!"


def _get_app():
    return current_app._get_current_object()


def _make_client():
    app = _get_app()
    return app.test_client()


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _ensure_test_user(client) -> str:
    """Register (or login) test user and return JWT token."""
    r = client.post("/login", json={"username": _TEST_EMAIL, "password": _TEST_PASS})
    if r.status_code == 200:
        return r.get_json().get("access_token", "")
    client.post("/register", json={"username": _TEST_EMAIL, "password": _TEST_PASS})
    r = client.post("/login", json={"username": _TEST_EMAIL, "password": _TEST_PASS})
    if r.status_code == 200:
        return r.get_json().get("access_token", "")
    return ""


def _assert(condition: bool, detail: str = ""):
    if not condition:
        raise AssertionError(detail or "Assertion failed")


# ---------------------------------------------------------------------------
# Run engine
# ---------------------------------------------------------------------------
def _run_tests(category_filter: Optional[str] = None) -> List[dict]:
    results = []
    client = _make_client()
    token = _ensure_test_user(client)
    ctx = {"client": client, "token": token, "created_ids": {}}

    tests = _registry
    if category_filter:
        tests = [t for t in tests if t["category"] == category_filter]

    for entry in tests:
        t0 = time.time()
        try:
            entry["fn"](ctx)
            results.append({
                "passed": True,
                "name": entry["name"],
                "category": entry["category"],
                "detail": "",
                "duration_ms": round((time.time() - t0) * 1000),
            })
        except Exception as exc:
            results.append({
                "passed": False,
                "name": entry["name"],
                "category": entry["category"],
                "detail": str(exc),
                "duration_ms": round((time.time() - t0) * 1000),
                "traceback": traceback.format_exc(limit=4),
            })
    return results


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
@bp_tests.route("/list", methods=["GET"])
@jwt_required()
def list_tests():
    grouped: Dict[str, list] = {}
    for entry in _registry:
        grouped.setdefault(entry["category"], []).append(entry["name"])
    return jsonify({"categories": grouped, "total": len(_registry)}), 200


@bp_tests.route("/run", methods=["POST"])
@jwt_required()
def run_all():
    category = (request.get_json(silent=True) or {}).get("category")
    results = _run_tests(category)
    passed = sum(1 for r in results if r["passed"])
    return jsonify({
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }), 200


@bp_tests.route("/run/<category>", methods=["POST"])
@jwt_required()
def run_category(category):
    results = _run_tests(category)
    passed = sum(1 for r in results if r["passed"])
    return jsonify({
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }), 200


# ===================================================================
#  TEST DEFINITIONS
# ===================================================================

# -------------------------------------------------------------------
# 1. AUTH
# -------------------------------------------------------------------
@register_test("auth", "API root responds 200")
def test_api_root(ctx):
    r = ctx["client"].get("/api")
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("auth", "Login with valid credentials")
def test_login_valid(ctx):
    r = ctx["client"].post("/login", json={"username": _TEST_EMAIL, "password": _TEST_PASS})
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")
    _assert("access_token" in r.get_json(), "No access_token in response")

@register_test("auth", "Login with wrong password returns 401")
def test_login_wrong_password(ctx):
    r = ctx["client"].post("/login", json={"username": _TEST_EMAIL, "password": "wrong"})
    _assert(r.status_code == 401, f"Expected 401, got {r.status_code}")

@register_test("auth", "Protected endpoint rejects no token")
def test_no_token(ctx):
    r = ctx["client"].get("/user_teams")
    _assert(r.status_code in (401, 422), f"Expected 401/422, got {r.status_code}")

@register_test("auth", "Protected endpoint accepts valid token")
def test_valid_token(ctx):
    r = ctx["client"].get("/user_teams", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("auth", "Register duplicate user returns 4xx")
def test_register_duplicate(ctx):
    r = ctx["client"].post("/register", json={"username": _TEST_EMAIL, "password": _TEST_PASS})
    _assert(r.status_code >= 400, f"Expected 4xx, got {r.status_code}")


# -------------------------------------------------------------------
# 2. SURVEY
# -------------------------------------------------------------------
@register_test("survey", "GET /questions returns list")
def test_questions(ctx):
    r = ctx["client"].get("/questions", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("survey", "GET /user_teams returns list")
def test_user_teams(ctx):
    r = ctx["client"].get("/user_teams", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")
    data = r.get_json()
    _assert(isinstance(data, (list, dict)), "Response is not list/dict")

@register_test("survey", "POST /create_team creates a team")
def test_create_team(ctx):
    name = f"autotest_{uuid.uuid4().hex[:6]}"
    r = ctx["client"].post("/create_team", json={"team_name": name}, headers=_auth_header(ctx["token"]))
    _assert(r.status_code in (200, 201), f"Expected 200/201, got {r.status_code}")
    data = r.get_json()
    tid = data.get("team_id") or data.get("id")
    if tid:
        ctx["created_ids"]["team_id"] = tid

@register_test("survey", "GET /team_progress/<id> works")
def test_team_progress(ctx):
    tid = ctx["created_ids"].get("team_id")
    if not tid:
        return
    r = ctx["client"].get(f"/team_progress/{tid}", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("survey", "POST /temp_results and GET /temp_results roundtrip")
def test_temp_results(ctx):
    payload = {"results": [{"category": "test", "score": 3}]}
    r = ctx["client"].post("/temp_results", json=payload, headers=_auth_header(ctx["token"]))
    _assert(r.status_code in (200, 201), f"POST expected 200/201, got {r.status_code}")
    r2 = ctx["client"].get("/temp_results", headers=_auth_header(ctx["token"]))
    _assert(r2.status_code == 200, f"GET expected 200, got {r2.status_code}")

@register_test("survey", "DELETE team cleans up")
def test_delete_team(ctx):
    tid = ctx["created_ids"].get("team_id")
    if not tid:
        return
    r = ctx["client"].delete(f"/dashboard/delete_team/{tid}", headers=_auth_header(ctx["token"]))
    _assert(r.status_code in (200, 204, 404), f"Expected 200/204, got {r.status_code}")


# -------------------------------------------------------------------
# 3. PROFILE
# -------------------------------------------------------------------
@register_test("profile", "GET /api/user_profile returns profile")
def test_get_profile(ctx):
    r = ctx["client"].get("/api/user_profile", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("profile", "POST /api/update_profile updates name")
def test_update_profile(ctx):
    r = ctx["client"].post("/api/update_profile",
                           json={"name": "AutoTest User", "position": "QA", "company": "Test"},
                           headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("profile", "Profile reflects updated data")
def test_profile_data(ctx):
    r = ctx["client"].get("/api/user_profile", headers=_auth_header(ctx["token"]))
    data = r.get_json()
    _assert(data.get("name") == "AutoTest User", f"Name mismatch: {data.get('name')}")


# -------------------------------------------------------------------
# 4. CONFLICTS
# -------------------------------------------------------------------
@register_test("conflicts", "GET /api/conflicts returns list")
def test_list_conflicts(ctx):
    r = ctx["client"].get("/api/conflicts", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("conflicts", "POST /api/conflicts creates conflict")
def test_create_conflict(ctx):
    r = ctx["client"].post("/api/conflicts",
                           json={"context": "autotest", "participants": "A,B", "attempts": "none", "goal": "test"},
                           headers=_auth_header(ctx["token"]))
    _assert(r.status_code in (200, 201), f"Expected 200/201, got {r.status_code}")
    data = r.get_json()
    cid = data.get("id") or data.get("conflict", {}).get("id")
    if cid:
        ctx["created_ids"]["conflict_id"] = cid

@register_test("conflicts", "DELETE /api/conflict/<id> removes conflict")
def test_delete_conflict(ctx):
    cid = ctx["created_ids"].get("conflict_id")
    if not cid:
        return
    r = ctx["client"].delete(f"/api/conflict/{cid}", headers=_auth_header(ctx["token"]))
    _assert(r.status_code in (200, 204), f"Expected 200/204, got {r.status_code}")


# -------------------------------------------------------------------
# 5. MOTIVATION / EMPLOYEES
# -------------------------------------------------------------------
@register_test("motivation", "GET /employees returns list")
def test_list_employees(ctx):
    r = ctx["client"].get("/employees", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("motivation", "POST /employees creates employee")
def test_create_employee(ctx):
    r = ctx["client"].post("/employees",
                           json={"name": "Test Employee", "role": "Dev"},
                           headers=_auth_header(ctx["token"]))
    _assert(r.status_code in (200, 201), f"Expected 200/201, got {r.status_code}")
    data = r.get_json()
    eid = data.get("id") or data.get("employee", {}).get("id")
    if eid:
        ctx["created_ids"]["employee_id"] = eid

@register_test("motivation", "GET /employee/<id> returns employee")
def test_get_employee(ctx):
    eid = ctx["created_ids"].get("employee_id")
    if not eid:
        return
    r = ctx["client"].get(f"/employee/{eid}", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("motivation", "DELETE /employee/<id> removes employee")
def test_delete_employee(ctx):
    eid = ctx["created_ids"].get("employee_id")
    if not eid:
        return
    r = ctx["client"].delete(f"/employee/{eid}", headers=_auth_header(ctx["token"]))
    _assert(r.status_code in (200, 204), f"Expected 200/204, got {r.status_code}")


# -------------------------------------------------------------------
# 6. DISC
# -------------------------------------------------------------------
@register_test("disc", "GET /api/disc/questions returns questions")
def test_disc_questions(ctx):
    r = ctx["client"].get("/api/disc/questions", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("disc", "GET /api/disc/history returns list")
def test_disc_history(ctx):
    r = ctx["client"].get("/api/disc/history", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("disc", "GET /api/disc/latest returns result or 404")
def test_disc_latest(ctx):
    r = ctx["client"].get("/api/disc/latest", headers=_auth_header(ctx["token"]))
    _assert(r.status_code in (200, 404), f"Expected 200/404, got {r.status_code}")


# -------------------------------------------------------------------
# 7. MEETING DESIGN
# -------------------------------------------------------------------
@register_test("meeting_design", "GET /api/meeting-design returns list")
def test_list_meeting_designs(ctx):
    r = ctx["client"].get("/api/meeting-design", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("meeting_design", "GET /api/teams returns teams")
def test_get_teams(ctx):
    r = ctx["client"].get("/api/teams", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")


# -------------------------------------------------------------------
# 8. SURVEYS MODULE
# -------------------------------------------------------------------
@register_test("surveys_module", "GET /api/surveys returns list")
def test_list_surveys(ctx):
    r = ctx["client"].get("/api/surveys", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("surveys_module", "GET /api/survey-templates returns list")
def test_list_survey_templates(ctx):
    r = ctx["client"].get("/api/survey-templates", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("surveys_module", "GET /api/employees returns list")
def test_surveys_employees(ctx):
    r = ctx["client"].get("/api/employees", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")


# -------------------------------------------------------------------
# 9. MATURITY LINK
# -------------------------------------------------------------------
@register_test("maturity_link", "POST /api/maturity-link creates session")
def test_create_maturity_session(ctx):
    r = ctx["client"].post("/api/maturity-link",
                           json={"team_name": "autotest_team"},
                           headers=_auth_header(ctx["token"]))
    _assert(r.status_code in (200, 201), f"Expected 200/201, got {r.status_code}")
    data = r.get_json()
    token = data.get("access_token") or data.get("token")
    if token:
        ctx["created_ids"]["maturity_token"] = token

@register_test("maturity_link", "GET /api/maturity/<token> returns session")
def test_get_maturity_session(ctx):
    tok = ctx["created_ids"].get("maturity_token")
    if not tok:
        return
    r = ctx["client"].get(f"/api/maturity/{tok}")
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("maturity_link", "GET /api/maturity-admin/overview returns data")
def test_maturity_admin_overview(ctx):
    r = ctx["client"].get("/api/maturity-admin/overview", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")


# -------------------------------------------------------------------
# 10. BACKLOG PREP
# -------------------------------------------------------------------
@register_test("backlog_prep", "GET /api/backlog/items returns list")
def test_list_backlog_items(ctx):
    r = ctx["client"].get("/api/backlog/items", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("backlog_prep", "POST /api/backlog/items creates epic")
def test_create_backlog_item(ctx):
    r = ctx["client"].post("/api/backlog/items",
                           json={"item_type": "epic", "title": "Autotest Epic", "description": "test"},
                           headers=_auth_header(ctx["token"]))
    _assert(r.status_code in (200, 201), f"Expected 200/201, got {r.status_code}")
    data = r.get_json()
    iid = data.get("id") or data.get("item", {}).get("id")
    if iid:
        ctx["created_ids"]["backlog_item_id"] = iid

@register_test("backlog_prep", "GET /api/backlog/items/<id> returns item")
def test_get_backlog_item(ctx):
    iid = ctx["created_ids"].get("backlog_item_id")
    if not iid:
        return
    r = ctx["client"].get(f"/api/backlog/items/{iid}", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("backlog_prep", "DELETE /api/backlog/items/<id> removes item")
def test_delete_backlog_item(ctx):
    iid = ctx["created_ids"].get("backlog_item_id")
    if not iid:
        return
    r = ctx["client"].delete(f"/api/backlog/items/{iid}", headers=_auth_header(ctx["token"]))
    _assert(r.status_code in (200, 204), f"Expected 200/204, got {r.status_code}")


# -------------------------------------------------------------------
# 11. ROADMAP
# -------------------------------------------------------------------
@register_test("roadmap", "GET /api/roadmap returns list")
def test_list_roadmaps(ctx):
    r = ctx["client"].get("/api/roadmap", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("roadmap", "POST /api/roadmap creates roadmap")
def test_create_roadmap(ctx):
    r = ctx["client"].post("/api/roadmap",
                           json={"name": "Autotest Roadmap"},
                           headers=_auth_header(ctx["token"]))
    _assert(r.status_code in (200, 201), f"Expected 200/201, got {r.status_code}")
    data = r.get_json()
    rid = data.get("id") or data.get("roadmap", {}).get("id")
    if rid:
        ctx["created_ids"]["roadmap_id"] = rid

@register_test("roadmap", "GET /api/roadmap/<id> returns roadmap")
def test_get_roadmap(ctx):
    rid = ctx["created_ids"].get("roadmap_id")
    if not rid:
        return
    r = ctx["client"].get(f"/api/roadmap/{rid}", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("roadmap", "DELETE /api/roadmap/<id> removes roadmap")
def test_delete_roadmap(ctx):
    rid = ctx["created_ids"].get("roadmap_id")
    if not rid:
        return
    r = ctx["client"].delete(f"/api/roadmap/{rid}", headers=_auth_header(ctx["token"]))
    _assert(r.status_code in (200, 204), f"Expected 200/204, got {r.status_code}")


# -------------------------------------------------------------------
# 12. CHAT
# -------------------------------------------------------------------
@register_test("chat", "GET /api/chat/contacts returns list")
def test_chat_contacts(ctx):
    r = ctx["client"].get("/api/chat/contacts", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("chat", "POST /api/chat/resolve with invalid email returns 400")
def test_chat_resolve_bad(ctx):
    r = ctx["client"].post("/api/chat/resolve",
                           json={"email": "not-an-email"},
                           headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 400, f"Expected 400, got {r.status_code}")

@register_test("chat", "POST /api/chat/resolve self returns 400")
def test_chat_resolve_self(ctx):
    r = ctx["client"].post("/api/chat/resolve",
                           json={"email": _TEST_EMAIL},
                           headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 400, f"Expected 400, got {r.status_code}")

@register_test("chat", "POST /api/chat/send without body returns 400")
def test_chat_send_empty(ctx):
    r = ctx["client"].post("/api/chat/send",
                           json={"recipient_id": 999999, "body": ""},
                           headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 400, f"Expected 400, got {r.status_code}")

@register_test("chat", "POST /api/chat/presence returns presence map")
def test_chat_presence(ctx):
    r = ctx["client"].post("/api/chat/presence",
                           json={"ids": [1]},
                           headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")
    _assert("presence" in r.get_json(), "No presence key")


# -------------------------------------------------------------------
# 13. SYSTEM THINKING
# -------------------------------------------------------------------
@register_test("system_thinking", "GET /api/system-thinking returns list")
def test_list_icebergs(ctx):
    r = ctx["client"].get("/api/system-thinking", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("system_thinking", "POST /api/system-thinking creates iceberg")
def test_create_iceberg(ctx):
    r = ctx["client"].post("/api/system-thinking",
                           json={"event": "autotest event"},
                           headers=_auth_header(ctx["token"]))
    _assert(r.status_code in (200, 201), f"Expected 200/201, got {r.status_code}")
    data = r.get_json()
    iid = data.get("id") or data.get("iceberg", {}).get("id")
    if iid:
        ctx["created_ids"]["iceberg_id"] = iid

@register_test("system_thinking", "GET /api/system-thinking/<id> returns iceberg")
def test_get_iceberg(ctx):
    iid = ctx["created_ids"].get("iceberg_id")
    if not iid:
        return
    r = ctx["client"].get(f"/api/system-thinking/{iid}", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("system_thinking", "DELETE /api/system-thinking/<id> removes iceberg")
def test_delete_iceberg(ctx):
    iid = ctx["created_ids"].get("iceberg_id")
    if not iid:
        return
    r = ctx["client"].delete(f"/api/system-thinking/{iid}", headers=_auth_header(ctx["token"]))
    _assert(r.status_code in (200, 204), f"Expected 200/204, got {r.status_code}")


# -------------------------------------------------------------------
# 14. AGILE KATA
# -------------------------------------------------------------------
@register_test("agile_kata", "GET /api/agile-kata returns list")
def test_list_kata(ctx):
    r = ctx["client"].get("/api/agile-kata", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("agile_kata", "POST /api/agile-kata creates canvas")
def test_create_kata(ctx):
    r = ctx["client"].post("/api/agile-kata",
                           json={"title": "Autotest Kata", "canvas_state": {"challenge": "test"}},
                           headers=_auth_header(ctx["token"]))
    _assert(r.status_code in (200, 201), f"Expected 200/201, got {r.status_code}")
    data = r.get_json()
    kid = data.get("id") or data.get("canvas", {}).get("id")
    if kid:
        ctx["created_ids"]["kata_id"] = kid

@register_test("agile_kata", "GET /api/agile-kata/<id> returns canvas")
def test_get_kata(ctx):
    kid = ctx["created_ids"].get("kata_id")
    if not kid:
        return
    r = ctx["client"].get(f"/api/agile-kata/{kid}", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("agile_kata", "DELETE /api/agile-kata/<id> removes canvas")
def test_delete_kata(ctx):
    kid = ctx["created_ids"].get("kata_id")
    if not kid:
        return
    r = ctx["client"].delete(f"/api/agile-kata/{kid}", headers=_auth_header(ctx["token"]))
    _assert(r.status_code in (200, 204), f"Expected 200/204, got {r.status_code}")


# -------------------------------------------------------------------
# 15. QA
# -------------------------------------------------------------------
@register_test("qa", "GET /api/qa-user-story/submissions returns list")
def test_qa_us_submissions(ctx):
    r = ctx["client"].get("/api/qa-user-story/submissions", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("qa", "GET /api/testing-types/list returns types")
def test_testing_types_list(ctx):
    r = ctx["client"].get("/api/testing-types/list", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("qa", "GET /api/ai-usage returns usage data")
def test_ai_usage(ctx):
    r = ctx["client"].get("/api/ai-usage", headers=_auth_header(ctx["token"]))
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")


# -------------------------------------------------------------------
# 16. i18n COMPLETENESS
# -------------------------------------------------------------------
def _load_i18n_file(lang: str) -> dict:
    base = os.path.join(os.path.dirname(__file__), "vue-frontend", "src", "i18n", "locales")
    path = os.path.join(base, f"{lang}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _collect_keys(d: dict, prefix: str = "") -> set:
    keys = set()
    for k, v in d.items():
        full = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(_collect_keys(v, full))
        else:
            keys.add(full)
    return keys


@register_test("i18n", "All top-level i18n sections exist in both RU and EN")
def test_i18n_top_level(ctx):
    ru = _load_i18n_file("ru")
    en = _load_i18n_file("en")
    ru_top = set(ru.keys())
    en_top = set(en.keys())
    only_ru = ru_top - en_top
    only_en = en_top - ru_top
    _assert(not only_ru and not only_en,
            f"Missing in EN: {only_ru or 'none'} | Missing in RU: {only_en or 'none'}")


@register_test("i18n", "All nested i18n keys match between RU and EN")
def test_i18n_nested_keys(ctx):
    ru = _load_i18n_file("ru")
    en = _load_i18n_file("en")
    ru_keys = _collect_keys(ru)
    en_keys = _collect_keys(en)
    only_ru = ru_keys - en_keys
    only_en = en_keys - ru_keys
    detail_parts = []
    if only_ru:
        detail_parts.append(f"Missing in EN ({len(only_ru)}): {', '.join(sorted(only_ru)[:20])}")
    if only_en:
        detail_parts.append(f"Missing in RU ({len(only_en)}): {', '.join(sorted(only_en)[:20])}")
    _assert(not only_ru and not only_en, " | ".join(detail_parts) or "Key mismatch")


@register_test("i18n", "No empty translation values in RU")
def test_i18n_no_empty_ru(ctx):
    ru = _load_i18n_file("ru")
    ru_keys = _collect_keys(ru)
    empty = []
    def _check(d, prefix=""):
        for k, v in d.items():
            full = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                _check(v, full)
            elif isinstance(v, str) and v.strip() == "":
                empty.append(full)
    _check(ru)
    _assert(not empty, f"Empty values in RU: {', '.join(empty[:20])}")


@register_test("i18n", "No empty translation values in EN")
def test_i18n_no_empty_en(ctx):
    en = _load_i18n_file("en")
    empty = []
    def _check(d, prefix=""):
        for k, v in d.items():
            full = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                _check(v, full)
            elif isinstance(v, str) and v.strip() == "":
                empty.append(full)
    _check(en)
    _assert(not empty, f"Empty values in EN: {', '.join(empty[:20])}")


@register_test("i18n", "RU translations are not identical to EN (spot check nav)")
def test_i18n_ru_differs_from_en(ctx):
    ru = _load_i18n_file("ru")
    en = _load_i18n_file("en")
    ru_nav = ru.get("nav", {})
    en_nav = en.get("nav", {})
    identical = [k for k in ru_nav if k in en_nav and ru_nav[k] == en_nav[k]]
    ratio = len(identical) / max(len(ru_nav), 1)
    _assert(ratio < 0.5, f"{len(identical)}/{len(ru_nav)} nav keys identical — translations may be missing")


# -------------------------------------------------------------------
# 17. i18n API (endpoint locale behavior)
# -------------------------------------------------------------------
@register_test("i18n_api", "GET /questions returns data (basic reachability)")
def test_i18n_api_questions(ctx):
    r = ctx["client"].get("/questions", headers={**_auth_header(ctx["token"]), "Accept-Language": "ru"})
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("i18n_api", "GET /api/disc/questions returns data")
def test_i18n_api_disc(ctx):
    r = ctx["client"].get("/api/disc/questions", headers={**_auth_header(ctx["token"]), "Accept-Language": "en"})
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("i18n_api", "GET /api/system-thinking/level-guide returns data")
def test_i18n_api_level_guide(ctx):
    r = ctx["client"].get("/api/system-thinking/level-guide", headers={**_auth_header(ctx["token"]), "Accept-Language": "ru"})
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("i18n_api", "GET /api/testing-types/list returns data")
def test_i18n_api_testing_types(ctx):
    r = ctx["client"].get("/api/testing-types/list", headers={**_auth_header(ctx["token"]), "Accept-Language": "en"})
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")

@register_test("i18n_api", "GET /api/agile-kata/example returns data")
def test_i18n_api_kata_example(ctx):
    r = ctx["client"].get("/api/agile-kata/example", headers={**_auth_header(ctx["token"]), "Accept-Language": "ru"})
    _assert(r.status_code == 200, f"Expected 200, got {r.status_code}")
