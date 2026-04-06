# ---------------------------------------------------------------------------
# DNS-over-HTTPS fallback  (MUST run BEFORE eventlet.monkey_patch)
# Render's system DNS cannot resolve api.openai.com — we pre-resolve via
# Cloudflare/Google DoH at startup and short-circuit getaddrinfo so that
# neither the stdlib nor eventlet ever hits the broken resolver for this host.
# ---------------------------------------------------------------------------
import socket as _sock_stdlib
import json as _json_stdlib
import logging as _logging_stdlib
import urllib.request as _urllib_req

_dns_log = _logging_stdlib.getLogger("dns_fallback")
_DOH_HOSTS = ("api.openai.com",)
_doh_cache: dict = {}
_real_getaddrinfo = _sock_stdlib.getaddrinfo


def _resolve_via_doh(hostname: str):
    for doh_url in [
        f"https://1.1.1.1/dns-query?name={hostname}&type=A",
        f"https://8.8.8.8/resolve?name={hostname}&type=A",
    ]:
        try:
            req = _urllib_req.Request(doh_url, headers={"Accept": "application/dns-json"})
            with _urllib_req.urlopen(req, timeout=5) as resp:
                data = _json_stdlib.loads(resp.read())
            for ans in data.get("Answer", []):
                if ans.get("type") == 1:
                    ip = ans["data"]
                    _dns_log.info("DoH resolved %s -> %s via %s", hostname, ip, doh_url[:25])
                    return ip
        except Exception as exc:
            _dns_log.debug("DoH %s failed: %s", doh_url[:25], exc)
    return None


def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host in _doh_cache:
        return _real_getaddrinfo(_doh_cache[host], port, family, type, proto, flags)
    return _real_getaddrinfo(host, port, family, type, proto, flags)


# Pre-resolve at import time (before eventlet touches socket)
for _h in _DOH_HOSTS:
    _ip = _resolve_via_doh(_h)
    if _ip:
        _doh_cache[_h] = _ip

# Patch BEFORE eventlet so eventlet captures our version as "original"
_sock_stdlib.getaddrinfo = _patched_getaddrinfo
# ---------------------------------------------------------------------------

import eventlet
eventlet.monkey_patch()

# Re-apply patch AFTER eventlet.monkey_patch() overwrites socket.getaddrinfo
import socket as _sock_green
_sock_green.getaddrinfo = _patched_getaddrinfo
# ---------------------------------------------------------------------------

from flask import Flask, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from database import db
from survey import bp_survey
from auth import bp_auth
from dashboard import bp_dashboard
from assessment import bp_assessment
from datetime import timedelta
import os
from flask_cors import CORS
from conflict import bp_conflict
from motivation import bp_motivation
from user_profile import profile_bp
from planning_poker import planning_bp
from disc_assessment import disc_bp
from meeting_design import bp_meeting_design
from surveys import surveys_bp
from maturity_link import maturity_bp
from backlog_prep import bp_backlog_prep
from roadmap import bp_roadmap, init_socketio, register_socketio_handlers
from community_chat import bp_community_chat, register_community_socketio_handlers, start_message_cleanup_loop
from system_thinking import bp_system_thinking
from agile_kata import bp_agile_kata
from agile_tools_ai import bp_agile_tools_ai
from testing_types import bp_testing_types
from usability_report import bp_usability_report
from qa_user_story import bp_qa_user_story
from qa_test_docs import bp_qa_test_docs
from flask_socketio import SocketIO
from ai_limits import bp_ai_limits, register_ai_limit_hooks, AiLimitExceeded
from tests_runner import bp_tests

app = Flask(__name__, static_folder="static")
CORS(app, supports_credentials=True)
CORS(app, resources={r"/api/*": {"origins": "https://www.growboard.ru"}}, supports_credentials=True)



# 📦 Подключение к базе данных
database_url = os.getenv("DATABASE_URL", "sqlite:///maturity_local.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
if database_url.startswith("sqlite"):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True
    }
else:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "connect_args": {
            "options": "-c timezone=utc"
        }
    }

# JWT
app.config['JWT_SECRET_KEY'] = 'supersecretkey'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=365)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=730)

# Инициализация
db.init_app(app)
jwt = JWTManager(app)

# Инициализация SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
init_socketio(socketio)
register_socketio_handlers(socketio)
register_community_socketio_handlers(socketio)

with app.app_context():
    db.create_all()
    # Добавление колонки для существующих БД (create_all не меняет таблицы)
    from sqlalchemy import text
    try:
        db.session.execute(
            text("ALTER TABLE qa_test_case_submissions ADD COLUMN share_token VARCHAR(64)")
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
    try:
        db.session.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_qa_test_case_submissions_share_token "
                "ON qa_test_case_submissions (share_token)"
            )
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
    try:
        db.session.execute(
            text("ALTER TABLE maturity_link_session ADD COLUMN recommendations_html TEXT")
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
    try:
        db.session.execute(
            text("ALTER TABLE maturity_link_session ADD COLUMN dont_know_recommendations_html TEXT")
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
    try:
        db.session.execute(
            text("ALTER TABLE maturity_link_session ADD COLUMN recommendations_plan_json JSON")
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
    try:
        db.session.execute(
            text("ALTER TABLE maturity_link_session ADD COLUMN dont_know_recommendations_plan_json JSON")
        )
        db.session.commit()
    except Exception:
        db.session.rollback()

register_ai_limit_hooks(app)
start_message_cleanup_loop(app)

# Blueprints
app.register_blueprint(bp_auth)
app.register_blueprint(bp_survey)
app.register_blueprint(bp_dashboard, url_prefix="/dashboard")
app.register_blueprint(bp_assessment)
app.register_blueprint(bp_conflict, url_prefix="/api")

app.register_blueprint(bp_motivation)

app.register_blueprint(profile_bp, url_prefix="/api")
app.register_blueprint(planning_bp, url_prefix="/api")
app.register_blueprint(disc_bp, url_prefix="/api/disc")
app.register_blueprint(bp_meeting_design)
app.register_blueprint(surveys_bp, url_prefix="/api")
app.register_blueprint(maturity_bp)
app.register_blueprint(bp_backlog_prep)
app.register_blueprint(bp_roadmap)
app.register_blueprint(bp_community_chat)
app.register_blueprint(bp_system_thinking)
app.register_blueprint(bp_agile_kata)
app.register_blueprint(bp_agile_tools_ai)
app.register_blueprint(bp_testing_types)
app.register_blueprint(bp_usability_report)
app.register_blueprint(bp_qa_user_story)
app.register_blueprint(bp_qa_test_docs)
app.register_blueprint(bp_ai_limits)
app.register_blueprint(bp_tests)


@app.errorhandler(AiLimitExceeded)
def handle_ai_limit_exceeded(e):
    return jsonify({"error": e.message}), 429


# 🎯 Отдача Vue SPA
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_vue(path):
    if path != "" and os.path.exists(os.path.join("static", path)):
        return send_from_directory("static", path)
    return send_from_directory("static", "index.html")

@app.route("/api")
def api_root():
    return {"message": "Scrum Maturity API is working!"}


@app.route("/api/ai-health")
def ai_health():
    """Diagnostic: check OpenAI connectivity at DNS / TCP / TLS / API levels."""
    import os as _os
    import socket
    import ssl
    import time
    import importlib

    result = {"openai_lib_version": None, "dns": None, "tcp": None, "tls": None, "api": None}

    try:
        import openai as _oai
        result["openai_lib_version"] = getattr(_oai, "__version__", "unknown")
    except Exception:
        result["openai_lib_version"] = "import_failed"

    key = _os.getenv("OPENAI_API_KEY") or ""
    result["key_set"] = bool(key)
    result["key_masked"] = (key[:7] + "..." + key[-4:]) if len(key) > 12 else ("too_short" if key else "missing")

    host = "api.openai.com"

    t0 = time.time()
    try:
        ips = socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM)
        result["dns"] = {"ok": True, "ms": int((time.time() - t0) * 1000), "ips": list({a[4][0] for a in ips})[:4]}
    except Exception as e:
        result["dns"] = {"ok": False, "ms": int((time.time() - t0) * 1000), "error": str(e)[:200]}
        return jsonify(result), 502

    t0 = time.time()
    try:
        sock = socket.create_connection((host, 443), timeout=10)
        result["tcp"] = {"ok": True, "ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        result["tcp"] = {"ok": False, "ms": int((time.time() - t0) * 1000), "error": str(e)[:200]}
        return jsonify(result), 502

    t0 = time.time()
    try:
        ctx = ssl.create_default_context()
        ssock = ctx.wrap_socket(sock, server_hostname=host)
        result["tls"] = {"ok": True, "ms": int((time.time() - t0) * 1000), "version": ssock.version()}
        ssock.close()
    except Exception as e:
        result["tls"] = {"ok": False, "ms": int((time.time() - t0) * 1000), "error": str(e)[:200]}
        sock.close()
        return jsonify(result), 502

    if not key:
        result["api"] = {"ok": False, "error": "OPENAI_API_KEY not set"}
        return jsonify(result), 503

    t0 = time.time()
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key, timeout=15.0)
        models = client.models.list()
        names = sorted(m.id for m in models.data if "gpt" in m.id)[:20]
        result["api"] = {"ok": True, "ms": int((time.time() - t0) * 1000), "gpt_models": names}
        return jsonify(result)
    except Exception as exc:
        result["api"] = {"ok": False, "ms": int((time.time() - t0) * 1000),
                         "error_type": type(exc).__name__, "detail": str(exc)[:400]}
        return jsonify(result), 502

# Экспортируем socketio для использования в gunicorn
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

