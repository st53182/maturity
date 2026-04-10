# Оценка зрелости по ссылке: пять вариантов ответа, баллы за вопрос, результаты для радара и PDF.
import logging
import os
import json
import html as html_module
import re
import uuid
from datetime import datetime
from collections import defaultdict

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from sqlalchemy import inspect, text

from database import db
from models import MaturityLinkSession, MaturityGroupPlan, User
from maturity_questions import (
    MATURITY_QUESTIONS,
    RADAR_GROUPS,
    ROLE_BY_THEME,
    BUSINESS_METRICS_DISCLAIMER,
    BUSINESS_METRICS_GLOSSARY,
)
from maturity_survey_locale import (
    resolve_survey_lang,
    localize_question_dict,
    localize_related_roles,
    localized_business_metrics_disclaimer,
    localized_business_metrics_glossary,
)

maturity_bp = Blueprint('maturity_link', __name__)
_log = logging.getLogger(__name__)


def _openai_http_response(exc: BaseException):
    """Переводит исключения OpenAI SDK в JSON и HTTP-код для публичных эндпоинтов."""
    exc_type = type(exc).__name__
    exc_msg = str(exc)[:600]
    _log.error("OpenAI error in maturity_link [%s]: %s", exc_type, exc_msg)
    try:
        from openai import APIError, APIConnectionError, APITimeoutError, RateLimitError, AuthenticationError

        if isinstance(exc, RateLimitError):
            return jsonify(
                {"error": "Превышен лимит запросов к AI. Повторите через несколько минут."}
            ), 429
        if isinstance(exc, AuthenticationError):
            _log.error("OpenAI AuthenticationError — check OPENAI_API_KEY on server")
            return jsonify({"error": f"Сервис рекомендаций временно недоступен (ошибка авторизации AI: {exc_type})."}), 503
        if isinstance(exc, (APIConnectionError, APITimeoutError)):
            return jsonify({"error": f"Не удалось связаться с сервисом AI ({exc_type}). Повторите позже."}), 503
        if isinstance(exc, APIError):
            return jsonify({"error": f"Ошибка сервиса AI ({exc_type}): {exc_msg[:300]}"}), 502
    except ImportError:
        pass
    _log.exception("Unhandled OpenAI exception in maturity_link")
    return jsonify({"error": f"Внутренняя ошибка ({exc_type}): {exc_msg[:300]}"}), 500


def _openai_client():
    """Клиент OpenAI с таймаутом (на проде без таймаута долгие запросы дают 502 от прокси)."""
    from openai import OpenAI

    timeout = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "120"))
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=timeout)


def _unique_model_chain(*names):
    seen = set()
    out = []
    for n in names:
        n = (n or "").strip()
        if not n or n in seen:
            continue
        seen.add(n)
        out.append(n)
    return out


def _openai_chat_model_list(
    env_primary: str, default_primary: str, *fallbacks: str
) -> list:
    """Модель из env; при ошибке API — запасные модели (если fallbacks не заданы: gpt-4o, gpt-4-turbo)."""
    primary = os.getenv(env_primary, default_primary)
    if fallbacks:
        return _unique_model_chain(primary, *fallbacks)
    return _unique_model_chain(primary, "gpt-4o", "gpt-4-turbo")


def _maturity_plan_model_chain(env_primary: str) -> list:
    """Цепочка для планов команды/группы: gpt-5-mini по умолчанию."""
    return _openai_chat_model_list(
        env_primary,
        "gpt-5-mini",
        "gpt-4.1",
        "gpt-4o",
        "gpt-4-turbo",
    )


def _is_gpt5(model: str) -> bool:
    return "gpt-5" in (model or "").strip().lower().split("/")[-1]


def _adapt_chat_kwargs_for_model(model: str, kwargs: dict) -> dict:
    """Normalize kwargs for OpenAI Chat Completions.

    gpt-5* (reasoning model family) rejects:
      - max_tokens  (use max_completion_tokens)
      - temperature (only default 1)
      - top_p       (only default 1)
    """
    out = dict(kwargs)
    if "max_tokens" in out and "max_completion_tokens" not in out:
        out["max_completion_tokens"] = out.pop("max_tokens")

    if _is_gpt5(model):
        out.pop("temperature", None)
        out.pop("top_p", None)

    return out


def _chat_completions_with_model_fallback(client, model_names, **kwargs):
    from openai import (
        APIError,
        APIConnectionError,
        APITimeoutError,
        RateLimitError,
        AuthenticationError,
    )

    if not model_names:
        raise ValueError("model_names is empty")
    last = None
    for m in model_names:
        try:
            call_kwargs = _adapt_chat_kwargs_for_model(m, kwargs)
            resp = client.chat.completions.create(model=m, **call_kwargs)
            if m != model_names[0]:
                _log.warning(
                    "OpenAI chat: used fallback model=%s (primary=%s)",
                    m,
                    model_names[0],
                )
            return resp
        except (RateLimitError, AuthenticationError, APIConnectionError, APITimeoutError):
            raise
        except APIError as e:
            last = e
            _log.warning(
                "OpenAI chat model=%s failed [%s]: %s",
                m,
                type(e).__name__,
                str(e)[:240],
            )
            continue
    raise last


# Значения ответа в JSON (строки). Устаревшие: true → yes, false → no.
MATURITY_ANSWER_KEYS = frozenset({'no', 'rather_no', 'dont_know', 'rather_yes', 'yes'})
MATURITY_ANSWER_SCORE = {
    'no': 0.0,
    'rather_no': 0.0,
    'dont_know': 0.0,
    'rather_yes': 0.5,
    'yes': 1.0,
}

QUESTIONS_COUNT = len(MATURITY_QUESTIONS)
QUESTIONS_PER_THEME = 3
AGILE_TOOLS_LINKS = [
    "Impact Mapping",
    "Wardley Mapping",
    "Story Mapping",
    "Value Stream Mapping",
    "A/B Testing",
    "OKR",
    "RICE",
    "WSJF",
    "Kano",
    "JTBD",
    "Lean Canvas",
    "FMEA",
    "5 Whys",
    "Ishikawa Diagram",
]

def _load_maturity_link_admin_emails():
    """
    Базовый список + MATURITY_LINK_ADMIN_EMAILS из окружения (через запятую).
    Синхронизируйте дефолты с vue-frontend/src/config/maturityLinkAdmin.js (DEFAULT_EMAILS).
    """
    base = {
        'artem@onagile.ru',
        'artjoms.grinakins@gmail.com',
    }
    raw = os.environ.get('MATURITY_LINK_ADMIN_EMAILS') or ''
    for part in raw.split(','):
        e = part.strip().lower()
        if e and '@' in e:
            base.add(e)
    return frozenset(base)


# Держать дефолты в sync с vue-frontend/src/config/maturityLinkAdmin.js
MATURITY_LINK_ADMIN_EMAILS = _load_maturity_link_admin_emails()


def _theme_indices():
    from collections import OrderedDict
    out = OrderedDict()
    for i, q in enumerate(MATURITY_QUESTIONS):
        theme = q["theme"]
        if theme not in out:
            out[theme] = []
        out[theme].append(i)
    return out


THEME_INDICES = _theme_indices()

DEFAULT_BUSINESS_METRICS = (
    "Позитивный ответ («Да») способствует улучшению продуктовых и операционных метрик в рамках продукта "
    "(retention, LTV, конверсия, снижение издержек — связь транзитивная). "
    "(На примере анализа данных из Citibank, Deutsche Bank.)"
)


def _canonical_maturity_answer_key(a):
    """Привести значение к одному из MATURITY_ANSWER_KEYS или None."""
    if a is True:
        return 'yes'
    if a is False:
        return 'no'
    if not isinstance(a, str):
        return None
    key = a.strip().lower().replace(' ', '_').replace('-', '_')
    if key in MATURITY_ANSWER_KEYS:
        return key
    return None


def _parse_submitted_answer(a):
    """Один элемент ответа: строка из MATURITY_ANSWER_KEYS или устаревшие true/false."""
    return _canonical_maturity_answer_key(a)


def _validate_answers_list(answers):
    if not isinstance(answers, list) or len(answers) != QUESTIONS_COUNT:
        return None, 'length'
    out = []
    for cell in answers:
        v = _parse_submitted_answer(cell)
        if v is None:
            return None, 'invalid'
        out.append(v)
    return out, None


def _normalize_stored_answer_cell(a):
    """Привести значение из БД к каноническому ключу ответа (строка)."""
    c = _canonical_maturity_answer_key(a)
    if c is not None:
        return c
    if isinstance(a, bool):
        return 'yes' if a else 'no'
    return 'no'


def _normalize_stored_answers_row(raw_list):
    if not isinstance(raw_list, list) or len(raw_list) != QUESTIONS_COUNT:
        return None
    return [_normalize_stored_answer_cell(x) for x in raw_list]


def _results_from_answers(answers):
    """answers: список канонических ключей. Баллы: нет/скорее нет/не знаю=0, скорее да=0.5, да=1."""
    if not answers or len(answers) != QUESTIONS_COUNT:
        return {}
    results = {}
    for theme, indices in THEME_INDICES.items():
        results[theme] = {}
        for sub_one_based, q_idx in enumerate(indices[:QUESTIONS_PER_THEME], 1):
            a = answers[q_idx]
            score = float(MATURITY_ANSWER_SCORE.get(a, 0.0))
            results[theme][str(sub_one_based)] = score
    return results


def _repair_truncated_json(text: str) -> str:
    """Close unclosed brackets/braces in truncated JSON from the LLM."""
    open_braces = 0
    open_brackets = 0
    in_string = False
    escape = False
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == '\\' and in_string:
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            open_braces += 1
        elif ch == '}':
            open_braces -= 1
        elif ch == '[':
            open_brackets += 1
        elif ch == ']':
            open_brackets -= 1

    if in_string:
        text = text.rstrip()
        if text.endswith('\\'):
            text = text[:-1]
        text += '"'

    tail = ""
    for _ in range(max(open_brackets, 0)):
        tail += "]"
    for _ in range(max(open_braces, 0)):
        tail += "}"
    return text + tail


def _safe_json_object(raw_text: str):
    """Best-effort JSON object parser for LLM output."""
    text = (raw_text or "").strip()
    if not text:
        return {}
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    text = text.strip()
    text = text.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'")

    def _try_parse(s):
        try:
            obj = json.loads(s)
        except Exception:
            try:
                obj = json.loads(s, strict=False)
            except Exception:
                return None
        if isinstance(obj, dict):
            return obj
        if isinstance(obj, str):
            try:
                obj2 = json.loads(obj)
                return obj2 if isinstance(obj2, dict) else None
            except Exception:
                return None
        return None

    result = _try_parse(text)
    if result is not None:
        return result

    start = text.find("{")
    if start < 0:
        return {}
    candidate = text[start:]

    candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
    result = _try_parse(candidate)
    if result is not None:
        return result

    repaired = _repair_truncated_json(candidate)
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    result = _try_parse(repaired)
    if result is not None:
        return result

    return {}




def _extract_answers_and_comments(raw_answers):
    """
    Backward-compatible storage:
    - old format: list[bool]
    - new format: { "answers": list, "comments": list[str|null] }
    """
    if isinstance(raw_answers, dict):
        answers = raw_answers.get("answers")
        comments = raw_answers.get("comments")
        if not isinstance(answers, list):
            answers = None
        if not isinstance(comments, list):
            comments = None
        return answers, comments
    if isinstance(raw_answers, list):
        return raw_answers, None
    return None, None


def _get_maturity_admin_user():
    uid = get_jwt_identity()
    try:
        uid = int(uid)
    except (TypeError, ValueError):
        return None
    user = User.query.get(uid)
    if not user or not user.username:
        return None
    if user.username.strip().lower() not in MATURITY_LINK_ADMIN_EMAILS:
        return None
    return user


def _normalize_group_name(value):
    if value is None:
        return None
    s = str(value).strip()
    return s[:255] if s else None


def _default_group_plan():
    return {
        "diagnosis": "",
        "initiatives": [],
        "roadmap": [],
        "risks": [],
    }


def _normalize_group_plan(payload):
    src = payload if isinstance(payload, dict) else {}
    plan = _default_group_plan()
    plan["diagnosis"] = str(src.get("diagnosis") or "").strip()

    initiatives = src.get("initiatives")
    if isinstance(initiatives, list):
        for item in initiatives[:12]:
            if not isinstance(item, dict):
                continue
            plan["initiatives"].append({
                "title": str(item.get("title") or "").strip(),
                "objective": str(item.get("objective") or "").strip(),
                "owner": str(item.get("owner") or "").strip(),
                "success_metric": str(item.get("success_metric") or "").strip(),
                "business_impact": str(item.get("business_impact") or "").strip(),
                "customer_impact": str(item.get("customer_impact") or "").strip(),
                "steps": [str(s).strip() for s in (item.get("steps") or []) if str(s).strip()][:8],
            })

    roadmap = src.get("roadmap")
    if isinstance(roadmap, list):
        for row in roadmap[:20]:
            if not isinstance(row, dict):
                continue
            plan["roadmap"].append({
                "period": str(row.get("period") or "").strip(),
                "start_date": str(row.get("start_date") or "").strip(),
                "end_date": str(row.get("end_date") or "").strip(),
                "initiative": str(row.get("initiative") or "").strip(),
                "milestone": str(row.get("milestone") or "").strip(),
            })

    risks = src.get("risks")
    if isinstance(risks, list):
        plan["risks"] = [str(r).strip() for r in risks if str(r).strip()][:12]

    return plan


def _group_plan_to_html(group_name, plan):
    p = _normalize_group_plan(plan)
    html = [f"<h3>План улучшений стрима: {group_name}</h3>"]
    if p["diagnosis"]:
        html.append(f"<p><strong>Диагноз:</strong> {p['diagnosis']}</p>")
    if p["initiatives"]:
        html.append("<h4>Инициативы</h4><ul>")
        for idx, i in enumerate(p["initiatives"], start=1):
            steps = i.get("steps") or []
            steps_html = ""
            if steps:
                items = "".join(
                    f"<li>{html_module.escape(str(s))}</li>" for s in steps if str(s).strip()
                )
                if items:
                    steps_html = (
                        "<br><strong>Конкретные шаги:</strong><ol>"
                        f"{items}</ol>"
                    )
            html.append(
                f"<li><strong>{idx}. {i['title'] or 'Инициатива'}</strong><br>"
                f"Цель: {i['objective'] or '—'}<br>"
                f"Владелец: {i['owner'] or '—'}<br>"
                f"Метрика успеха: {i['success_metric'] or '—'}<br>"
                f"Бизнес-эффект: {i['business_impact'] or '—'}<br>"
                f"Эффект для заказчиков: {i['customer_impact'] or '—'}"
                f"{steps_html}</li>"
            )
        html.append("</ul>")
    if p["roadmap"]:
        html.append("<h4>Roadmap (12 недель)</h4><ul>")
        for r in p["roadmap"]:
            html.append(
                f"<li><strong>{r['period'] or 'Период'}</strong> "
                f"({r['start_date'] or '—'} - {r['end_date'] or '—'}): "
                f"{r['initiative'] or '—'} — {r['milestone'] or '—'}</li>"
            )
        html.append("</ul>")
    if p["risks"]:
        html.append("<h4>Риски и меры снижения</h4><ul>")
        for r in p["risks"]:
            html.append(f"<li>{r}</li>")
        html.append("</ul>")
    return "".join(html)


def _ensure_maturity_link_session_columns():
    """
    Лёгкая runtime-миграция: добавляет новые колонки в существующую таблицу,
    чтобы локальные SQLite/Postgres базы не падали после деплоя.
    """
    try:
        inspector = inspect(db.engine)
        columns = {c["name"] for c in inspector.get_columns("maturity_link_session")}
        if "group_name" not in columns:
            db.session.execute(text("ALTER TABLE maturity_link_session ADD COLUMN group_name VARCHAR(255)"))
        db.session.commit()
    except Exception:
        db.session.rollback()


def _ensure_group_plan_table():
    try:
        db.create_all()
    except Exception:
        db.session.rollback()


def _normalize_comments_list(comments):
    if not isinstance(comments, list):
        return None
    out = []
    for c in comments:
        if c is None:
            out.append(None)
            continue
        s = str(c).strip()
        if not s:
            out.append(None)
            continue
        out.append(s[:2000])
    return out


def _metrics_tree_access_allowed(survey_token=None):
    token = (survey_token or "").strip()
    if token:
        session = MaturityLinkSession.query.filter_by(access_token=token).first()
        if session:
            return True
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        return uid is not None
    except Exception:
        return False


@maturity_bp.route('/api/maturity-link', methods=['POST'])
@jwt_required(optional=True)
def create_maturity_link():
    """Создать сессию оценки по ссылке. Тело: { "team_name": "опционально" }. Возвращает token и url."""
    _ensure_maturity_link_session_columns()
    data = request.get_json() or {}
    team_name = data.get('team_name', '').strip() or None
    group_name = _normalize_group_name(data.get('group_name'))
    token = str(uuid.uuid4())
    session = MaturityLinkSession(access_token=token, team_name=team_name, group_name=group_name)
    db.session.add(session)
    db.session.commit()
    base = request.host_url.rstrip('/')
    return jsonify({
        'token': token,
        'url': f'{base}/new/maturity/{token}',
        'team_name': session.team_name,
        'group_name': session.group_name
    }), 201


@maturity_bp.route('/api/maturity/<token>', methods=['GET'])
def get_maturity_survey(token):
    """Публично: получить опрос по токену (вопросы с id 0..N-1, по 10 на страницу)."""
    lang = resolve_survey_lang(request)
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        err = (
            'Link not found or invalid'
            if lang == 'en'
            else 'Ссылка не найдена или недействительна'
        )
        return jsonify({'error': err}), 404
    questions = []
    for i, q in enumerate(MATURITY_QUESTIONS):
        base = {
            'id': i,
            'category': q['category'],
            'theme': q['theme'],
            'text': q['text'],
            'why_important': q.get('why_important', ''),
            'metrics_impact': q.get('metrics_impact', ''),
            'negative_for_business': q.get('negative_for_business', ''),
            'business_metrics': q.get('business_metrics') or DEFAULT_BUSINESS_METRICS,
            'related_roles': ROLE_BY_THEME.get(q['theme'], []),
        }
        base = localize_question_dict(i, base, lang)
        base['related_roles'] = localize_related_roles(base['related_roles'], lang)
        questions.append(base)
    return jsonify({
        'team_name': session.team_name,
        'group_name': session.group_name,
        'completed': session.completed_at is not None,
        'questions': questions,
        'lang': lang,
        'business_metrics_disclaimer': localized_business_metrics_disclaimer(lang),
        'business_metrics_glossary': localized_business_metrics_glossary(
            BUSINESS_METRICS_GLOSSARY, lang
        ),
    })


@maturity_bp.route('/api/maturity/<token>/submit', methods=['POST'])
def submit_maturity_answers(token):
    """Публично: отправить ответы. Тело: answers — N строк: no | rather_no | dont_know | rather_yes | yes (допустимы устаревшие true/false)."""
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        return jsonify({'error': 'Ссылка не найдена'}), 404
    if session.completed_at:
        return jsonify({'error': 'Оценка уже пройдена', 'results_url': f'/new/maturity/{token}/results'}), 400
    data = request.get_json() or {}
    answers = data.get('answers')
    comments = data.get('comments')
    normalized, err = _validate_answers_list(answers)
    if err:
        return jsonify({
            'error': (
                f'Нужен массив из {QUESTIONS_COUNT} ответов: '
                '"no", "rather_no", "dont_know", "rather_yes", "yes" '
                '(или устаревшие true/false)'
            ),
        }), 400
    if comments is not None:
        if not isinstance(comments, list) or len(comments) != QUESTIONS_COUNT:
            return jsonify({'error': f'Поле comments должно быть массивом из {QUESTIONS_COUNT} элементов (или отсутствовать)'}), 400
        session.answers = {"answers": normalized, "comments": _normalize_comments_list(comments)}
    else:
        session.answers = normalized
    session.completed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({
        'message': 'Ответы сохранены',
        'results_url': f'/new/maturity/{token}/results'
    }), 200


@maturity_bp.route('/api/maturity/<token>/answers', methods=['PUT'])
def update_maturity_answers(token):
    """Обновить ответы (в т.ч. для уже пройденной оценки — пересчёт отчёта)."""
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        return jsonify({'error': 'Ссылка не найдена'}), 404
    data = request.get_json() or {}
    answers = data.get('answers')
    comments = data.get('comments')
    normalized, err = _validate_answers_list(answers)
    if err:
        return jsonify({
            'error': (
                f'Нужен массив из {QUESTIONS_COUNT} ответов: '
                '"no", "rather_no", "dont_know", "rather_yes", "yes" '
                '(или устаревшие true/false)'
            ),
        }), 400
    if comments is not None and (not isinstance(comments, list) or len(comments) != QUESTIONS_COUNT):
        return jsonify({'error': f'Поле comments должно быть массивом из {QUESTIONS_COUNT} элементов (или отсутствовать)'}), 400

    if isinstance(comments, list):
        nc = _normalize_comments_list(comments)
        session.answers = {"answers": normalized, "comments": nc}
    else:
        prev_answers, prev_comments = _extract_answers_and_comments(session.answers)
        if isinstance(prev_comments, list) and len(prev_comments) == QUESTIONS_COUNT:
            session.answers = {"answers": normalized, "comments": prev_comments}
        else:
            session.answers = normalized
    db.session.commit()
    return jsonify({
        'message': 'Ответы обновлены',
        'results_url': f'/new/maturity/{token}/results'
    }), 200


@maturity_bp.route('/api/maturity/<token>/results', methods=['GET'])
def get_maturity_results(token):
    """Публично: результаты для радара и PDF. answers: канонические строки ответов."""
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        return jsonify({'error': 'Ссылка не найдена'}), 404
    lang = resolve_survey_lang(request)
    answers_list, comments_list = _extract_answers_and_comments(session.answers)
    if not session.completed_at or not answers_list:
        return jsonify({'error': 'Оценка ещё не пройдена'}), 400
    normalized = _normalize_stored_answers_row(answers_list)
    if not normalized:
        return jsonify({'error': 'Некорректные данные ответов'}), 400
    results = _results_from_answers(normalized)
    completed_at = session.completed_at.isoformat() if session.completed_at else None
    questions = [
        localize_question_dict(
            i,
            {
                'id': i,
                'theme': q['theme'],
                'text': q['text'],
                'why_important': q.get('why_important', ''),
                'metrics_impact': q.get('metrics_impact', ''),
                'negative_for_business': q.get('negative_for_business', ''),
                'business_metrics': q.get('business_metrics') or DEFAULT_BUSINESS_METRICS,
            },
            lang,
        )
        for i, q in enumerate(MATURITY_QUESTIONS)
    ]
    team_default = 'Team' if lang == 'en' else 'Команда'
    return jsonify({
        'team_name': session.team_name or team_default,
        'completed_at': completed_at,
        'results': results,
        'radar_groups': RADAR_GROUPS,
        'answers': normalized,
        'comments': comments_list or [None] * QUESTIONS_COUNT,
        'questions': questions,
        'business_metrics_disclaimer': localized_business_metrics_disclaimer(lang),
        'business_metrics_glossary': localized_business_metrics_glossary(BUSINESS_METRICS_GLOSSARY, lang),
        'recommendations_html': session.recommendations_html or '',
        'recommendations_plan': _normalize_group_plan(session.recommendations_plan_json),
        'dont_know_recommendations_html': session.dont_know_recommendations_html or '',
        'dont_know_recommendations_plan': _normalize_group_plan(session.dont_know_recommendations_plan_json),
    })


@maturity_bp.route('/api/maturity/<token>/recommendations', methods=['GET'])
def get_saved_maturity_recommendations(token):
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        return jsonify({'error': 'Ссылка не найдена'}), 404
    return jsonify({
        "content": session.recommendations_html or '',
        "plan": _normalize_group_plan(session.recommendations_plan_json),
    })


@maturity_bp.route('/api/maturity/<token>/recommendations', methods=['PUT'])
def save_maturity_recommendations(token):
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        return jsonify({'error': 'Ссылка не найдена'}), 404
    data = request.get_json() or {}
    plan = _normalize_group_plan(data.get("plan"))
    html = str(data.get("content") or "").strip() or _group_plan_to_html(session.team_name or "Команда", plan)
    session.recommendations_plan_json = plan
    session.recommendations_html = html
    db.session.commit()
    return jsonify({
        "success": True,
        "content": session.recommendations_html or '',
        "plan": _normalize_group_plan(session.recommendations_plan_json),
    })


@maturity_bp.route('/api/maturity/<token>/recommendations', methods=['POST'])
def get_maturity_recommendations(token):
    """Публично: сгенерировать рекомендации по результатам через OpenAI."""
    import os
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        return jsonify({'error': 'Ссылка не найдена'}), 404
    if not session.completed_at or not session.answers:
        return jsonify({'error': 'Оценка ещё не пройдена'}), 400
    if not os.getenv('OPENAI_API_KEY'):
        return jsonify({'error': 'Сервис рекомендаций не настроен (OPENAI_API_KEY)'}), 503

    raw_ans, _ = _extract_answers_and_comments(session.answers)
    normalized = _normalize_stored_answers_row(raw_ans)
    if not normalized:
        return jsonify({'error': 'Некорректные данные ответов'}), 400
    results = _results_from_answers(normalized)
    summary_lines = []
    for cat, subs in results.items():
        vals = [float(v) for v in subs.values()]
        total_score = sum(vals)
        yes_count = sum(1 for v in vals if v >= 1)
        half_count = sum(1 for v in vals if abs(v - 0.5) < 1e-9)
        summary_lines.append(
            f"- {cat}: сумма баллов {total_score:.1f}/3, «да»={yes_count}/3, «скорее да»={half_count}/3"
        )

    summary_text = "\n".join(summary_lines)
    client = _openai_client()

    tools_hint = ", ".join(AGILE_TOOLS_LINKS)
    prompt = f"""Ты опытный Agile-коуч. По результатам оценки зрелости команды (да/нет по темам) дай конкретный план улучшений для команды.

Результаты по категориям (3 вопроса на тему; за вопрос: нет/скорее нет/не знаю=0, скорее да=0.5, да=1; максимум по теме = 3):
{summary_text}

Контекст (обязательно):
- Считай, что команда **уже как-то использует Scrum** (ритуалы и артефакты могут быть формальными, нестабильными или «для галочки»), но это не нулевая зрелость и не «мы только думаем внедрить Agile».
- **Не давай** рекомендаций в духе «впервые ввести/начать ретро, дейли, планирование спринта, бэклог, ревью» как будто их нет. Вместо этого — **докрутить качество**: формат, глубина, метрики, договорённости, DoR/DoD, фокус на ценности, снятие формализма.
- План строй **строго от переданных баллов по темам**: приоритет — категории с **низкой суммой** и малым числом «да»; названия инициатив и шаги должны отражать **конкретные слабые темы** из сводки (можно упоминать тему в title/objective). Для сильных тем — 0–1 инициатива на усиление, без обучения «с нуля».

Тип команд (важно):
- Ориентируйся на команды **обеспечения поставки** и **внутренние платформенные/сервисные** (enablement, общие сервисы, платформа, интеграции, инфраструктура как продукт для внутренних заказчиков), а не на классические **продуктовые** команды у конечного клиента.
- Примеры ценности: короче очередь на поставку для продуктовых команд, стабильнее пайплайн и релизы, быстрее готовность API/среды/интеграции, меньше ожидание внутреннего заказчика. Не уводи фокус только в продуктовые метрики конечного клиента (конверсия в приложении и т.п.), если это не вытекает из темы оценки.

Приоритет инициатив (сначала поток):
- **В первую очередь** предлагай инициативы, которые сокращают **Lead Time** (время от запроса до результата в эксплуатации у потребителя ценности) и **T2M / Time-to-Market** (скорость вывода изменений; для enablement — время до готовности возможности для смежных команд).
- Минимум **3 из 5** инициатив: в поле `business_impact` обязательно тег **[Lead Time]** и/или **[T2M]** (можно оба). Остальные две не должны противоречить приоритету потока.

Язык и термины:
- Весь ответ на русском. Любой **англоязычный термин** (например Sprint Goal, backlog, DoR, DoD, CI/CD, WIP) при **первом упоминании** в diagnosis, title, objective, steps сопровождай **кратким пояснением в скобках** по-русскому.

Требования:
- Сфокусируйся на категориях с низким баллом; для сильных сторон можно дать 1–2 совета по усилению.
- Ровно 5 инициатив (не больше и не меньше).
- В каждой инициативе массив steps: ровно 5–7 строк. Каждая строка — исполнимый шаг: глагол + конкретный объект/артефакт + срок или частота (например «в течение 3 дней», «на ближайшем планировании», «еженедельно») + кто отвечает (роль). Запрещены размытые фразы без места, времени и измеримого результата («улучшить коммуникацию» без канала и артефакта).
- objective: одна чёткая цель инициативы; owner: роль/функция владельца (не выдумывай ФИО).
- success_metric: формулировка «текущая база → цель за 2–4 недели» или явный порог; обязательно связь с T2M, Lead Time или выбранной бизнес-метрикой. Не придумывай числа, которых нет в данных оценки.
- business_impact: начни с 1–2 тегов из набора в квадратных скобках: [T2M], [Lead Time], [Гибкость приоритетов], [Предсказуемость поставки], [Cost-to-serve], [Качество/дефектность], [Удержание/NPS] — затем 1–2 предложения: что получит бизнес. Без выдуманных процентов и выручки «с потолка».
- customer_impact: эффект для заказчика/пользователя, согласованный с business_impact.
- Главный фокус: операционные практики — процессы, WIP-лимиты, приоритизация, DoR/DoD, декомпозиция, QA-петли, метрики потока.
- Минимизируй абстракции про мировоззрение, ценности, культуру без конкретных действий и артефактов.
- Не предлагай ротацию ролей PO/DPO и любые перестановки PO/DPO.
- Приоритизируй инициативы по ожидаемому эффекту на T2M, Lead Time и бизнес-метрики (выручка, удержание, cost-to-serve — только как тип связи, без цифр).
- Добавь отдельный подзаголовок «Инструменты GrowBoard», где дашь 1-3 релевантных инструмента и ссылки в формате HTML:
  <a href="/new/agile-tools">Название инструмента (поиск в Agile Tools)</a>.
  Можно использовать только инструменты из списка: {tools_hint}.
- Ответ верни ТОЛЬКО JSON (без markdown) в структуре:
{{
  "diagnosis": "2-4 предложения",
  "initiatives": [
    {{
      "title": "...",
      "objective": "...",
      "owner": "...",
      "success_metric": "...",
      "business_impact": "...",
      "customer_impact": "...",
      "steps": ["5–7 исполнимых шагов по правилам выше"]
    }}
  ],
  "roadmap": [
    {{
      "period": "Недели 1-2",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "initiative": "...",
      "milestone": "..."
    }}
  ],
  "risks": ["..."]
}}
- Пиши по-русски; при необходимости допустимы англоязычные термины с кратким русским пояснением в скобках при первом упоминании (согласно блоку «Язык и термины» выше)."""

    rec_models = _maturity_plan_model_chain("MATURITY_TEAM_PLAN_MODEL")
    _log.info(
        "Maturity recommendations: model_chain=%s, token=%s",
        rec_models,
        token[:8],
    )
    try:
        response = _chat_completions_with_model_fallback(
            client,
            rec_models,
            messages=[
                {"role": "system", "content": "Ты Agile-коуч для команд обеспечения поставки и платформенных команд. Приоритет — сокращение Lead Time и T2M. Команда уже в Scrum; улучшения по слабым темам оценки. Исполнимые шаги; англотермины с русскими пояснениями в скобках при первом упоминании."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=3500,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        parsed = _safe_json_object(raw)
        plan = _normalize_group_plan(parsed)
        plan_is_empty = (
            not plan.get("diagnosis")
            and not plan.get("initiatives")
            and not plan.get("roadmap")
            and not plan.get("risks")
        )
        if plan_is_empty:
            fallback = (raw or "").strip()
            content = fallback if fallback.startswith("<") else f"<p>{fallback}</p>"
        else:
            content = _group_plan_to_html(session.team_name or "Команда", plan)
            session.recommendations_plan_json = plan
        session.recommendations_html = content or ''
        db.session.commit()
        return jsonify({
            "content": content,
            "plan": _normalize_group_plan(session.recommendations_plan_json),
        })
    except Exception as e:
        return _openai_http_response(e)


@maturity_bp.route('/api/maturity/<token>/recommendations/dont-know', methods=['GET'])
def get_saved_maturity_recommendations_dont_know(token):
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        return jsonify({'error': 'Ссылка не найдена'}), 404
    return jsonify({
        "content": session.dont_know_recommendations_html or '',
        "plan": _normalize_group_plan(session.dont_know_recommendations_plan_json),
    })


@maturity_bp.route('/api/maturity/<token>/recommendations/dont-know', methods=['PUT'])
def save_maturity_recommendations_dont_know(token):
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        return jsonify({'error': 'Ссылка не найдена'}), 404
    data = request.get_json() or {}
    plan = _normalize_group_plan(data.get("plan"))
    html = str(data.get("content") or "").strip() or _group_plan_to_html(
        f"{session.team_name or 'Команда'} — ответы «Не знаю»",
        plan,
    )
    session.dont_know_recommendations_plan_json = plan
    session.dont_know_recommendations_html = html
    db.session.commit()
    return jsonify({
        "success": True,
        "content": session.dont_know_recommendations_html or '',
        "plan": _normalize_group_plan(session.dont_know_recommendations_plan_json),
    })


@maturity_bp.route('/api/maturity/<token>/recommendations/dont-know', methods=['POST'])
def get_maturity_recommendations_dont_know(token):
    """Рекомендации по вопросам, где команда ответила «не знаю» — фокус на следующий квартал."""
    import os
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        return jsonify({'error': 'Ссылка не найдена'}), 404
    if not session.completed_at or not session.answers:
        return jsonify({'error': 'Оценка ещё не пройдена'}), 400
    if not os.getenv('OPENAI_API_KEY'):
        return jsonify({'error': 'Сервис рекомендаций не настроен (OPENAI_API_KEY)'}), 503

    raw_ans, _ = _extract_answers_and_comments(session.answers)
    normalized = _normalize_stored_answers_row(raw_ans)
    if not normalized:
        return jsonify({'error': 'Некорректные данные ответов'}), 400

    lines = []
    for i, q in enumerate(MATURITY_QUESTIONS):
        if normalized[i] == 'dont_know':
            lines.append(f"- Вопрос {i + 1} ({q.get('theme', '')}): {q.get('text', '')}")

    if not lines:
        content = '<p>Нет ответов «не знаю» — блок не требуется.</p>'
        session.dont_know_recommendations_html = content
        db.session.commit()
        return jsonify({'content': content})

    topics = "\n".join(lines)
    client = _openai_client()
    prompt = f"""Команда прошла оценку зрелости и на перечисленные ниже утверждения ответила «не знаю» (нет уверенности, есть ли это у них).

Утверждения:
{topics}

Контекст: команда **уже в каком-то виде живёт в Scrum**; «не знаю» значит неуверенность в **качестве/наличии практики**, а не отсутствие Scrum целиком. Не предлагай «первую ретро/первый дейли» — предлагай **прояснение и аудит**: что уже делается, как проверить, как зафиксировать договорённости.

Тип команд: в первую очередь **обеспечение поставки / платформа / внутренние сервисы**; примеры прояснения — как это влияет на **Lead Time** и **T2M** для внутренних потребителей. Минимум 3 из 5 инициатив: в `business_impact` теги **[Lead Time]** и/или **[T2M]**. Англотермины при первом упоминании — с кратким русским пояснением в скобках.

Дай практичные советы на **следующий квартал**: что сделать, чтобы команда **поняла**, есть ли это у них (короткие проверки, вопросы на существующих ретро, лёгкий опрос, наблюдение за потоком, выборка артефактов и т.д.).
Ровно 5 инициатив (не больше и не меньше). В каждой инициативе steps: 5–7 исполнимых шагов (глагол + артефакт/канал + срок/частота + роль), без размытых формулировок.
business_impact: начни с 1–2 тегов из [T2M], [Lead Time], [Гибкость приоритетов], [Предсказуемость поставки], [Cost-to-serve], [Качество/дефектность], [Удержание/NPS] и кратко опиши, зачем бизнесу прояснять эту практику (без выдуманных цифр).
success_metric: как поймёте, что неопределённость снята (измеримый сигнал за 2–6 недель).
customer_impact: что получит заказчик, когда команда прояснит практику.
Упор на прикладные изменения в процессах, без абстракций про мировоззрение/ценности.
Не предлагай ротацию ролей PO/DPO и любые перестановки PO/DPO.
Верни ТОЛЬКО JSON (без markdown) в структуре:
{{
  "diagnosis": "2-4 предложения",
  "initiatives": [
    {{
      "title": "...",
      "objective": "...",
      "owner": "...",
      "success_metric": "...",
      "business_impact": "...",
      "customer_impact": "...",
      "steps": ["5–7 исполнимых шагов по правилам выше"]
    }}
  ],
  "roadmap": [
    {{
      "period": "Недели 1-2",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "initiative": "...",
      "milestone": "..."
    }}
  ],
  "risks": ["..."]
}}
Ответ по-русски; при необходимости допустимы англоязычные термины с кратким русским пояснением в скобках при первом упоминании."""

    try:
        response = _chat_completions_with_model_fallback(
            client,
            _maturity_plan_model_chain("MATURITY_TEAM_PLAN_MODEL"),
            messages=[
                {"role": "system", "content": "Ты Agile-коуч для команд обеспечения поставки и платформы. Проясняешь «не знаю» с прицелом на Lead Time и T2M для внутренних заказчиков. Англотермины — с русскими пояснениями в скобках."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.55,
            max_tokens=3500,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        parsed = _safe_json_object(raw)
        plan = _normalize_group_plan(parsed)
        plan_is_empty = (
            not plan.get("diagnosis")
            and not plan.get("initiatives")
            and not plan.get("roadmap")
            and not plan.get("risks")
        )
        if plan_is_empty:
            fallback = (raw or "").strip()
            content = fallback if fallback.startswith("<") else f"<p>{fallback}</p>"
        else:
            content = _group_plan_to_html(f"{session.team_name or 'Команда'} — ответы «Не знаю»", plan)
            session.dont_know_recommendations_plan_json = plan
        session.dont_know_recommendations_html = content or ''
        db.session.commit()
        return jsonify({
            "content": content,
            "plan": _normalize_group_plan(session.dont_know_recommendations_plan_json),
        })
    except Exception as e:
        return _openai_http_response(e)


@maturity_bp.route('/api/maturity/<token>/clarify', methods=['POST'])
def clarify_question(token):
    """Разъяснение вопроса нейросетью с примерами для банковской сферы (продуктовые, платформенные, сервисные команды)."""
    import os
    data = request.get_json() or {}
    lang_raw = str(data.get('lang') or '').strip().lower()
    lang = 'en' if lang_raw == 'en' else 'ru'
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        err = 'Link not found' if lang == 'en' else 'Ссылка не найдена'
        return jsonify({'error': err}), 404
    if not os.getenv('OPENAI_API_KEY'):
        err = 'Explanations service is not configured (OPENAI_API_KEY)' if lang == 'en' else 'Сервис разъяснений не настроен (OPENAI_API_KEY)'
        return jsonify({'error': err}), 503
    question_text = data.get('question_text', '').strip() or data.get('text', '').strip()
    if not question_text:
        err = 'Provide question_text' if lang == 'en' else 'Укажите question_text'
        return jsonify({'error': err}), 400
    client = _openai_client()
    if lang == 'en':
        prompt = f"""Explain what this team maturity assessment statement means. Give concrete examples from banking for three team types:
1) product teams (client-facing products — cards, loans, apps);
2) platform teams (internal platforms, API, infrastructure);
3) service teams (support, operations, services for internal stakeholders).

Statement: «{question_text}»

Answer briefly in English with 1–2 examples per team type where appropriate."""
        system_msg = (
            "You are an expert in Agile and banking delivery. You explain maturity assessment items with examples from banks "
            "(Citibank, Deutsche Bank, etc.)."
        )
    else:
        prompt = f"""Разъясни, что имеется в виду в этом утверждении оценки зрелости команды. Приведи конкретные примеры в банковской сфере для трёх типов команд:
1) продуктовые команды (разработка продуктов для клиентов — карты, кредиты, приложения);
2) платформенные команды (внутренние платформы, API, инфраструктура);
3) сервисные команды (поддержка, операции, сервисы для внутренних заказчиков).

Утверждение: «{question_text}»

Ответ дай кратко, по-русски, с 1–2 примерами на каждый тип команды где уместно."""
        system_msg = "Ты эксперт по Agile и банковской разработке. Разъясняешь вопросы оценки зрелости с примерами из банков (Citibank, Deutsche Bank и др.)."
    try:
        response = _chat_completions_with_model_fallback(
            client,
            _openai_chat_model_list("MATURITY_TEAM_PLAN_MODEL", "gpt-4.1"),
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=800,
        )
        content = response.choices[0].message.content
        return jsonify({"content": content})
    except Exception as e:
        return _openai_http_response(e)


@maturity_bp.route('/api/metrics-tree/explain', methods=['POST'])
def metrics_tree_explain():
    import os
    data = request.get_json() or {}
    lang_raw = str(data.get('lang') or '').strip().lower()
    lang = 'en' if lang_raw == 'en' else 'ru'
    if not os.getenv('OPENAI_API_KEY'):
        err = 'Explanations service is not configured (OPENAI_API_KEY)' if lang == 'en' else 'Сервис разъяснений не настроен (OPENAI_API_KEY)'
        return jsonify({'error': err}), 503
    survey_token = data.get('survey_token')
    if not _metrics_tree_access_allowed(survey_token=survey_token):
        err = 'Access denied' if lang == 'en' else 'Доступ запрещён'
        return jsonify({'error': err}), 403
    metric_key = str(data.get('metric_key') or '').strip()
    metric_name = str(data.get('metric_name') or '').strip()
    metric_name_ru = str(data.get('metric_name_ru') or '').strip()
    if not metric_key and not metric_name:
        err = 'Provide metric_key or metric_name' if lang == 'en' else 'Укажите metric_key или metric_name'
        return jsonify({'error': err}), 400

    client = _openai_client()
    metric_title = f"{metric_name} ({metric_name_ru})" if metric_name_ru else metric_name
    if lang == 'en':
        prompt = f"""Explain this metric in plain language for a product team.

Metric: {metric_title}
Key: {metric_key or 'n/a'}

Give a structured answer in English:
1) What it measures;
2) Why it matters for profit/revenue/cost;
3) How it is usually measured (formula or practical approach);
4) What team actions affect it in the next 2–4 weeks.
Be concise and practical."""
        system_msg = "You are an Agile/Product consultant. You give precise, practical metric explanations."
    else:
        prompt = f"""Объясни метрику простым языком для продуктовой команды.

Метрика: {metric_title}
Ключ: {metric_key or 'n/a'}

Дай структурированный ответ на русском:
1) Что измеряет;
2) Почему важна для прибыли/выручки/затрат;
3) Как обычно измеряют (формула или практичный способ);
4) Какие действия команды влияют на метрику в ближайшие 2-4 недели.
Кратко, по делу, без воды."""
        system_msg = "Ты Agile/Product консультант. Даешь точные прикладные разъяснения метрик."
    try:
        response = _chat_completions_with_model_fallback(
            client,
            _openai_chat_model_list("METRICS_TREE_MODEL", "gpt-4.1"),
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ],
            temperature=0.35,
            max_tokens=900,
        )
        content = response.choices[0].message.content
        return jsonify({"content": content})
    except Exception as e:
        return _openai_http_response(e)


@maturity_bp.route('/api/metrics-tree/relationship', methods=['POST'])
def metrics_tree_relationship():
    import os
    data = request.get_json() or {}
    lang_raw = str(data.get('lang') or '').strip().lower()
    lang = 'en' if lang_raw == 'en' else 'ru'
    if not os.getenv('OPENAI_API_KEY'):
        err = 'Explanations service is not configured (OPENAI_API_KEY)' if lang == 'en' else 'Сервис разъяснений не настроен (OPENAI_API_KEY)'
        return jsonify({'error': err}), 503
    survey_token = data.get('survey_token')
    if not _metrics_tree_access_allowed(survey_token=survey_token):
        err = 'Access denied' if lang == 'en' else 'Доступ запрещён'
        return jsonify({'error': err}), 403

    metric_a_name = str(data.get('metric_a_name') or '').strip()
    metric_a_name_ru = str(data.get('metric_a_name_ru') or '').strip()
    metric_b_name = str(data.get('metric_b_name') or '').strip()
    metric_b_name_ru = str(data.get('metric_b_name_ru') or '').strip()
    if not metric_a_name or not metric_b_name:
        err = 'Provide metric_a_name and metric_b_name' if lang == 'en' else 'Укажите metric_a_name и metric_b_name'
        return jsonify({'error': err}), 400

    client = _openai_client()
    def _classify_metric(metric_key, metric_name_text):
        key = (metric_key or "").lower()
        name_text = (metric_name_text or "").lower()
        business_tokens = [
            "profit", "revenue", "cost", "costs", "выруч", "прибыл", "затрат", "retention rate", "sessions per user",
            "feature adoption", "engagement", "retention", "acquisition", "activation"
        ]
        agile_delivery_tokens = [
            "lead time", "cycle time", "wip", "blocked", "flow efficiency", "queue time",
            "deployment frequency", "throughput", "velocity", "team maturity", "process maturity",
            "engineering practices", "code review", "test coverage", "ci/cd", "mttr",
            "change failure rate", "bug escape", "defect rate", "rework", "tech debt", "time-to-market", "t2m"
        ]
        if any(t in key or t in name_text for t in business_tokens):
            return "business"
        if any(t in key or t in name_text for t in agile_delivery_tokens):
            return "agile_delivery"
        return "unknown"

    class_a = _classify_metric(data.get('metric_a_key'), f"{metric_a_name} {metric_a_name_ru}")
    class_b = _classify_metric(data.get('metric_b_key'), f"{metric_b_name} {metric_b_name_ru}")

    a_title = f"{metric_a_name} ({metric_a_name_ru})" if metric_a_name_ru else metric_a_name
    b_title = f"{metric_b_name} ({metric_b_name_ru})" if metric_b_name_ru else metric_b_name

    # Если пара "agile/delivery" + "business", оставляем только осмысленное направление.
    if lang == "en":
        if class_a == "agile_delivery" and class_b == "business":
            direction_rules = f"""For this pair, cover only the direction from Agile/Delivery to Business:
- Required section "A -> B" (how {a_title} affects {b_title}).
- Do not add section "B -> A".
"""
        elif class_b == "agile_delivery" and class_a == "business":
            direction_rules = f"""For this pair, cover only the direction from Agile/Delivery to Business:
- Required section "B -> A" (how {b_title} affects {a_title}).
- Do not add section "A -> B".
"""
        else:
            direction_rules = """Show influence both ways: "A -> B" and "B -> A"."""

        prompt = f"""Explain the relationship between two metrics in product development.

Metric A: {a_title}
Metric B: {b_title}
Class A: {class_a}
Class B: {class_b}

{direction_rules}

Answer in English:
1) For each required direction, describe the causal link and mechanism;
2) State effect lag (fast/medium/slow) for each required direction;
3) Name 2-3 intermediate operational metrics through which the effect shows up;
4) Give a practical trade-off example and how to control it;
5) What to monitor weekly so the target metric does not degrade.

Output format:
- only the sections required by the direction rules above;
- plus "Intermediate metrics", "Trade-off", "Weekly monitoring".
Be concise and practical."""
        system_msg = "You are an Agile/Engineering expert on flow and product system metrics."
    else:
        if class_a == "agile_delivery" and class_b == "business":
            direction_rules = f"""В этой паре давай только направление из Agile/Delivery в Business:
- Обязательно раздел "A -> B" (как {a_title} влияет на {b_title}).
- Не добавляй раздел "B -> A".
"""
        elif class_b == "agile_delivery" and class_a == "business":
            direction_rules = f"""В этой паре давай только направление из Agile/Delivery в Business:
- Обязательно раздел "B -> A" (как {b_title} влияет на {a_title}).
- Не добавляй раздел "A -> B".
"""
        else:
            direction_rules = """Покажи влияние в обе стороны: "A -> B" и "B -> A"."""

        prompt = f"""Объясни связь между двумя метриками в продуктовой разработке.

Метрика A: {a_title}
Метрика B: {b_title}
Класс A: {class_a}
Класс B: {class_b}

{direction_rules}

Ответ на русском:
1) Для каждого требуемого направления укажи причинно-следственную связь и механизм влияния;
2) Укажи лаг эффекта (быстрый/средний/долгий) для каждого требуемого направления;
3) Через какие 2-3 промежуточные операционные метрики проявляется влияние;
4) Пример практического trade-off и как его контролировать;
5) Что мониторить еженедельно, чтобы не ухудшить целевую метрику.

Формат ответа:
- только обязательные разделы по правилу направлений выше;
- плюс "Промежуточные метрики", "Trade-off", "Еженедельный контроль".
Кратко и прикладно, без воды."""
        system_msg = "Ты Agile/Engineering эксперт по системным метрикам потока и продукта."
    try:
        response = _chat_completions_with_model_fallback(
            client,
            _openai_chat_model_list("METRICS_TREE_MODEL", "gpt-4.1"),
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ],
            temperature=0.35,
            max_tokens=1000,
        )
        content = response.choices[0].message.content
        return jsonify({"content": content})
    except Exception as e:
        return _openai_http_response(e)


@maturity_bp.route('/api/maturity-admin/overview', methods=['GET'])
@jwt_required()
def maturity_admin_overview():
    user = _get_maturity_admin_user()
    if not user:
        return jsonify({'error': 'Доступ запрещён'}), 403
    _ensure_maturity_link_session_columns()
    selected_group = _normalize_group_name(request.args.get('group_name'))
    rows = MaturityLinkSession.query.order_by(MaturityLinkSession.created_at.desc()).all()
    if selected_group:
        rows = [r for r in rows if _normalize_group_name(getattr(r, "group_name", None)) == selected_group]
    groups = sorted({(_normalize_group_name(getattr(s, "group_name", None)) or "Без группы") for s in MaturityLinkSession.query.all()})
    return jsonify({
        'selected_group': selected_group,
        'groups': groups,
        'sessions': [
            {
                'id': s.id,
                'team_name': s.team_name,
                'group_name': _normalize_group_name(getattr(s, 'group_name', None)),
                'token': s.access_token,
                'token_suffix': s.access_token[-8:] if s.access_token else '',
                'created_at': s.created_at.isoformat() if s.created_at else None,
                'completed_at': s.completed_at.isoformat() if s.completed_at else None,
                'completed': s.completed_at is not None,
            }
            for s in rows
        ]
    })


@maturity_bp.route('/api/maturity-admin/session/<int:session_id>/group', methods=['PUT'])
@jwt_required()
def maturity_admin_update_group(session_id):
    user = _get_maturity_admin_user()
    if not user:
        return jsonify({'error': 'Доступ запрещён'}), 403
    _ensure_maturity_link_session_columns()
    s = MaturityLinkSession.query.get(session_id)
    if not s:
        return jsonify({'error': 'Сессия не найдена'}), 404
    data = request.get_json() or {}
    s.group_name = _normalize_group_name(data.get('group_name'))
    db.session.commit()
    return jsonify({
        'id': s.id,
        'group_name': s.group_name,
    })


@maturity_bp.route('/api/maturity-admin/session/<int:session_id>', methods=['DELETE'])
@jwt_required()
def maturity_admin_delete_session(session_id):
    user = _get_maturity_admin_user()
    if not user:
        return jsonify({'error': 'Доступ запрещён'}), 403
    s = MaturityLinkSession.query.get(session_id)
    if not s:
        return jsonify({'error': 'Сессия не найдена'}), 404
    db.session.delete(s)
    db.session.commit()
    return jsonify({'message': 'Удалено'})


@maturity_bp.route('/api/maturity-admin/aggregates', methods=['GET'])
@jwt_required()
def maturity_admin_aggregates():
    user = _get_maturity_admin_user()
    if not user:
        return jsonify({'error': 'Доступ запрещён'}), 403
    _ensure_maturity_link_session_columns()
    selected_group = _normalize_group_name(request.args.get('group_name'))
    completed = MaturityLinkSession.query.filter(MaturityLinkSession.completed_at.isnot(None)).all()
    if selected_group:
        completed = [s for s in completed if _normalize_group_name(getattr(s, "group_name", None)) == selected_group]
    _agg_keys = ("yes", "rather_yes", "no", "rather_no", "dont_know")

    def _empty_counts():
        return {k: 0 for k in _agg_keys}

    counts = [_empty_counts() for _ in range(QUESTIONS_COUNT)]
    valid_sessions = 0
    by_group = defaultdict(lambda: {"sessions": 0, **_empty_counts()})
    for s in completed:
        raw_ans, _ = _extract_answers_and_comments(s.answers)
        row = _normalize_stored_answers_row(raw_ans) if raw_ans else None
        if not row:
            continue
        valid_sessions += 1
        gname = _normalize_group_name(getattr(s, "group_name", None)) or "Без группы"
        by_group[gname]["sessions"] += 1
        for i, a in enumerate(row):
            if a == "yes":
                counts[i]["yes"] += 1
                by_group[gname]["yes"] += 1
            elif a == "rather_yes":
                counts[i]["rather_yes"] += 1
                by_group[gname]["rather_yes"] += 1
            elif a == "no":
                counts[i]["no"] += 1
                by_group[gname]["no"] += 1
            elif a == "rather_no":
                counts[i]["rather_no"] += 1
                by_group[gname]["rather_no"] += 1
            else:
                counts[i]["dont_know"] += 1
                by_group[gname]["dont_know"] += 1

    questions_out = []
    for i in range(QUESTIONS_COUNT):
        c = counts[i]
        t = sum(c[k] for k in _agg_keys)
        base = {
            "index": i,
            "theme": MATURITY_QUESTIONS[i]["theme"],
            "short_text": (MATURITY_QUESTIONS[i]["text"][:80] + "…") if len(MATURITY_QUESTIONS[i]["text"]) > 80 else MATURITY_QUESTIONS[i]["text"],
            "counts": c,
        }
        if t <= 0:
            questions_out.append({
                **base,
                "yes_pct": 0.0,
                "rather_yes_pct": 0.0,
                "no_pct": 0.0,
                "rather_no_pct": 0.0,
                "dont_know_pct": 0.0,
            })
        else:
            questions_out.append({
                **base,
                "yes_pct": round(100.0 * c["yes"] / t, 1),
                "rather_yes_pct": round(100.0 * c["rather_yes"] / t, 1),
                "no_pct": round(100.0 * c["no"] / t, 1),
                "rather_no_pct": round(100.0 * c["rather_no"] / t, 1),
                "dont_know_pct": round(100.0 * c["dont_know"] / t, 1),
            })

    return jsonify({
        "selected_group": selected_group,
        "completed_sessions": valid_sessions,
        "group_summaries": [
            {
                "group_name": g,
                "sessions": v["sessions"],
                "yes": v["yes"],
                "rather_yes": v["rather_yes"],
                "no": v["no"],
                "rather_no": v["rather_no"],
                "dont_know": v["dont_know"],
            }
            for g, v in sorted(by_group.items(), key=lambda item: item[0].lower())
        ],
        "questions": questions_out,
    })


@maturity_bp.route('/api/maturity-admin/insights', methods=['GET'])
@jwt_required()
def maturity_admin_insights():
    """Короткая сводка по агрегатам через OpenAI (опционально)."""
    import os
    user = _get_maturity_admin_user()
    if not user:
        return jsonify({'error': 'Доступ запрещён'}), 403
    _ensure_maturity_link_session_columns()
    selected_group = _normalize_group_name(request.args.get('group_name'))
    if not os.getenv('OPENAI_API_KEY'):
        return jsonify({'error': 'OPENAI_API_KEY не задан'}), 503

    completed = MaturityLinkSession.query.filter(MaturityLinkSession.completed_at.isnot(None)).all()
    if selected_group:
        completed = [s for s in completed if _normalize_group_name(getattr(s, "group_name", None)) == selected_group]
    theme_yes = {}
    theme_rather_yes = {}
    theme_score_sum = defaultdict(float)
    theme_n = {}
    for s in completed:
        raw_ans, _ = _extract_answers_and_comments(s.answers)
        row = _normalize_stored_answers_row(raw_ans) if raw_ans else None
        if not row:
            continue
        for i, q in enumerate(MATURITY_QUESTIONS):
            th = q["theme"]
            theme_n[th] = theme_n.get(th, 0) + 1
            cell = row[i]
            if cell == "yes":
                theme_yes[th] = theme_yes.get(th, 0) + 1
            if cell == "rather_yes":
                theme_rather_yes[th] = theme_rather_yes.get(th, 0) + 1
            theme_score_sum[th] += MATURITY_ANSWER_SCORE.get(cell, 0.0)

    lines = []
    for th in sorted(theme_n.keys()):
        n = theme_n[th]
        y = theme_yes.get(th, 0)
        ry = theme_rather_yes.get(th, 0)
        pct = round(100.0 * y / n, 1) if n else 0
        avg = round(theme_score_sum[th] / n, 2) if n else 0.0
        lines.append(f"- {th}: «да» {y}/{n} ({pct}%), «скорее да» {ry}/{n}, средний балл за ответ {avg}/1")

    if not lines:
        return jsonify({"content": "<p>Нет завершённых оценок для сводки.</p>"})

    summary = "\n".join(lines)
    client = _openai_client()
    prompt = f"""По агрегированным данным оценок зрелости (число «да», «скорее да» и средний балл 0–1 за ответ по темам) дай краткий executive summary.

Сводка:
{summary}

Требования:
- Только факты из сводки, без выдуманных цифр.
- Укажи 2-3 самые перспективные зоны экспериментов с фокусом на бизнес-эффект и ускорение T2M/Lead Time.
- Для каждой зоны дай один короткий «следующий эксперимент» на 1-2 недели.
- Избегай абстрактных рекомендаций про ценности/майндсет/мировоззрение, если нет конкретного операционного шага.
- Не предлагай ротацию ролей PO/DPO и любые перестановки PO/DPO.
- Добавь блок «Инструменты GrowBoard» с 2-4 ссылками:
  <a href="/new/agile-tools">Название инструмента (поиск в Agile Tools)</a>
  Используй только релевантные инструменты.

Ответ: кратко, по-русски, HTML (<p>, <strong>, <ul>, <li>, <a>)."""

    try:
        response = _chat_completions_with_model_fallback(
            client,
            _openai_chat_model_list("MATURITY_ADMIN_INSIGHTS_MODEL", "gpt-4.1"),
            messages=[
                {"role": "system", "content": "Ты Agile-коуч. Интерпретируешь только переданные агрегаты."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=600,
        )
        content = response.choices[0].message.content
        return jsonify({"content": content})
    except Exception as e:
        return _openai_http_response(e)


@maturity_bp.route('/api/maturity-admin/group-plan', methods=['GET'])
@jwt_required()
def maturity_admin_group_plan_get():
    user = _get_maturity_admin_user()
    if not user:
        return jsonify({'error': 'Доступ запрещён'}), 403
    _ensure_group_plan_table()
    group_name = _normalize_group_name(request.args.get("group_name"))
    if not group_name:
        return jsonify({'error': 'Укажите group_name'}), 400
    row = MaturityGroupPlan.query.filter_by(group_name=group_name).first()
    if not row:
        return jsonify({"group_name": group_name, "plan": _default_group_plan(), "content": "", "updated_at": None})
    return jsonify({
        "group_name": group_name,
        "plan": _normalize_group_plan(row.plan_json),
        "content": row.plan_html or "",
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    })


@maturity_bp.route('/api/maturity-admin/group-plan', methods=['PUT'])
@jwt_required()
def maturity_admin_group_plan_save():
    user = _get_maturity_admin_user()
    if not user:
        return jsonify({'error': 'Доступ запрещён'}), 403
    _ensure_group_plan_table()
    data = request.get_json() or {}
    group_name = _normalize_group_name(data.get("group_name"))
    if not group_name:
        return jsonify({'error': 'Укажите group_name'}), 400
    plan = _normalize_group_plan(data.get("plan"))
    html = str(data.get("content") or "").strip() or _group_plan_to_html(group_name, plan)
    row = MaturityGroupPlan.query.filter_by(group_name=group_name).first()
    if not row:
        row = MaturityGroupPlan(group_name=group_name, plan_json=plan, plan_html=html, updated_by_user_id=user.id)
        db.session.add(row)
    else:
        row.plan_json = plan
        row.plan_html = html
        row.updated_by_user_id = user.id
    db.session.commit()
    return jsonify({
        "group_name": group_name,
        "plan": plan,
        "content": row.plan_html,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    })


@maturity_bp.route('/api/maturity-admin/group-plan', methods=['POST'])
@jwt_required()
def maturity_admin_group_plan_generate():
    """Сгенерировать план улучшений для группы команд (стрима)."""
    import os
    user = _get_maturity_admin_user()
    if not user:
        return jsonify({'error': 'Доступ запрещён'}), 403
    _ensure_maturity_link_session_columns()
    _ensure_group_plan_table()
    if not os.getenv('OPENAI_API_KEY'):
        return jsonify({'error': 'OPENAI_API_KEY не задан'}), 503

    data = request.get_json() or {}
    group_name = _normalize_group_name(data.get("group_name"))
    if not group_name:
        return jsonify({'error': 'Укажите group_name'}), 400

    completed = MaturityLinkSession.query.filter(MaturityLinkSession.completed_at.isnot(None)).all()
    completed = [s for s in completed if _normalize_group_name(getattr(s, "group_name", None)) == group_name]
    if not completed:
        return jsonify({'error': 'Нет завершённых оценок для выбранной группы'}), 400

    theme_yes = {}
    theme_rather_yes = {}
    theme_score_sum = defaultdict(float)
    theme_n = {}
    for s in completed:
        raw_ans, _ = _extract_answers_and_comments(s.answers)
        row = _normalize_stored_answers_row(raw_ans) if raw_ans else None
        if not row:
            continue
        for i, q in enumerate(MATURITY_QUESTIONS):
            th = q["theme"]
            theme_n[th] = theme_n.get(th, 0) + 1
            cell = row[i]
            if cell == "yes":
                theme_yes[th] = theme_yes.get(th, 0) + 1
            if cell == "rather_yes":
                theme_rather_yes[th] = theme_rather_yes.get(th, 0) + 1
            theme_score_sum[th] += MATURITY_ANSWER_SCORE.get(cell, 0.0)

    if not theme_n:
        return jsonify({'error': 'Недостаточно валидных данных по группе'}), 400

    theme_rows = []
    for th in sorted(theme_n.keys()):
        n = theme_n[th]
        y = theme_yes.get(th, 0)
        ry = theme_rather_yes.get(th, 0)
        pct = round(100.0 * y / n, 1) if n else 0.0
        avg = round(theme_score_sum[th] / n, 2) if n else 0.0
        theme_rows.append({"theme": th, "yes": y, "rather_yes": ry, "total": n, "yes_pct": pct, "avg_score": avg})
    summary = "\n".join([
        f"- {r['theme']}: да {r['yes']}/{r['total']} ({r['yes_pct']}%), скорее да {r['rather_yes']}/{r['total']}, средний балл {r['avg_score']}/1"
        for r in theme_rows
    ])

    client = _openai_client()
    tools_hint = ", ".join(AGILE_TOOLS_LINKS)
    prompt = f"""Ты Agile transformation lead. Нужно подготовить план улучшений для стрима команд по агрегированной зрелости.

Группа команд: {group_name}
Завершённых оценок: {len(completed)}
Сводка по темам:
{summary}

Контекст (обязательно):
- Команды стрима **уже работают в Scrum** (возможно неаккуратно); это не массовое внедрение с нуля.
- **Не предлагай** инициативы уровня «впервые ввести ретро/стендап/планирование/бэклог для всех». Фокус — **выравнивание и улучшение** практик по темам, где в сводке **низкая доля «да» и средний балл** (явно опирайся на названия тем из сводки в diagnosis и в названиях инициатив).
- План стрима = типовые дыры по данным агрегата, а не учебник Scrum для новичков.

Тип команд стрима:
- В основном команды **обеспечения поставки** и **платформенные/сервисные** (внутренние заказчики, enablement). Инициативы стрима — про сокращение **Lead Time** и **T2M** на стыках команд, очереди, пайплайны, а не только про продуктовые фичи для конечного клиента.
- Минимум **3 из 5** инициатив: в `business_impact` теги **[Lead Time]** и/или **[T2M]**.
- Англоязычные термины при первом упоминании сопровождай **кратким русским пояснением в скобках**.

Верни ТОЛЬКО JSON без markdown и без пояснений в следующей структуре:
{{
  "diagnosis": "2-4 предложения",
  "initiatives": [
    {{
      "title": "...",
      "objective": "...",
      "owner": "...",
      "success_metric": "...",
      "business_impact": "...",
      "customer_impact": "...",
      "steps": ["5–7 исполнимых шагов по правилам выше"]
    }}
  ],
  "roadmap": [
    {{
      "period": "Недели 1-2",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "initiative": "...",
      "milestone": "..."
    }}
  ],
  "risks": ["..."]
}}
Условия:
- Ровно 5 инициатив уровня стрима (не больше и не меньше).
- Roadmap на 12 недель с конкретными вехами.
- В каждой инициативе steps: 5–7 исполнимых шагов (глагол + объект/артефакт + срок или частота + роль ответственного). Запрещены размытые формулировки без места, времени и результата.
- objective и owner: чётко и на уровне стрима (роль/функция, не ФИО).
- success_metric: «база → цель за 2–4 недели» или явный порог; связь с T2M, Lead Time или бизнес-метрикой. Не выдумывай числа вне переданной сводки.
- business_impact: начни с 1–2 тегов из [T2M], [Lead Time], [Гибкость приоритетов], [Предсказуемость поставки], [Cost-to-serve], [Качество/дефектность], [Удержание/NPS], затем кратко — что получит бизнес от инициативы стрима.
- customer_impact: эффект для клиента/внутреннего заказчика, согласованный с business_impact.
- Для каждой инициативы заложи быстрый эксперимент 1–2 недели в первых шагах steps.
- Приоритизируй по эффекту на **Lead Time** и **T2M** в первую очередь, затем прочие бизнес-метрики (типы связи, без выдуманных цифр).
- Избегай абстракций про мировоззрение, ценности, культуру без артефактов и действий.
- Не предлагай ротацию ролей PO/DPO и любые перестановки PO/DPO.
- В конец diagnosis добавь блок «Рекомендуемые инструменты GrowBoard» с 3-5 ссылками HTML на Agile Tools:
  <a href="/new/agile-tools">Название инструмента</a>.
  Выбирай только релевантные инструменты из списка: {tools_hint}.
- Пиши по-русски; при необходимости допустимы англоязычные термины с кратким русским пояснением в скобках при первом упоминании.
- Не выдумывай числа вне переданной сводки.
"""
    try:
        response = _chat_completions_with_model_fallback(
            client,
            _maturity_plan_model_chain("MATURITY_GROUP_PLAN_MODEL"),
            messages=[
                {"role": "system", "content": "Ты практик трансформаций в enterprise. Стрим — в основном enablement и обеспечение поставки; приоритет Lead Time и T2M. План по слабым темам данных. Исполнимые шаги; англотермины с русскими пояснениями в скобках."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.45,
            max_tokens=3500,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        parsed = _safe_json_object(raw)
        plan = _normalize_group_plan(parsed)
        content = _group_plan_to_html(group_name, plan)

        row = MaturityGroupPlan.query.filter_by(group_name=group_name).first()
        if not row:
            row = MaturityGroupPlan(group_name=group_name, plan_json=plan, plan_html=content, updated_by_user_id=user.id)
            db.session.add(row)
        else:
            row.plan_json = plan
            row.plan_html = content
            row.updated_by_user_id = user.id
        db.session.commit()
        return jsonify({
            "group_name": group_name,
            "sessions": len(completed),
            "themes": theme_rows,
            "plan": plan,
            "content": content,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        })
    except Exception as e:
        return _openai_http_response(e)
