"""Контент тренажёра «Роли в Scrum».

Участник распределяет карточки ответственности между 3 ролями
(Product Owner, Команда, Scrum Master) и для каждой роли выставляет
уровень участия: 🟢 отвечает, 🟡 участвует, 🔴 не должен делать.

Модуль задаёт:
  - ROLES            — три роли + описание
  - LEVELS           — уровни ответственности
  - CARDS            — 15 атомарных карточек с expected[role] = level
  - COMMON_ERRORS    — типовые ошибки и их последствия
  - evaluate_selection()  — считает green/yellow/red и health по
                             каждой карточке, роли и модулю целиком
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set


# --------------------------- Роли ---------------------------

ROLES: List[Dict] = [
    {
        "key": "po",
        "title": {"ru": "Владелец продукта", "en": "Product Owner"},
        "short": {"ru": "PO", "en": "PO"},
        "emoji": "📦",
        "desc": {
            "ru": "Отвечает за ценность и приоритеты продукта.",
            "en": "Owns the value and priorities of the product.",
        },
        "focus": {
            "ru": "что делать и зачем",
            "en": "what to build and why",
        },
    },
    {
        "key": "team",
        "title": {"ru": "Команда", "en": "The Team"},
        "short": {"ru": "Команда", "en": "Team"},
        "emoji": "👥",
        "desc": {
            "ru": "Создаёт продукт и отвечает за его качество.",
            "en": "Builds the product and owns its quality.",
        },
        "focus": {
            "ru": "как делать и делать качественно",
            "en": "how to build and build it well",
        },
    },
    {
        "key": "sm",
        "title": {"ru": "Scrum-мастер", "en": "Scrum Master"},
        "short": {"ru": "SM", "en": "SM"},
        "emoji": "🧭",
        "desc": {
            "ru": "Помогает процессу работать эффективно, убирает препятствия.",
            "en": "Keeps the process healthy and removes impediments.",
        },
        "focus": {
            "ru": "чтобы команде было легко делать хорошо",
            "en": "to make it easy for the team to deliver",
        },
    },
]

ROLE_KEYS: List[str] = [r["key"] for r in ROLES]


def valid_role_keys() -> Set[str]:
    return set(ROLE_KEYS)


# --------------------------- Уровни ответственности ---------------------------

LEVELS: List[Dict] = [
    {
        "key": "responsible",
        "title": {"ru": "Отвечает", "en": "Accountable"},
        "emoji": "🟢",
        "desc": {
            "ru": "Эта роль несёт ответственность за результат по этой карточке.",
            "en": "This role owns the outcome for this card.",
        },
    },
    {
        "key": "participates",
        "title": {"ru": "Участвует", "en": "Participates"},
        "emoji": "🟡",
        "desc": {
            "ru": "Роль вовлечена и влияет на результат, но не отвечает за него.",
            "en": "Involved and contributes, but not accountable.",
        },
    },
    {
        "key": "should_not",
        "title": {"ru": "Не должен делать", "en": "Should not do"},
        "emoji": "🔴",
        "desc": {
            "ru": "Эта роль не должна брать это на себя.",
            "en": "This role should stay out of this.",
        },
    },
]

LEVEL_KEYS: List[str] = [l["key"] for l in LEVELS]


def valid_level_keys() -> Set[str]:
    return set(LEVEL_KEYS)


# --------------------------- Карточки ---------------------------

# Каждая карточка: expected[role_key] = level.
# Если уровень не указан — считается, что "should_not" (роль не должна делать).

CARDS: List[Dict] = [
    {
        "key": "priorities",
        "title": {"ru": "Определяет приоритеты продукта",
                  "en": "Sets product priorities"},
        "subtitle": {
            "ru": "Что важнее в бэклоге сейчас: порядок и фокус — что делаем раньше, что позже, исходя из ценности.",
            "en": "What matters most in the backlog: ordering and focus — what to do sooner vs. later, based on value.",
        },
        "expected": {"po": "responsible", "team": "participates", "sm": "should_not"},
        "rationale": {
            "ru": "Если приоритеты размазаны — продукт теряет фокус.",
            "en": "If priorities are scattered, the product loses focus.",
        },
    },
    {
        "key": "value",
        "title": {"ru": "Отвечает за ценность продукта",
                  "en": "Owns product value"},
        "subtitle": {
            "ru": "Связь «продукт — польза» для пользователей и бизнеса: зачем этот продукт существует и что считаем успехом.",
            "en": "How the product links to user and business benefit — why the product exists and what “success” means.",
        },
        "expected": {"po": "responsible", "team": "participates", "sm": "should_not"},
        "rationale": {
            "ru": "Без одного ответственного за ценность команда делает «всё подряд».",
            "en": "Without one owner of value the team builds 'a bit of everything'.",
        },
    },
    {
        "key": "product_decisions",
        "title": {"ru": "Принимает решения по продукту",
                  "en": "Makes product decisions"},
        "subtitle": {
            "ru": "Что войдёт в релиз, готовность инкремента, accept/reject, продуктовые компромиссы (не «как писать код»).",
            "en": "What ships, when the increment is “done”, accept/reject, and product trade‑offs (not how to implement).",
        },
        "expected": {"po": "responsible", "team": "participates", "sm": "should_not"},
        "rationale": {
            "ru": "Если решения принимает SM или команда — теряется ориентир на клиента.",
            "en": "If SM or the team decides, the customer lens is lost.",
        },
    },
    {
        "key": "formulate_tasks",
        "title": {"ru": "Формулирует задачи",
                  "en": "Writes user stories / tasks"},
        "subtitle": {
            "ru": "Понятные формулировки PBI, критерии приёмки с точки зрения продукта; команда уточняет, как реализовать.",
            "en": "Clear backlog items and acceptance criteria as a product view; the team refines how to build it.",
        },
        "expected": {"po": "responsible", "team": "participates", "sm": "should_not"},
        "rationale": {
            "ru": "Формулировки — это продукт: PO отвечает, команда уточняет.",
            "en": "Wording is a product decision: PO owns, the team refines.",
        },
    },
    {
        "key": "maintain_backlog",
        "title": {"ru": "Поддерживает бэклог продукта",
                  "en": "Maintains the product backlog"},
        "subtitle": {
            "ru": "Актуальность, порядок, прозрачность: из чего состоит бэклог и в каком он виде для планирования.",
            "en": "Keeping the backlog current, ordered, and transparent for planning and discussion.",
        },
        "expected": {"po": "responsible", "team": "participates", "sm": "participates"},
        "rationale": {
            "ru": "Бэклог — зона PO, но команда и SM регулярно помогают его чистить.",
            "en": "Backlog is PO's area, but team and SM help keep it healthy.",
        },
    },
    {
        "key": "build_product",
        "title": {"ru": "Создаёт продукт",
                  "en": "Builds the product"},
        "subtitle": {
            "ru": "Проектирует, разрабатывает, тестирует и поставляет рабочий инкремент (код, контент, интеграции) — не «идеи в общем», а конкретная поставка.",
            "en": "Design, build, test, and ship a working increment (code, content, integrations) — concrete delivery, not vague “making something”.",
        },
        "expected": {"po": "should_not", "team": "responsible", "sm": "should_not"},
        "rationale": {
            "ru": "Делает только команда. PO не пишет код/контент за команду, SM тоже.",
            "en": "Only the team builds. PO doesn't ship for the team, nor does SM.",
        },
    },
    {
        "key": "how_to_work",
        "title": {"ru": "Определяет, как делать работу",
                  "en": "Decides how to do the work"},
        "subtitle": {
            "ru": "Практики, архитектура, стандарты кода, распределение задач внутри команды — «как» делаем работу, которую взяли.",
            "en": "Practices, architecture, standards, and how the team organises the work it commits to.",
        },
        "expected": {"po": "should_not", "team": "responsible", "sm": "should_not"},
        "rationale": {
            "ru": "«Как» — это всегда команда. Если решает PO или SM — теряется ответственность.",
            "en": "'How' is always the team. If PO or SM decide, ownership dies.",
        },
    },
    {
        "key": "estimate_tasks",
        "title": {"ru": "Оценивает задачи",
                  "en": "Estimates tasks"},
        "subtitle": {
            "ru": "Сложность, риск, трудоёмкость, прогноз срока — исходя из того, кто реально будет выполнять работу.",
            "en": "Size, risk, and forecast — from the people who will actually do the work.",
        },
        "expected": {"po": "participates", "team": "responsible", "sm": "should_not"},
        "rationale": {
            "ru": "Без команды в оценке — планы нереалистичны.",
            "en": "Without the team in estimation — plans become unrealistic.",
        },
    },
    {
        "key": "quality",
        "title": {"ru": "Отвечает за качество",
                  "en": "Owns quality"},
        "subtitle": {
            "ru": "Definition of Done, тестирование, устойчивое качество поставляемого инкремента — в первую очередь зона команды.",
            "en": "Definition of Done, testing, and sustainable quality of the increment — first and foremost the team’s area.",
        },
        "expected": {"po": "participates", "team": "responsible", "sm": "participates"},
        "rationale": {
            "ru": "Качество делает команда, но оно волнует всех.",
            "en": "The team delivers quality, but it matters to everyone.",
        },
    },
    {
        "key": "remove_impediments",
        "title": {"ru": "Устраняет препятствия",
                  "en": "Removes impediments"},
        "subtitle": {
            "ru": "Снимает внешние блокеры с пути команды: согласования, зависимости, ожидания, организационные тупики.",
            "en": "Clears external blockers: approvals, dependencies, hand‑offs, and organisational issues slowing the team.",
        },
        "expected": {"po": "participates", "team": "participates", "sm": "responsible"},
        "rationale": {
            "ru": "Это ключевая функция SM — расчищать дорогу команде.",
            "en": "Clearing the road is the SM's core job.",
        },
    },
    {
        "key": "help_team_effective",
        "title": {"ru": "Помогает команде работать эффективно",
                  "en": "Helps the team work effectively"},
        "subtitle": {
            "ru": "Коучинг, обучение, среда и культура — не постановка задач вместо команды и не «микроменеджмент».",
            "en": "Coaching, learning, and environment — not replacing the team or micromanaging the work.",
        },
        "expected": {"po": "should_not", "team": "participates", "sm": "responsible"},
        "rationale": {
            "ru": "Это не управление командой — это коучинг и сервис.",
            "en": "Not managing the team — it's coaching and service.",
        },
    },
    {
        "key": "organize_events",
        "title": {"ru": "Организует встречи команды",
                  "en": "Facilitates team events"},
        "subtitle": {
            "ru": "Scrum-церемонии, фасилитация, timebox, чтобы встречи давали пользу, а не только «прошли в календаре».",
            "en": "Scrum events, facilitation, and timeboxes so meetings deliver value, not just calendar time.",
        },
        "expected": {"po": "participates", "team": "participates", "sm": "responsible"},
        "rationale": {
            "ru": "SM отвечает, что встречи проходят и идут по делу, остальные — приходят и работают.",
            "en": "SM ensures events happen and stay focused; others show up and contribute.",
        },
    },
    {
        "key": "improve_process",
        "title": {"ru": "Улучшает процесс работы",
                  "en": "Improves the way of working"},
        "subtitle": {
            "ru": "Ретро, адаптация правил и практик под контекст: как команда работает вместе и со стейкхолдерами.",
            "en": "Retros and evolving practices to fit the context: how the team works together and with stakeholders.",
        },
        "expected": {"po": "participates", "team": "responsible", "sm": "responsible"},
        "rationale": {
            "ru": "Процесс — совместная зона команды и SM, PO подключается.",
            "en": "Process is a shared zone of the team and SM, with PO weighing in.",
        },
    },
    {
        "key": "customer_contact",
        "title": {"ru": "Взаимодействует с заказчиками",
                  "en": "Talks to customers and stakeholders"},
        "subtitle": {
            "ru": "Основной контакт по продукту: стейкхолдеры, пользователи, внешние ожидания; команда подключается на демо и уточнениях.",
            "en": "Main product contact with stakeholders and users; the team joins demos and Q&A as needed.",
        },
        "expected": {"po": "responsible", "team": "participates", "sm": "should_not"},
        "rationale": {
            "ru": "PO — лицо продукта наружу, команда участвует по делу.",
            "en": "PO is the outward face; the team joins when useful.",
        },
    },
    {
        "key": "shared_understanding",
        "title": {"ru": "Следит, что команда понимает задачи",
                  "en": "Ensures shared understanding of tasks"},
        "subtitle": {
            "ru": "Снимает рассинхрон «все по-разному поняли»: уточнения до старта работы, совместные refinement, ясные договорённости.",
            "en": "Closes gaps in what people think was agreed: clarify before work, joint refinement, shared clarity.",
        },
        "expected": {"po": "participates", "team": "participates", "sm": "responsible"},
        "rationale": {
            "ru": "SM ловит рассинхрон и организует уточнение: PO + команда.",
            "en": "SM spots the gap and helps PO and the team close it.",
        },
    },
]


def valid_card_keys() -> Set[str]:
    return {c["key"] for c in CARDS}


def _card(key: str) -> Optional[Dict]:
    for c in CARDS:
        if c["key"] == key:
            return c
    return None


# --------------------------- Типовые ошибки ---------------------------

COMMON_ERRORS: List[Dict] = [
    {
        "key": "sm_runs_dev",
        "title": {"ru": "Scrum-мастер управляет разработкой",
                  "en": "Scrum Master runs development"},
        "consequences": [
            {"ru": "Команда теряет ответственность за результат",
             "en": "The team loses ownership of the outcome"},
            {"ru": "SM перегружен и не улучшает процесс",
             "en": "SM is overloaded and stops improving the process"},
        ],
    },
    {
        "key": "po_runs_team",
        "title": {"ru": "Владелец продукта управляет командой",
                  "en": "PO manages the team"},
        "consequences": [
            {"ru": "Команда не чувствует ответственности за «как»",
             "en": "The team stops owning the 'how'"},
            {"ru": "Конфликты между PO и командой",
             "en": "PO vs team conflicts emerge"},
        ],
    },
    {
        "key": "team_not_planning",
        "title": {"ru": "Команда не участвует в планировании",
                  "en": "The team is not part of planning"},
        "consequences": [
            {"ru": "Нереалистичные оценки и обещания",
             "en": "Unrealistic estimates and promises"},
            {"ru": "Перегруз и срыв сроков",
             "en": "Overload and missed deadlines"},
        ],
    },
    {
        "key": "no_product_ownership",
        "title": {"ru": "Нет ответственности за продукт",
                  "en": "No one owns the product"},
        "consequences": [
            {"ru": "Делаем всё подряд и теряем фокус",
             "en": "We chase everything and lose focus"},
            {"ru": "Никто не защищает ценность",
             "en": "Nobody protects the value"},
        ],
    },
    {
        "key": "sm_as_secretary",
        "title": {"ru": "SM превращается в администратора встреч",
                  "en": "SM becomes a meeting secretary"},
        "consequences": [
            {"ru": "Процесс не улучшается",
             "en": "The process stops improving"},
            {"ru": "Препятствия остаются нерешёнными",
             "en": "Impediments stay unresolved"},
        ],
    },
    {
        "key": "po_designs_solution",
        "title": {"ru": "PO диктует, как реализовать задачу",
                  "en": "PO dictates how to implement"},
        "consequences": [
            {"ru": "Теряется экспертность команды",
             "en": "The team's expertise is wasted"},
            {"ru": "Решения получаются хуже, чем могли бы",
             "en": "Solutions end up weaker than they could be"},
        ],
    },
]


def valid_error_keys() -> Set[str]:
    return {e["key"] for e in COMMON_ERRORS}


# --------------------------- Локализация ---------------------------


def _loc(obj: Dict, locale: str) -> str:
    if not isinstance(obj, dict):
        return ""
    return obj.get(locale) or obj.get("ru") or obj.get("en") or ""


def get_content_for_locale(locale: str) -> Dict:
    locale = locale if locale in {"ru", "en"} else "ru"
    roles = [
        {
            "key": r["key"],
            "title": _loc(r["title"], locale),
            "short": _loc(r["short"], locale),
            "emoji": r["emoji"],
            "desc": _loc(r["desc"], locale),
            "focus": _loc(r["focus"], locale),
        }
        for r in ROLES
    ]
    levels = [
        {
            "key": l["key"],
            "title": _loc(l["title"], locale),
            "emoji": l["emoji"],
            "desc": _loc(l["desc"], locale),
        }
        for l in LEVELS
    ]
    cards = [
        {
            "key": c["key"],
            "title": _loc(c["title"], locale),
            "subtitle": _loc(c.get("subtitle") or {}, locale),
            "rationale": _loc(c["rationale"], locale),
        }
        for c in CARDS
    ]
    errors = [
        {
            "key": e["key"],
            "title": _loc(e["title"], locale),
            "consequences": [_loc(c, locale) for c in e["consequences"]],
        }
        for e in COMMON_ERRORS
    ]
    return {
        "roles": roles,
        "levels": levels,
        "cards": cards,
        "errors": errors,
    }


# --------------------------- Валидация / оценка ---------------------------


def _expected_level(card_key: str, role_key: str) -> str:
    c = _card(card_key)
    if not c:
        return "should_not"
    return (c.get("expected") or {}).get(role_key, "should_not")


def _classify(expected: str, picked: Optional[str]) -> str:
    """→ 'green' | 'yellow' | 'red' | 'missing'.

    - picked == expected           → green
    - picked is None and expected == 'should_not'  → green (неявный «не должен»)
    - picked is None and expected != 'should_not'  → missing
    - expected / picked — соседние уровни           → yellow
    - expected / picked — противоположные           → red
    """
    if picked is None:
        return "green" if expected == "should_not" else "missing"
    if picked == expected:
        return "green"
    # Соседи по шкале: responsible <-> participates, participates <-> should_not
    neighbours = {
        ("responsible", "participates"),
        ("participates", "responsible"),
        ("participates", "should_not"),
        ("should_not", "participates"),
    }
    if (expected, picked) in neighbours:
        return "yellow"
    # Противоположные: responsible <-> should_not
    return "red"


def sanitize_selection(raw: Optional[Dict]) -> Dict[str, Dict[str, Optional[str]]]:
    """{card_key: {role_key: level | None}}, только валидные значения."""
    out: Dict[str, Dict[str, Optional[str]]] = {}
    if not isinstance(raw, dict):
        return out
    valid_cards = valid_card_keys()
    for card_key, roles_map in raw.items():
        if not isinstance(card_key, str) or card_key not in valid_cards:
            continue
        if not isinstance(roles_map, dict):
            continue
        clean: Dict[str, Optional[str]] = {}
        for role_key in ROLE_KEYS:
            val = roles_map.get(role_key)
            if val is None or val == "" or val == "none":
                clean[role_key] = None
                continue
            if isinstance(val, str) and val in LEVEL_KEYS:
                clean[role_key] = val
            else:
                clean[role_key] = None
        out[card_key] = clean
    return out


def sanitize_custom_cards(raw) -> List[Dict]:
    """Пользовательские карточки, добавленные участником."""
    if not isinstance(raw, list):
        return []
    out: List[Dict] = []
    for item in raw[:5]:
        if not isinstance(item, dict):
            continue
        title = (item.get("title") or "").strip()
        if not title:
            continue
        title = title[:160]
        assigned = item.get("assigned") or {}
        clean_assigned: Dict[str, Optional[str]] = {}
        for role_key in ROLE_KEYS:
            lv = assigned.get(role_key) if isinstance(assigned, dict) else None
            if isinstance(lv, str) and lv in LEVEL_KEYS:
                clean_assigned[role_key] = lv
            else:
                clean_assigned[role_key] = None
        out.append({"title": title, "assigned": clean_assigned})
    return out


def sanitize_custom_role(raw) -> Optional[Dict]:
    """Пользовательская роль (одна)."""
    if not isinstance(raw, dict):
        return None
    title = (raw.get("title") or "").strip()[:120]
    desc = (raw.get("desc") or "").strip()[:240]
    if not title:
        return None
    return {"title": title, "desc": desc}


def sanitize_errors(raw) -> List[str]:
    if not isinstance(raw, list):
        return []
    valid = valid_error_keys()
    seen: Set[str] = set()
    out: List[str] = []
    for k in raw:
        if isinstance(k, str) and k in valid and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def evaluate_selection(selection: Dict[str, Dict[str, Optional[str]]]) -> Dict:
    """Возвращает:
    {
      cards: {
        card_key: {
          roles: {
            role_key: {expected, picked, color}
          },
          color: 'green' | 'yellow' | 'red',
        }
      },
      per_role: {role_key: {green, yellow, red, missing}},
      total: {green, yellow, red, missing, max, score, health_pct},
    }"""
    per_role = {rk: {"green": 0, "yellow": 0, "red": 0, "missing": 0} for rk in ROLE_KEYS}
    total = {"green": 0, "yellow": 0, "red": 0, "missing": 0}
    cards_eval: Dict[str, Dict] = {}
    for card in CARDS:
        ck = card["key"]
        roles_eval: Dict[str, Dict] = {}
        colors_here: List[str] = []
        for rk in ROLE_KEYS:
            expected = _expected_level(ck, rk)
            picked = (selection.get(ck) or {}).get(rk)
            color = _classify(expected, picked)
            roles_eval[rk] = {"expected": expected, "picked": picked, "color": color}
            per_role[rk][color] += 1
            total[color] += 1
            colors_here.append(color)
        if "red" in colors_here:
            card_color = "red"
        elif "missing" in colors_here:
            card_color = "red"
        elif "yellow" in colors_here:
            card_color = "yellow"
        else:
            card_color = "green"
        cards_eval[ck] = {"roles": roles_eval, "color": card_color}

    cells = len(CARDS) * len(ROLE_KEYS)
    score = total["green"] * 2 + total["yellow"] * 1 - total["red"] * 1
    max_score = cells * 2
    health_pct = round(max(score, 0) / max_score * 100) if max_score > 0 else 0
    return {
        "cards": cards_eval,
        "per_role": per_role,
        "total": {**total, "max": max_score, "score": score, "health_pct": health_pct},
    }


def card_title(key: str, locale: str) -> str:
    for c in CARDS:
        if c["key"] == key:
            return _loc(c["title"], locale)
    return key


def role_title(key: str, locale: str) -> str:
    for r in ROLES:
        if r["key"] == key:
            return _loc(r["title"], locale)
    return key


def level_title(key: str, locale: str) -> str:
    for l in LEVELS:
        if l["key"] == key:
            return _loc(l["title"], locale)
    return key
