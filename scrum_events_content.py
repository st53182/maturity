"""Контент тренажёра Scrum events / «Ритм работы команды».

Задача модуля — научить новичков собирать рабочий цикл команды из
атомарных карточек (цель, участники, артефакты и сущности, время, длительность)
для 5 событий: Planning, Product Backlog Refinement, Daily, Review, Retrospective.

Структура:
  - STAGES       — 5 этапов с ожидаемыми наборами карточек
  - CARDS        — банк всех карточек по 5 категориям
  - COMMON_ERRORS — типовые ошибки и их последствия
  - CUSTOM_CONTEXTS — альтернативные контексты для режима «Собери своё»
  - evaluate_selection() — считает score и помечает зелёным/жёлтым/красным
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple


# --------------------------- Этапы ---------------------------

# expected — карточки, которые однозначно уместны.
# acceptable — карточки, про которые можно поспорить, но это не ошибка.
# Всё остальное считается «не туда».

STAGES: List[Dict] = [
    {
        "key": "planning",
        "title": {"ru": "Планирование работы", "en": "Sprint Planning"},
        "short": {"ru": "Sprint Planning", "en": "Sprint Planning"},
        "purpose": {
            "ru": "Позволяет команде понять, что делать и как этого достичь.",
            "en": "Helps the team agree on what to do and how.",
        },
        "problem_it_solves": {
            "ru": "Снимает неопределённость в начале спринта и формирует общую цель.",
            "en": "Removes uncertainty at the start and creates a shared goal.",
        },
        "expected": {
            "goals": ["plan_work", "set_sprint_goal", "decompose_tasks", "prepare_tasks"],
            "participants": ["team", "product_owner", "scrum_master"],
            "artifacts": [
                "product_backlog", "sprint_backlog", "sprint_goal",
                "task_list", "definition_of_ready",
            ],
            "time": ["before_sprint", "first_day"],
            "duration": ["up_to_4h", "up_to_8h"],
        },
        "acceptable": {
            "goals": ["sync_team"],
            "participants": ["stakeholders"],
            "artifacts": ["team_agreements", "definition_of_done"],
            "time": [],
            "duration": ["1_2h", "up_to_3h"],
        },
    },
    {
        "key": "refinement",
        "title": {
            "ru": "Уточнение бэклога продукта",
            "en": "Product Backlog Refinement",
        },
        "short": {"ru": "Refinement", "en": "Refinement"},
        "purpose": {
            "ru": "Отдельный процесс: детализация, оценка и порядок элементов бэклога, чтобы планирование и работа в спринте опирались на прозрачные и готовые к работе требования.",
            "en": "A separate ongoing activity: detail, size and order backlog items so planning and the sprint are based on clear, ready work.",
        },
        "problem_it_solves": {
            "ru": "Уменьшает сырые требования и сюрпризы на планировании спринта.",
            "en": "Reduces vague items and last-minute surprises at sprint planning.",
        },
        "expected": {
            "goals": ["prepare_tasks", "decompose_tasks", "update_backlog"],
            "participants": ["team", "product_owner", "scrum_master"],
            "artifacts": [
                "product_backlog",
                "backlog_refinement",
                "task_list",
                "definition_of_ready",
            ],
            "time": ["before_sprint", "middle_of_sprint", "first_day"],
            "duration": ["30_min", "1h", "1_2h"],
        },
        "acceptable": {
            "goals": ["sync_team", "set_sprint_goal", "plan_work"],
            "participants": ["stakeholders", "customer"],
            "artifacts": ["sprint_backlog", "sprint_goal", "team_agreements", "blockers"],
            "time": ["every_day", "end_of_sprint"],
            "duration": ["up_to_3h", "up_to_4h"],
        },
    },
    {
        "key": "daily",
        "title": {"ru": "Ежедневная синхронизация", "en": "Daily"},
        "short": {"ru": "Daily", "en": "Daily"},
        "purpose": {
            "ru": "Помогает не терять синхронизацию и быстро выявлять проблемы.",
            "en": "Keeps the team aligned and surfaces blockers fast.",
        },
        "problem_it_solves": {
            "ru": "Устраняет микро-рассинхрон и даёт шанс перепланировать день.",
            "en": "Fixes micro-misalignment and lets the team replan the day.",
        },
        "expected": {
            "goals": ["sync_team", "understand_progress", "spot_issues"],
            "participants": ["team", "scrum_master"],
            "artifacts": [
                "sprint_goal", "progress", "task_list",
                "team_agreements", "blockers",
            ],
            "time": ["every_day"],
            "duration": ["15_min"],
        },
        "acceptable": {
            "goals": [],
            "participants": [],
            "artifacts": ["sprint_backlog"],
            "time": ["middle_of_sprint"],
            "duration": ["30_min"],
        },
    },
    {
        "key": "review",
        "title": {"ru": "Обзор спринта (Sprint Review)", "en": "Sprint Review (sprint review)"},
        "short": {"ru": "Sprint Review", "en": "Sprint Review"},
        "purpose": {
            "ru": "Событие Sprint Review: показать инкремент, получить обратную связь и скорректировать бэклог продукта.",
            "en": "The Sprint Review: show the increment, gather feedback, and adapt the Product Backlog.",
        },
        "problem_it_solves": {
            "ru": "Снимает риск «сделали и никому не нужно» и согласует ожидания стейкхолдеров с инкрементом.",
            "en": "Prevents shipping the wrong thing and aligns stakeholders with the increment.",
        },
        "expected": {
            "goals": ["show_result", "get_feedback", "update_backlog"],
            "participants": ["team", "product_owner", "stakeholders", "customer"],
            "artifacts": [
                "increment", "feedback", "product_metrics",
                "product_backlog", "sprint_goal",
            ],
            "time": ["end_of_sprint"],
            "duration": ["1h", "1_2h", "up_to_3h", "up_to_4h"],
        },
        "acceptable": {
            "goals": ["sync_team"],
            "participants": ["scrum_master"],
            "artifacts": ["definition_of_done"],
            "time": [],
            "duration": ["30_min"],
        },
    },
    {
        "key": "retro",
        "title": {"ru": "Ретроспектива (улучшение процесса)", "en": "Retrospective (process improvement)"},
        "short": {"ru": "Retrospective", "en": "Retrospective"},
        "purpose": {
            "ru": "Событие «Ретроспектива Спринта»: командно разобрать, как прошла работа, и спланировать улучшения процесса.",
            "en": "The Sprint Retrospective: inspect how the sprint went and plan improvements to how the team works.",
        },
        "problem_it_solves": {
            "ru": "Превращает усталость и раздражение в конкретные улучшения и договорённости.",
            "en": "Turns friction into concrete improvements and working agreements.",
        },
        "expected": {
            "goals": ["analyze_process", "find_improvements"],
            "participants": ["team", "scrum_master"],
            "artifacts": [
                "improvements", "team_agreements", "blockers",
            ],
            "time": ["end_of_sprint", "after_sprint"],
            "duration": ["1h", "1_2h", "up_to_3h"],
        },
        "acceptable": {
            "goals": ["spot_issues"],
            "participants": ["product_owner"],
            "artifacts": ["feedback", "progress"],
            "time": [],
            "duration": ["30_min", "up_to_4h"],
        },
    },
]


STAGE_KEYS: List[str] = [s["key"] for s in STAGES]


def valid_stage_keys() -> Set[str]:
    return set(STAGE_KEYS)


# --------------------------- Карточки ---------------------------

# 5 категорий. Каждая карточка — один ключ, одна короткая строка.

CARDS: Dict[str, List[Dict]] = {
    "goals": [
        {"key": "plan_work", "title": {"ru": "Спланировать работу команды", "en": "Plan the team's work"}},
        {"key": "set_sprint_goal", "title": {"ru": "Сформулировать цель спринта", "en": "Set the sprint goal"}},
        {"key": "decompose_tasks", "title": {"ru": "Декомпозировать задачи", "en": "Break down tasks"}},
        {"key": "sync_team", "title": {"ru": "Синхронизировать команду", "en": "Sync the team"}},
        {"key": "understand_progress", "title": {"ru": "Понять прогресс к цели", "en": "See progress to the goal"}},
        {"key": "spot_issues", "title": {"ru": "Выявить проблемы", "en": "Spot issues"}},
        {"key": "get_feedback", "title": {"ru": "Получить обратную связь", "en": "Get feedback"}},
        {"key": "show_result", "title": {"ru": "Показать результат работы", "en": "Show the result"}},
        {"key": "analyze_process", "title": {"ru": "Проанализировать процесс", "en": "Analyse the process"}},
        {"key": "find_improvements", "title": {"ru": "Найти улучшения", "en": "Find improvements"}},
        {"key": "update_backlog", "title": {"ru": "Обновить бэклог продукта", "en": "Refresh the product backlog"}},
        {"key": "prepare_tasks", "title": {"ru": "Подготовить задачи к работе", "en": "Get tasks ready to work on"}},
    ],
    "participants": [
        {"key": "team", "title": {"ru": "Команда", "en": "The team"}},
        {"key": "product_owner", "title": {"ru": "Владелец продукта", "en": "Product Owner"}},
        {"key": "scrum_master", "title": {"ru": "Скрам-мастер", "en": "Scrum Master"}},
        {"key": "customer", "title": {"ru": "Заказчик / клиент", "en": "Customer"}},
        {"key": "stakeholders", "title": {"ru": "Стейкхолдеры", "en": "Stakeholders"}},
    ],
    "artifacts": [
        {"key": "product_backlog", "title": {"ru": "Бэклог продукта", "en": "Product backlog"}},
        {
            "key": "backlog_refinement",
            "title": {
                "ru": "Уточнение бэклога продукта (PBI)",
                "en": "Product Backlog Refinement (PBI)",
            },
        },
        {"key": "sprint_backlog", "title": {"ru": "Бэклог спринта", "en": "Sprint backlog"}},
        {"key": "sprint_goal", "title": {"ru": "Цель спринта", "en": "Sprint goal"}},
        {"key": "increment", "title": {"ru": "Инкремент продукта", "en": "Product increment"}},
        {"key": "progress", "title": {"ru": "Прогресс команды", "en": "Team progress"}},
        {"key": "task_list", "title": {"ru": "Список задач", "en": "Task list"}},
        {"key": "team_agreements", "title": {"ru": "Договорённости команды", "en": "Team agreements"}},
        {"key": "feedback", "title": {"ru": "Обратная связь", "en": "Feedback"}},
        {"key": "product_metrics", "title": {"ru": "Метрики продукта", "en": "Product metrics"}},
        {"key": "improvements", "title": {"ru": "Список улучшений", "en": "List of improvements"}},
        {"key": "blockers", "title": {"ru": "Препятствия и проблемы", "en": "Blockers and issues"}},
        {"key": "definition_of_ready", "title": {"ru": "Definition of Ready", "en": "Definition of Ready"}},
        {"key": "definition_of_done", "title": {"ru": "Definition of Done", "en": "Definition of Done"}},
    ],
    "time": [
        {"key": "before_sprint", "title": {"ru": "Перед началом спринта", "en": "Before the sprint"}},
        {"key": "first_day", "title": {"ru": "В первый день спринта", "en": "First day of the sprint"}},
        {"key": "every_day", "title": {"ru": "Каждый день", "en": "Every day"}},
        {"key": "middle_of_sprint", "title": {"ru": "В середине спринта", "en": "Mid-sprint"}},
        {"key": "end_of_sprint", "title": {"ru": "В конце спринта", "en": "End of the sprint"}},
        {"key": "after_sprint", "title": {"ru": "После завершения спринта", "en": "After the sprint"}},
    ],
    "duration": [
        {"key": "15_min", "title": {"ru": "15 минут", "en": "15 minutes"}},
        {"key": "30_min", "title": {"ru": "30 минут", "en": "30 minutes"}},
        {"key": "1h", "title": {"ru": "1 час", "en": "1 hour"}},
        {"key": "1_2h", "title": {"ru": "1–2 часа", "en": "1–2 hours"}},
        {"key": "up_to_3h", "title": {"ru": "До 3 часов", "en": "Up to 3 hours"}},
        {"key": "up_to_4h", "title": {"ru": "До 4 часов", "en": "Up to 4 hours"}},
        {"key": "up_to_8h", "title": {"ru": "До 8 часов", "en": "Up to 8 hours"}},
    ],
}


CATEGORIES: List[str] = list(CARDS.keys())  # ["goals","participants","artifacts","time","duration"]


def valid_card_keys(category: str) -> Set[str]:
    return {c["key"] for c in CARDS.get(category, [])}


# --------------------------- Типовые ошибки ---------------------------

COMMON_ERRORS: List[Dict] = [
    {
        "key": "no_team_on_planning",
        "title": {"ru": "Нет команды на планировании", "en": "No team at planning"},
        "consequences": [
            {"ru": "Команда не понимает, что и зачем делать", "en": "The team doesn't know what or why"},
            {"ru": "Переделки в середине спринта", "en": "Rework in the middle of the sprint"},
        ],
    },
    {
        "key": "no_customer_on_review",
        "title": {"ru": "Нет заказчика на демонстрации", "en": "No customer at the review"},
        "consequences": [
            {"ru": "Обратная связь приходит поздно", "en": "Feedback comes too late"},
            {"ru": "Делаем не то, что нужно", "en": "We build the wrong thing"},
        ],
    },
    {
        "key": "no_retro",
        "title": {"ru": "Отсутствует ретроспектива", "en": "No retrospective"},
        "consequences": [
            {"ru": "Команда не улучшается", "en": "The team stops improving"},
            {"ru": "Проблемы копятся и взрываются", "en": "Issues pile up and explode"},
        ],
    },
    {
        "key": "meetings_too_long",
        "title": {"ru": "Слишком длинные встречи", "en": "Meetings are too long"},
        "consequences": [
            {"ru": "Потеря времени и внимания", "en": "Wasted time and focus"},
            {"ru": "Люди перестают приходить", "en": "People stop showing up"},
        ],
    },
    {
        "key": "no_clear_goal",
        "title": {"ru": "Нет чёткой цели спринта", "en": "No clear sprint goal"},
        "consequences": [
            {"ru": "Команда делает всё подряд", "en": "The team chases everything at once"},
            {"ru": "Снижение качества и мотивации", "en": "Quality and motivation drop"},
        ],
    },
    {
        "key": "daily_as_status",
        "title": {"ru": "Daily превращается в отчёт менеджеру", "en": "Daily becomes a status report"},
        "consequences": [
            {"ru": "Нет настоящей синхронизации", "en": "No real team sync"},
            {"ru": "Скрытые проблемы не вскрываются", "en": "Hidden issues stay hidden"},
        ],
    },
    {
        "key": "review_without_increment",
        "title": {"ru": "На Review нечего показывать", "en": "Nothing to show at Review"},
        "consequences": [
            {"ru": "Нет прогресса для обсуждения", "en": "No progress to discuss"},
            {"ru": "Стейкхолдеры теряют доверие", "en": "Stakeholders lose trust"},
        ],
    },
    {
        "key": "no_refinement",
        "title": {"ru": "Нет отдельного уточнения бэклога", "en": "No backlog refinement habit"},
        "consequences": [
            {"ru": "Бэклог сырой, планирование растягивается", "en": "The backlog stays vague and planning drags"},
            {"ru": "В спринт попадают непрозрачные элементы", "en": "Unclear work enters the sprint"},
        ],
    },
]


def valid_error_keys() -> Set[str]:
    return {e["key"] for e in COMMON_ERRORS}


# --------------------------- Альтернативные контексты ---------------------------

CUSTOM_CONTEXTS: List[Dict] = [
    {
        "key": "team_meeting",
        "title": {"ru": "Планёрка", "en": "Team meeting"},
        "desc": {
            "ru": "Регулярная встреча команды, на которой договариваются о следующем шаге.",
            "en": "A recurring team meeting to agree on the next step.",
        },
    },
    {
        "key": "marketing_meeting",
        "title": {"ru": "Маркетинг-встреча", "en": "Marketing meeting"},
        "desc": {
            "ru": "Встреча, где синхронизируются по кампаниям и контенту.",
            "en": "A meeting to sync on campaigns and content.",
        },
    },
    {
        "key": "ops_shift",
        "title": {"ru": "Операционная смена", "en": "Operational shift"},
        "desc": {
            "ru": "Пересменка в сервисе: что было вчера, что сейчас, что завтра.",
            "en": "A service shift handover: yesterday, today, tomorrow.",
        },
    },
]


def valid_custom_keys() -> Set[str]:
    return {c["key"] for c in CUSTOM_CONTEXTS}


# --------------------------- Локализация ---------------------------


def _loc(obj: Dict, locale: str) -> str:
    if not isinstance(obj, dict):
        return ""
    return obj.get(locale) or obj.get("ru") or obj.get("en") or ""


def get_content_for_locale(locale: str) -> Dict:
    locale = locale if locale in {"ru", "en"} else "ru"

    stages = []
    for s in STAGES:
        stages.append({
            "key": s["key"],
            "title": _loc(s["title"], locale),
            "short": _loc(s["short"], locale),
            "purpose": _loc(s["purpose"], locale),
            "problem_it_solves": _loc(s["problem_it_solves"], locale),
            # Для фронта отдаём expected/acceptable как ключи —
            # визуальная подсветка делается клиентом на основании result.
        })

    cards = {}
    for cat, items in CARDS.items():
        cards[cat] = [{"key": c["key"], "title": _loc(c["title"], locale)} for c in items]

    errors = [
        {
            "key": e["key"],
            "title": _loc(e["title"], locale),
            "consequences": [_loc(c, locale) for c in e["consequences"]],
        }
        for e in COMMON_ERRORS
    ]

    customs = [
        {
            "key": c["key"],
            "title": _loc(c["title"], locale),
            "desc": _loc(c["desc"], locale),
        }
        for c in CUSTOM_CONTEXTS
    ]

    # Эталонные ключи карточек по этапам (для финального экрана «как должно быть»)
    reference: Dict[str, Dict] = {}
    for s in STAGES:
        reference[s["key"]] = {
            "expected": {c: list(s["expected"].get(c, [])) for c in CATEGORIES},
            "acceptable": {c: list(s["acceptable"].get(c, [])) for c in CATEGORIES},
        }

    return {
        "stages": stages,
        "cards": cards,
        "categories": CATEGORIES,
        "errors": errors,
        "customs": customs,
        "reference": reference,
    }


def get_content_for_participant(locale: str) -> Dict:
    """Контент для участника: без эталона (разбор — на дебрифе с фасилитатором)."""
    out = dict(get_content_for_locale(locale))
    out.pop("reference", None)
    return out


def get_facilitator_reference_view(locale: str) -> Dict:
    """Эталон + подписи карточек — только для панели фасилитатора / JWT API."""
    full = get_content_for_locale(locale)
    return {
        "stages": full["stages"],
        "categories": full["categories"],
        "cards": full["cards"],
        "reference": full["reference"],
    }


# --------------------------- Оценка выбора ---------------------------


def _stage(key: str) -> Optional[Dict]:
    for s in STAGES:
        if s["key"] == key:
            return s
    return None


def sanitize_selection(raw: Optional[Dict]) -> Dict[str, Dict[str, List[str]]]:
    """Нормализует payload участника: {stage: {category: [keys]}}."""
    out: Dict[str, Dict[str, List[str]]] = {}
    if not isinstance(raw, dict):
        return out
    for stage_key in STAGE_KEYS:
        stage_raw = raw.get(stage_key) or {}
        stage_out: Dict[str, List[str]] = {}
        if not isinstance(stage_raw, dict):
            out[stage_key] = {c: [] for c in CATEGORIES}
            continue
        for cat in CATEGORIES:
            cat_raw = stage_raw.get(cat) or []
            if not isinstance(cat_raw, list):
                cat_raw = []
            valid = valid_card_keys(cat)
            seen: Set[str] = set()
            clean: List[str] = []
            for k in cat_raw:
                if not isinstance(k, str):
                    continue
                if k in valid and k not in seen:
                    seen.add(k)
                    clean.append(k)
            stage_out[cat] = clean
        out[stage_key] = stage_out
    return out


def _classify(
    selected: List[str], expected: List[str], acceptable: List[str]
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """→ (green, yellow, red, missing_expected)."""
    exp = set(expected)
    accept = set(acceptable)
    green: List[str] = []
    yellow: List[str] = []
    red: List[str] = []
    for k in selected:
        if k in exp:
            green.append(k)
        elif k in accept:
            yellow.append(k)
        else:
            red.append(k)
    missing = [k for k in expected if k not in selected]
    return green, yellow, red, missing


def evaluate_stage(stage_key: str, stage_selection: Dict[str, List[str]]) -> Dict:
    """Оценивает один этап: по каждой категории возвращает
    green/yellow/red/missing и общий цвет стадии."""
    s = _stage(stage_key)
    if not s:
        return {
            "stage_key": stage_key,
            "categories": {},
            "score": 0,
            "max_score": 0,
            "color": "gray",
        }

    categories: Dict[str, Dict] = {}
    score = 0
    max_score = 0
    any_red = False
    any_yellow = False

    for cat in CATEGORIES:
        expected = s["expected"].get(cat, [])
        acceptable = s["acceptable"].get(cat, [])
        picked = stage_selection.get(cat, [])
        green, yellow, red, missing = _classify(picked, expected, acceptable)

        cat_score = len(green) * 2 + len(yellow) - len(red)
        cat_max = max(len(expected), 1) * 2
        score += max(cat_score, 0)
        max_score += cat_max

        if red:
            any_red = True
        if yellow or missing:
            any_yellow = True

        categories[cat] = {
            "green": green,
            "yellow": yellow,
            "red": red,
            "missing": missing,
            "score": cat_score,
            "max_score": cat_max,
        }

    color = "red" if any_red else ("yellow" if any_yellow else "green")
    return {
        "stage_key": stage_key,
        "categories": categories,
        "score": score,
        "max_score": max_score,
        "color": color,
    }


def evaluate_selection(selection: Dict[str, Dict[str, List[str]]]) -> Dict:
    """Оценивает весь набор этапов."""
    stages_eval: Dict[str, Dict] = {}
    total_score = 0
    total_max = 0
    colors = {"green": 0, "yellow": 0, "red": 0}
    for s_key in STAGE_KEYS:
        ev = evaluate_stage(s_key, selection.get(s_key, {}))
        stages_eval[s_key] = ev
        total_score += ev["score"]
        total_max += ev["max_score"]
        colors[ev["color"]] = colors.get(ev["color"], 0) + 1

    pct = round((total_score / total_max) * 100) if total_max > 0 else 0
    return {
        "stages": stages_eval,
        "total_score": total_score,
        "total_max": total_max,
        "health_pct": pct,
        "color_counts": colors,
    }


# --------------------------- Вспомогательное ---------------------------


def card_title(category: str, key: str, locale: str) -> str:
    for c in CARDS.get(category, []):
        if c["key"] == key:
            return _loc(c["title"], locale)
    return key


def stage_title(key: str, locale: str) -> str:
    s = _stage(key)
    return _loc(s["title"], locale) if s else key
