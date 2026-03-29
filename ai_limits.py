from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

from flask import Blueprint, has_request_context, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request

from database import db
from models import AiUsageCounter

AI_LIMIT_PER_PERIOD = 50
AI_LIMIT_ERROR = (
    f"Достигнут лимит AI-запросов ({AI_LIMIT_PER_PERIOD} за месяц). "
    "Обратитесь к администратору или дождитесь нового периода."
)

bp_ai_limits = Blueprint("ai_limits", __name__)


class AiLimitExceeded(Exception):
    def __init__(self, message: str = AI_LIMIT_ERROR):
        super().__init__(message)
        self.message = message


def _month_start_utc() -> datetime:
    now = datetime.utcnow()
    return datetime(now.year, now.month, 1)


def _extract_survey_token() -> Optional[str]:
    token = request.headers.get("X-Survey-Token")
    if token:
        return token.strip()[:120]

    args_token = request.args.get("survey_token") or request.args.get("access_token") or request.args.get("token")
    if args_token:
        return str(args_token).strip()[:120]

    data = request.get_json(silent=True) if has_request_context() else None
    if isinstance(data, dict):
        payload_token = data.get("survey_token") or data.get("access_token") or data.get("token")
        if payload_token:
            return str(payload_token).strip()[:120]

    path_parts = [p for p in (request.path or "").split("/") if p]
    if len(path_parts) >= 3 and path_parts[0] == "api" and path_parts[1] == "maturity":
        return path_parts[2][:120]
    return None


def resolve_scope_key() -> str:
    if has_request_context():
        try:
            verify_jwt_in_request(optional=True)
            uid = get_jwt_identity()
            if uid:
                return f"user:{uid}"
        except Exception:
            pass

        survey_token = _extract_survey_token()
        if survey_token:
            return f"survey:{survey_token}"

        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.remote_addr or "unknown"
        return f"ip:{ip[:120]}"
    return "system:no-request-context"


def _get_counter(scope_key: str, period_start: datetime) -> AiUsageCounter:
    counter = (
        AiUsageCounter.query.filter_by(scope_key=scope_key, period_start=period_start)
        .with_for_update()
        .first()
    )
    if not counter:
        counter = AiUsageCounter(scope_key=scope_key, period_start=period_start, count=0)
        db.session.add(counter)
        db.session.flush()
    return counter


def check_and_consume_ai_quota() -> Tuple[str, int]:
    period_start = _month_start_utc()
    scope_key = resolve_scope_key()
    counter = _get_counter(scope_key, period_start)
    if counter.count >= AI_LIMIT_PER_PERIOD:
        raise AiLimitExceeded()
    counter.count += 1
    db.session.commit()
    return scope_key, AI_LIMIT_PER_PERIOD - counter.count


def get_quota_status() -> dict:
    period_start = _month_start_utc()
    scope_key = resolve_scope_key()
    counter = AiUsageCounter.query.filter_by(scope_key=scope_key, period_start=period_start).first()
    used = counter.count if counter else 0
    return {
        "scope_key": scope_key,
        "limit": AI_LIMIT_PER_PERIOD,
        "used": used,
        "remaining": max(AI_LIMIT_PER_PERIOD - used, 0),
        "period_start": period_start.isoformat() + "Z",
    }


AI_LIMITED_POST_PATHS = {
    "/openai_recommend",
    "/generate_plan",
    "/api/agile-kata/ai",
    "/api/agile-tools/ask",
    "/api/meeting-design/ai-conversation-topics",
    "/api/meeting-design/ai-facilitator-help",
    "/api/meeting-design/generate",
    "/api/meeting-design/regenerate-block",
    "/help",
    "/evaluate",
    "/prep",
    "/api/backlog/prep/assist",
    "/api/meeting-design/form-assist",
    "/api/conflict/resolve",
    "/api/api/conflict/resolve",
    "/api/metrics-tree/explain",
    "/api/metrics-tree/relationship",
    "/api/maturity-admin/group-plan",
}


def _is_dynamic_system_thinking_generate(path: str) -> bool:
    return path.startswith("/api/system-thinking/") and path.endswith("/generate-solutions")


def _is_dynamic_maturity_path(path: str, tail: str) -> bool:
    if not path.startswith("/api/maturity/"):
        return False
    parts = [p for p in path.split("/") if p]
    if len(parts) < 4:
        return False
    return parts[-1] == tail


def should_limit_current_request() -> bool:
    path = request.path
    if request.method == "GET" and path == "/api/maturity-admin/insights":
        return True
    if request.method != "POST":
        return False
    if path in AI_LIMITED_POST_PATHS:
        return True
    if _is_dynamic_system_thinking_generate(path):
        return True
    return (
        _is_dynamic_maturity_path(path, "recommendations")
        or _is_dynamic_maturity_path(path, "dont-know")
        or _is_dynamic_maturity_path(path, "clarify")
    )


def register_ai_limit_hooks(app) -> None:
    @app.before_request
    def _apply_ai_limit():
        if should_limit_current_request():
            check_and_consume_ai_quota()


@bp_ai_limits.route("/api/ai-usage", methods=["GET"])
@jwt_required(optional=True)
def ai_usage_status():
    return jsonify(get_quota_status())
