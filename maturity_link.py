# Оценка зрелости по ссылке: создание сессии, прохождение (да/нет/не знаю), результаты для радара и PDF.
import os
import uuid
from datetime import datetime
from collections import defaultdict

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
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

maturity_bp = Blueprint('maturity_link', __name__)

QUESTIONS_COUNT = len(MATURITY_QUESTIONS)
QUESTIONS_PER_THEME = 3

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


def _parse_submitted_answer(a):
    """Один элемент ответа из JSON: True / False / 'dont_know'."""
    if a is True:
        return True
    if a is False:
        return False
    if isinstance(a, str):
        key = a.strip().lower().replace(' ', '_')
        if key == 'dont_know':
            return 'dont_know'
    return None


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
    """Привести значение из БД к True / False / 'dont_know'."""
    if a is True:
        return True
    if a is False:
        return False
    if isinstance(a, str):
        key = a.strip().lower().replace(' ', '_')
        if key == 'dont_know':
            return 'dont_know'
    if isinstance(a, bool):
        return a
    return False


def _normalize_stored_answers_row(raw_list):
    if not isinstance(raw_list, list) or len(raw_list) != QUESTIONS_COUNT:
        return None
    return [_normalize_stored_answer_cell(x) for x in raw_list]


def _results_from_answers(answers):
    """answers: list of True / False / 'dont_know'. Балл 5 только за True, иначе 0."""
    if not answers or len(answers) != QUESTIONS_COUNT:
        return {}
    results = {}
    for theme, indices in THEME_INDICES.items():
        results[theme] = {}
        for sub_one_based, q_idx in enumerate(indices[:QUESTIONS_PER_THEME], 1):
            a = answers[q_idx]
            score = 5.0 if a is True else 0.0
            results[theme][str(sub_one_based)] = score
    return results


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
            html.append(
                f"<li><strong>{idx}. {i['title'] or 'Инициатива'}</strong><br>"
                f"Цель: {i['objective'] or '—'}<br>"
                f"Владелец: {i['owner'] or '—'}<br>"
                f"Метрика успеха: {i['success_metric'] or '—'}<br>"
                f"Бизнес-эффект: {i['business_impact'] or '—'}<br>"
                f"Эффект для заказчиков: {i['customer_impact'] or '—'}</li>"
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
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        return jsonify({'error': 'Ссылка не найдена или недействительна'}), 404
    questions = [
        {
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
        for i, q in enumerate(MATURITY_QUESTIONS)
    ]
    return jsonify({
        'team_name': session.team_name,
        'group_name': session.group_name,
        'completed': session.completed_at is not None,
        'questions': questions,
        'business_metrics_disclaimer': BUSINESS_METRICS_DISCLAIMER,
        'business_metrics_glossary': BUSINESS_METRICS_GLOSSARY,
    })


@maturity_bp.route('/api/maturity/<token>/submit', methods=['POST'])
def submit_maturity_answers(token):
    """Публично: отправить ответы. Тело: answers — N элементов: true | false | \"dont_know\"."""
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
        return jsonify({'error': f'Нужен массив из {QUESTIONS_COUNT} ответов: true, false или \"dont_know\"'}), 400
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
        return jsonify({'error': f'Нужен массив из {QUESTIONS_COUNT} ответов: true, false или \"dont_know\"'}), 400
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
    """Публично: результаты для радара и PDF. answers: true / false / \"dont_know\"."""
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        return jsonify({'error': 'Ссылка не найдена'}), 404
    answers_list, comments_list = _extract_answers_and_comments(session.answers)
    if not session.completed_at or not answers_list:
        return jsonify({'error': 'Оценка ещё не пройдена'}), 400
    normalized = _normalize_stored_answers_row(answers_list)
    if not normalized:
        return jsonify({'error': 'Некорректные данные ответов'}), 400
    results = _results_from_answers(normalized)
    completed_at = session.completed_at.isoformat() if session.completed_at else None
    questions = [
        {
            'id': i,
            'theme': q['theme'],
            'text': q['text'],
            'why_important': q.get('why_important', ''),
            'metrics_impact': q.get('metrics_impact', ''),
            'negative_for_business': q.get('negative_for_business', ''),
            'business_metrics': q.get('business_metrics') or DEFAULT_BUSINESS_METRICS,
        }
        for i, q in enumerate(MATURITY_QUESTIONS)
    ]
    return jsonify({
        'team_name': session.team_name or 'Команда',
        'completed_at': completed_at,
        'results': results,
        'radar_groups': RADAR_GROUPS,
        'answers': normalized,
        'comments': comments_list or [None] * QUESTIONS_COUNT,
        'questions': questions,
        'business_metrics_disclaimer': BUSINESS_METRICS_DISCLAIMER,
        'business_metrics_glossary': BUSINESS_METRICS_GLOSSARY,
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
        avg = sum(vals) / len(vals) if vals else 0
        yes_count = sum(1 for v in vals if v >= 5)
        summary_lines.append(f"- {cat}: средний балл {avg:.1f}/5, ответов «да» {yes_count}/{len(vals)}")

    summary_text = "\n".join(summary_lines)
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    prompt = f"""Ты опытный Agile-коуч. По результатам оценки зрелости команды (да/нет по темам) дай конкретные рекомендации по улучшению.

Результаты по категориям (балл 0–5, где 5 = «да»):
{summary_text}

Требования:
- Сфокусируйся на категориях с низким баллом; для сильных сторон можно дать 1–2 совета по усилению.
- Рекомендации должны быть практичными: что сделать, к кому обратиться, какие форматы ввести.
- Используй короткие параграфы и при необходимости списки. Можно использовать HTML: <p>, <ul>, <li>, <strong>.
- Ответ только на русском."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты Agile-коуч. Дай структурированные рекомендации по улучшению зрелости команды на основе данных оценки."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=2000,
        )
        content = response.choices[0].message.content
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
        return jsonify({'content': '<p>Нет ответов «не знаю» — блок не требуется.</p>'})

    topics = "\n".join(lines)
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    prompt = f"""Команда прошла оценку зрелости и на перечисленные ниже утверждения ответила «не знаю» (нет уверенности, есть ли это у них).

Утверждения:
{topics}

Дай практичные советы на **следующий квартал**: что сделать, чтобы команда **поняла**, есть ли это у них (эксперименты, вопрос Scrum Master, наблюдение на ретро, короткий опрос, парные интервью и т.д.). Структура: HTML (<p>, <ul>, <li>, <strong>). Только русский язык."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты Agile-коуч. Помогаешь командам снять неопределённость по практикам зрелости."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.55,
            max_tokens=2000,
        )
        content = response.choices[0].message.content
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@maturity_bp.route('/api/maturity/<token>/clarify', methods=['POST'])
def clarify_question(token):
    """Разъяснение вопроса нейросетью с примерами для банковской сферы (продуктовые, платформенные, сервисные команды)."""
    import os
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        return jsonify({'error': 'Ссылка не найдена'}), 404
    if not os.getenv('OPENAI_API_KEY'):
        return jsonify({'error': 'Сервис разъяснений не настроен (OPENAI_API_KEY)'}), 503
    data = request.get_json() or {}
    question_text = data.get('question_text', '').strip() or data.get('text', '').strip()
    if not question_text:
        return jsonify({'error': 'Укажите question_text'}), 400
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    prompt = f"""Разъясни, что имеется в виду в этом утверждении оценки зрелости команды. Приведи конкретные примеры в банковской сфере для трёх типов команд:
1) продуктовые команды (разработка продуктов для клиентов — карты, кредиты, приложения);
2) платформенные команды (внутренние платформы, API, инфраструктура);
3) сервисные команды (поддержка, операции, сервисы для внутренних заказчиков).

Утверждение: «{question_text}»

Ответ дай кратко, по-русски, с 1–2 примерами на каждый тип команды где уместно."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по Agile и банковской разработке. Разъясняешь вопросы оценки зрелости с примерами из банков (Citibank, Deutsche Bank и др.)."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=800,
        )
        content = response.choices[0].message.content
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    counts = [{"yes": 0, "no": 0, "dont_know": 0} for _ in range(QUESTIONS_COUNT)]
    valid_sessions = 0
    by_group = defaultdict(lambda: {"sessions": 0, "yes": 0, "no": 0, "dont_know": 0})
    for s in completed:
        raw_ans, _ = _extract_answers_and_comments(s.answers)
        row = _normalize_stored_answers_row(raw_ans) if raw_ans else None
        if not row:
            continue
        valid_sessions += 1
        gname = _normalize_group_name(getattr(s, "group_name", None)) or "Без группы"
        by_group[gname]["sessions"] += 1
        for i, a in enumerate(row):
            if a is True:
                counts[i]["yes"] += 1
                by_group[gname]["yes"] += 1
            elif a is False:
                counts[i]["no"] += 1
                by_group[gname]["no"] += 1
            else:
                counts[i]["dont_know"] += 1
                by_group[gname]["dont_know"] += 1

    questions_out = []
    for i in range(QUESTIONS_COUNT):
        c = counts[i]
        t = c["yes"] + c["no"] + c["dont_know"]
        if t <= 0:
            questions_out.append({
                "index": i,
                "theme": MATURITY_QUESTIONS[i]["theme"],
                "short_text": (MATURITY_QUESTIONS[i]["text"][:80] + "…") if len(MATURITY_QUESTIONS[i]["text"]) > 80 else MATURITY_QUESTIONS[i]["text"],
                "yes_pct": 0.0,
                "no_pct": 0.0,
                "dont_know_pct": 0.0,
                "counts": c,
            })
        else:
            questions_out.append({
                "index": i,
                "theme": MATURITY_QUESTIONS[i]["theme"],
                "short_text": (MATURITY_QUESTIONS[i]["text"][:80] + "…") if len(MATURITY_QUESTIONS[i]["text"]) > 80 else MATURITY_QUESTIONS[i]["text"],
                "yes_pct": round(100.0 * c["yes"] / t, 1),
                "no_pct": round(100.0 * c["no"] / t, 1),
                "dont_know_pct": round(100.0 * c["dont_know"] / t, 1),
                "counts": c,
            })

    return jsonify({
        "selected_group": selected_group,
        "completed_sessions": valid_sessions,
        "group_summaries": [
            {
                "group_name": g,
                "sessions": v["sessions"],
                "yes": v["yes"],
                "no": v["no"],
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
    theme_n = {}
    for s in completed:
        raw_ans, _ = _extract_answers_and_comments(s.answers)
        row = _normalize_stored_answers_row(raw_ans) if raw_ans else None
        if not row:
            continue
        for i, q in enumerate(MATURITY_QUESTIONS):
            th = q["theme"]
            theme_n[th] = theme_n.get(th, 0) + 1
            if row[i] is True:
                theme_yes[th] = theme_yes.get(th, 0) + 1

    lines = []
    for th in sorted(theme_n.keys()):
        n = theme_n[th]
        y = theme_yes.get(th, 0)
        pct = round(100.0 * y / n, 1) if n else 0
        lines.append(f"- {th}: «да» {y}/{n} ({pct}%)")

    if not lines:
        return jsonify({"content": "<p>Нет завершённых оценок для сводки.</p>"})

    summary = "\n".join(lines)
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    prompt = f"""По агрегированным данным оценок зрелости (доля ответов «да» по темам среди завершённых опросов) дай 2–4 предложения: какие темы чаще всего слабые, на что обратить внимание организации. Только факты из сводки, без выдуманных цифр.

Сводка:
{summary}

Ответ: кратко, по-русски, HTML (<p>, <strong>)."""

    try:
        response = client.chat.completions.create(
            model=os.getenv("MATURITY_ADMIN_INSIGHTS_MODEL", "gpt-4.1-mini"),
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
        return jsonify({"error": str(e)}), 500


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
    theme_n = {}
    for s in completed:
        raw_ans, _ = _extract_answers_and_comments(s.answers)
        row = _normalize_stored_answers_row(raw_ans) if raw_ans else None
        if not row:
            continue
        for i, q in enumerate(MATURITY_QUESTIONS):
            th = q["theme"]
            theme_n[th] = theme_n.get(th, 0) + 1
            if row[i] is True:
                theme_yes[th] = theme_yes.get(th, 0) + 1

    if not theme_n:
        return jsonify({'error': 'Недостаточно валидных данных по группе'}), 400

    theme_rows = []
    for th in sorted(theme_n.keys()):
        n = theme_n[th]
        y = theme_yes.get(th, 0)
        pct = round(100.0 * y / n, 1) if n else 0.0
        theme_rows.append({"theme": th, "yes": y, "total": n, "yes_pct": pct})
    summary = "\n".join([f"- {r['theme']}: да {r['yes']}/{r['total']} ({r['yes_pct']}%)" for r in theme_rows])

    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    prompt = f"""Ты Agile transformation lead. Нужно подготовить план улучшений для стрима команд по агрегированной зрелости.

Группа команд: {group_name}
Завершённых оценок: {len(completed)}
Сводка по темам:
{summary}

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
      "steps": ["...", "..."]
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
- 5 инициатив уровня стрима.
- 12 недель roadmap.
- Пиши только по-русски.
- Не выдумывай числа вне переданной сводки.
"""
    try:
        import json
        response = client.chat.completions.create(
            model=os.getenv("MATURITY_GROUP_PLAN_MODEL", "gpt-4.1"),
            messages=[
                {"role": "system", "content": "Ты практик Agile-трансформаций в enterprise и банковской среде."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.45,
            max_tokens=2600,
        )
        raw = response.choices[0].message.content or "{}"
        try:
            parsed = json.loads(raw)
        except Exception:
            start = raw.find("{")
            end = raw.rfind("}")
            parsed = json.loads(raw[start:end + 1]) if start >= 0 and end > start else {}
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
        return jsonify({"error": str(e)}), 500
