import os
import re
import secrets
import uuid
from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import Blueprint, current_app, request, jsonify
from flask_jwt_extended import create_access_token, decode_token, get_jwt_identity, jwt_required
from sqlalchemy import inspect, text

from database import db
from models import Assessment, Question, Team, User, UserInvite



bp_auth = Blueprint('auth', __name__)


def ensure_auth_runtime_migrations():
    insp = inspect(db.engine)
    if "user_invite" not in insp.get_table_names():
        UserInvite.__table__.create(bind=db.engine, checkfirst=True)
        return
    cols = {c["name"] for c in insp.get_columns("user_invite")}
    changed = False
    if "max_uses" not in cols:
        db.session.execute(text("ALTER TABLE user_invite ADD COLUMN max_uses INTEGER NOT NULL DEFAULT 1"))
        changed = True
    if "use_count" not in cols:
        db.session.execute(text("ALTER TABLE user_invite ADD COLUMN use_count INTEGER NOT NULL DEFAULT 0"))
        changed = True
    if changed:
        db.session.commit()
        # backfill: previously single-use completed invites
        db.session.execute(
            text(
                "UPDATE user_invite SET use_count = 1, max_uses = 1 "
                "WHERE (status = 'used' OR used_by_user_id IS NOT NULL) AND (use_count = 0 OR use_count IS NULL)"
            )
        )
        db.session.commit()


def _valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""))


def _new_invite_code() -> str:
    return f"{uuid.uuid4().hex}_{secrets.token_urlsafe(12)}"


_DEMO_TEAM_SCORE_PATTERN = (3, 3, 4, 3, 4, 3, 4, 3, 3, 4)
_DEMO_RECOMMENDATIONS_HTML = (
    "<p><strong>Демо / Demo</strong></p>"
    "<p>Это пример результатов оценки зрелости — так выглядит отчёт после прохождения опроса. "
    "Пройдите оценку заново для своей команды, чтобы заменить данные на реальные.</p>"
    "<p><em>This is sample maturity data. Run the survey for your team to see real scores and recommendations.</em></p>"
)


def _seed_demo_team_with_maturity_assessment(user_id: int) -> None:
    """Создаёт демо-команду с заполненным опросником зрелости (одна «сессия» оценки)."""
    questions = Question.query.order_by(Question.id).all()
    if not questions:
        return
    team_name = f"Команда-пример · {user_id}"
    if Team.query.filter_by(name=team_name).first():
        return
    ts = datetime.utcnow()
    team = Team(name=team_name, user_id=user_id, created_at=ts)
    db.session.add(team)
    db.session.flush()
    first_row = None
    for i, q in enumerate(questions):
        score = _DEMO_TEAM_SCORE_PATTERN[i % len(_DEMO_TEAM_SCORE_PATTERN)]
        row = Assessment(
            user_id=user_id,
            team_id=team.id,
            question_id=q.id,
            score=score,
            created_at=ts,
        )
        db.session.add(row)
        if i == 0:
            first_row = row
    db.session.flush()
    if first_row is not None:
        first_row.recommendations = _DEMO_RECOMMENDATIONS_HTML


@bp_auth.route('/register', methods=['POST'])
def register():
    ensure_auth_runtime_migrations()
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")
    invite_code = (data.get("invite_code") or "").strip()

    if not email or not password or not invite_code:
        return jsonify({"error": "Email, password and invite_code are required"}), 400

    existing_user = User.query.filter_by(username=email).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 400

    invite = UserInvite.query.filter_by(code=invite_code).first()
    now = datetime.utcnow()
    if not invite:
        return jsonify({"error": "Invite code is invalid"}), 400
    if invite.status != "active":
        return jsonify({"error": "Invite is not active"}), 400
    if invite.expires_at and invite.expires_at < now:
        invite.status = "expired"
        db.session.commit()
        return jsonify({"error": "Invite expired"}), 400
    max_uses = int(invite.max_uses or 1)
    if max_uses < 1:
        max_uses = 1
    use_count = int(invite.use_count or 0)
    if use_count >= max_uses:
        return jsonify({"error": "Invite already used"}), 400
    if invite.invitee_email and invite.invitee_email.lower() != email.lower():
        return jsonify({"error": "Invite is bound to another email"}), 400

    new_user = User(username=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.flush()

    invite.use_count = use_count + 1
    invite.used_by_user_id = new_user.id
    invite.used_at = now
    if invite.use_count >= max_uses:
        invite.status = "used"

    try:
        with db.session.begin_nested():
            _seed_demo_team_with_maturity_assessment(int(new_user.id))
    except Exception as e:
        current_app.logger.warning("Demo maturity team seed skipped: %s", e)

    db.session.commit()

    return jsonify({"message": "User registered successfully!"})

@bp_auth.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": access_token})


@bp_auth.route('/api/invites', methods=['POST'])
@jwt_required()
def create_invite():
    ensure_auth_runtime_migrations()
    inviter_user_id = int(get_jwt_identity())
    data = request.json or {}
    invitee_email = (data.get("invitee_email") or "").strip().lower() or None
    ttl_days = int(data.get("ttl_days") or 7)
    ttl_days = max(1, min(ttl_days, 30))
    max_uses = int(data.get("max_uses") or 1)
    max_uses = max(1, min(max_uses, 100))

    if max_uses > 1 and invitee_email:
        return jsonify({"error": "For multi-use codes, leave invitee email empty"}), 400

    if invitee_email and not _valid_email(invitee_email):
        return jsonify({"error": "Invalid invitee email"}), 400

    invite = UserInvite(
        code=_new_invite_code(),
        inviter_user_id=inviter_user_id,
        invitee_email=invitee_email,
        max_uses=max_uses,
        use_count=0,
        expires_at=datetime.utcnow() + timedelta(days=ttl_days),
        status="active",
    )
    db.session.add(invite)
    db.session.commit()
    return jsonify({
        "id": invite.id,
        "code": invite.code,
        "invitee_email": invite.invitee_email,
        "max_uses": invite.max_uses,
        "use_count": invite.use_count,
        "status": invite.status,
        "expires_at": invite.expires_at.isoformat() + "Z",
        "created_at": invite.created_at.isoformat() + "Z",
    }), 201


@bp_auth.route('/api/invites/my', methods=['GET'])
@jwt_required()
def my_invites():
    ensure_auth_runtime_migrations()
    user_id = int(get_jwt_identity())
    now = datetime.utcnow()
    invites = UserInvite.query.filter_by(inviter_user_id=user_id).order_by(UserInvite.created_at.desc()).all()
    out = []
    changed = False
    for inv in invites:
        max_uses = int(getattr(inv, "max_uses", None) or 1)
        use_count = int(getattr(inv, "use_count", None) or 0)
        if max_uses < 1:
            max_uses = 1
        uses_remaining = max(0, max_uses - use_count)
        status = inv.status
        if status == "active" and inv.expires_at and inv.expires_at < now:
            status = "expired"
            inv.status = "expired"
            changed = True
        elif status == "active" and uses_remaining == 0:
            status = "used"
        out.append({
            "id": inv.id,
            "code": inv.code,
            "invitee_email": inv.invitee_email,
            "max_uses": max_uses,
            "use_count": use_count,
            "uses_remaining": uses_remaining,
            "status": status,
            "expires_at": inv.expires_at.isoformat() + "Z" if inv.expires_at else None,
            "created_at": inv.created_at.isoformat() + "Z" if inv.created_at else None,
            "used_at": inv.used_at.isoformat() + "Z" if inv.used_at else None,
            "used_by_user_id": inv.used_by_user_id,
        })
    if changed:
        db.session.commit()
    return jsonify({"invites": out})


SECRET_KEY = os.getenv("SECRET_KEY", "my_secret_key")


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token or "Bearer " not in token:
            return jsonify({"error": "Токен отсутствует!"}), 401

        token = token.split(" ")[1]  # Убираем "Bearer "

        try:
            data = decode_token(token)
            current_user = User.query.get(data["sub"])
            if not current_user:
                return jsonify({"error": "Пользователь не найден"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Токен истёк"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Недействительный токен"}), 401

        return f(current_user, *args, **kwargs)

    return decorated
