"""Контент тренажёра приоритизации WSJF (Weighted Shortest Job First).

Учим принимать решения в условиях неопределённости на примере
автомобильной компании, выбирающей одно из трёх направлений:
гибрид / электро / водород.

Формула:
    priority = (value + urgency) / complexity

где value, urgency и complexity участник ставит по шкале 1-2-3-5-8-13
(Fibonacci). Ценим не формулу, а разговор вокруг неё: что поставил
выше, почему, какой trade-off принял.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple


FIBO_SCALE: List[int] = [1, 2, 3, 5, 8, 13]


# --------------------------- Роли ---------------------------


ROLES: List[Dict] = [
    {
        "key": "business",
        "title": {"ru": "Бизнес", "en": "Business"},
        "focus": {"ru": "Фокус на прибыли сейчас", "en": "Focus on profit now"},
        "desc": {
            "ru": "Ты смотришь на деньги и сроки: важна выручка в обозримом горизонте, риски — во вторую очередь.",
            "en": "You look at revenue and timing: near-term money matters most, risks come second.",
        },
        # На что роль склонна обращать больше внимания при оценке
        "bias": {"value": 1, "urgency": 0, "complexity": -1},
    },
    {
        "key": "engineer",
        "title": {"ru": "Инженер", "en": "Engineer"},
        "focus": {"ru": "Фокус на реализуемости", "en": "Focus on feasibility"},
        "desc": {
            "ru": "Ты знаешь цену сроков и технических рисков. Важно, чтобы команда вообще смогла это сделать — и не развалилась.",
            "en": "You know the cost of timelines and tech risk. Making it actually work without burning the team matters most.",
        },
        "bias": {"value": 0, "urgency": -1, "complexity": 1},
    },
    {
        "key": "strategist",
        "title": {"ru": "Стратег", "en": "Strategist"},
        "focus": {"ru": "Фокус на будущем", "en": "Focus on the future"},
        "desc": {
            "ru": "Смотришь за горизонт: где будет рынок через 3-5 лет и на чём можно сыграть «в долгую», даже если сейчас больно.",
            "en": "You look over the horizon: where will the market be in 3-5 years and where can we play a long game even if it hurts now.",
        },
        "bias": {"value": 0, "urgency": 1, "complexity": 0},
    },
]


def valid_role_keys() -> Set[str]:
    return {r["key"] for r in ROLES}


# --------------------------- Опции ---------------------------


# expected_scores — «экспертные» оценки value/urgency/complexity. Мы
# не настаиваем, что это «правильные» значения — но сравнение с ними
# помогает подсветить типичные ошибки.
OPTIONS: List[Dict] = [
    {
        "key": "hybrid",
        "title": {"ru": "Гибридные автомобили", "en": "Hybrid cars"},
        "short": {
            "ru": "Быстрый доход, низкий риск, слабая перспектива",
            "en": "Fast revenue, low risk, weak long-term prospects",
        },
        "description": {
            "ru": (
                "Из-за жалоб клиентов на расход топлива вы рассматриваете гибриды. "
                "Это может поднять выручку ~+150 M€ к прошлому году. Но если рынок "
                "быстро уйдёт в чистое электро, продукт устареет."
            ),
            "en": (
                "Customers complain about fuel use, so you are considering hybrids. "
                "Could lift revenue ~+€150M YoY. But if the market jumps straight to "
                "pure electric, the product ages fast."
            ),
        },
        "revenue_label": {"ru": "+150 M€", "en": "+€150M"},
        "time_label": {"ru": "≈ 5 месяцев", "en": "≈ 5 months"},
        "expected_scores": {"value": 5, "urgency": 8, "complexity": 3},
        "strengths": {
            "ru": ["Быстро до денег", "Технология отработана", "Низкий риск срыва"],
            "en": ["Quick path to money", "Proven technology", "Low execution risk"],
        },
        "risks": {
            "ru": [
                "Окно возможностей короткое",
                "Рынок может уйти в электро раньше",
            ],
            "en": [
                "Window of opportunity is short",
                "Market may shift to EV earlier",
            ],
        },
    },
    {
        "key": "electric",
        "title": {"ru": "Электромобили", "en": "Electric cars"},
        "short": {
            "ru": "Баланс выручки и роста, средний риск",
            "en": "Balanced revenue and growth, medium risk",
        },
        "description": {
            "ru": (
                "У вас уже есть опыт недорогих машин и договорённости о поставках для "
                "города — около 100 000 авто в год и ~+300 M€ выручки. Но сложнее в "
                "производстве, возможны задержки и технические риски."
            ),
            "en": (
                "You have experience with affordable cars and a city-fleet deal — "
                "~100k vehicles/year and ~+€300M revenue. But production is harder, "
                "with possible delays and technical risks."
            ),
        },
        "revenue_label": {"ru": "+300 M€", "en": "+€300M"},
        "time_label": {"ru": "≈ 7 месяцев", "en": "≈ 7 months"},
        "expected_scores": {"value": 13, "urgency": 8, "complexity": 8},
        "strengths": {
            "ru": [
                "Большая выручка",
                "Рынок растёт",
                "Есть готовый контракт на 100k машин",
            ],
            "en": [
                "Large revenue",
                "Market is growing",
                "Ready contract for 100k units",
            ],
        },
        "risks": {
            "ru": [
                "Риски производства и сроков",
                "Нужны инвестиции в линии и батареи",
            ],
            "en": [
                "Production and timing risk",
                "Heavy investment in lines and batteries",
            ],
        },
    },
    {
        "key": "hydrogen",
        "title": {"ru": "Водородные автомобили", "en": "Hydrogen cars"},
        "short": {
            "ru": "Возможный прорыв, высокий риск, долгий срок",
            "en": "Possible breakthrough, high risk, long horizon",
        },
        "description": {
            "ru": (
                "У вас есть гипотеза о водороде. Один из конкурентов тоже смотрит в эту "
                "сторону, но ещё не начал разработку. Потенциал огромный, но технология "
                "новая и риски соответствующие."
            ),
            "en": (
                "You have a hypothesis about hydrogen. A competitor is eyeing the same "
                "direction but hasn't started yet. Huge potential, but the tech is new "
                "and risks match."
            ),
        },
        "revenue_label": {"ru": "? — позже", "en": "? — later"},
        "time_label": {"ru": "≈ 20 месяцев", "en": "≈ 20 months"},
        "expected_scores": {"value": 13, "urgency": 2, "complexity": 13},
        "strengths": {
            "ru": [
                "Возможный прорыв на 3-5 лет",
                "Преимущество первого хода",
            ],
            "en": [
                "Possible breakthrough in 3-5 years",
                "First-mover advantage",
            ],
        },
        "risks": {
            "ru": [
                "Долго без выручки",
                "Новая технология, риск провала",
                "Большие инвестиции",
            ],
            "en": [
                "Long period without revenue",
                "New tech, risk of failure",
                "Heavy investment",
            ],
        },
    },
]


def valid_option_keys() -> Set[str]:
    return {o["key"] for o in OPTIONS}


def _option(key: str) -> Optional[Dict]:
    for o in OPTIONS:
        if o["key"] == key:
            return o
    return None


# --------------------------- События ---------------------------


# Событие после первого выбора — «новая информация», которая меняет
# оценки. Для каждого события задаём рекомендуемые корректировки и
# короткое обоснование.
EVENTS: List[Dict] = [
    {
        "key": "subsidies_electric",
        "title": {
            "ru": "Государство вводит субсидии на электромобили",
            "en": "Government introduces EV subsidies",
        },
        "lead": {
            "ru": "Субсидия на покупателя — до 15% стоимости. Спрос на электро скачком растёт, окно возможностей — год-полтора.",
            "en": "A buyer subsidy up to 15% of the price. Demand for EVs jumps; the window is 12-18 months.",
        },
        # как меняется «экспертная» картина:
        "shifts": [
            {"option": "electric", "dim": "urgency", "to": 13, "reason_key": "shift.ev_urgency_up"},
            {"option": "hybrid", "dim": "value", "to": 3, "reason_key": "shift.hybrid_value_down"},
        ],
        "favors": "electric",
    },
    {
        "key": "hybrid_market_falling",
        "title": {
            "ru": "Рынок гибридов начинает падать",
            "en": "The hybrid market starts to decline",
        },
        "lead": {
            "ru": "Отчёты за квартал: гибриды теряют долю — покупатели ждут электро. Окно для гибрида закрывается раньше, чем казалось.",
            "en": "Quarterly reports: hybrids are losing share — buyers wait for EVs. The hybrid window closes earlier than expected.",
        },
        "shifts": [
            {"option": "hybrid", "dim": "value", "to": 2, "reason_key": "shift.hybrid_value_drop"},
            {"option": "hybrid", "dim": "urgency", "to": 3, "reason_key": "shift.hybrid_urgency_drop"},
        ],
        "favors": "electric",
    },
    {
        "key": "hydrogen_faster",
        "title": {
            "ru": "Технология водорода развивается быстрее, чем ожидалось",
            "en": "Hydrogen tech matures faster than expected",
        },
        "lead": {
            "ru": "Топливные элементы подешевели на 30% за год, появляются промышленные партнёры. Горизонт до прорыва — ближе.",
            "en": "Fuel cells are 30% cheaper YoY, industrial partners are emerging. The breakthrough horizon gets closer.",
        },
        "shifts": [
            {"option": "hydrogen", "dim": "complexity", "to": 5, "reason_key": "shift.h2_easier"},
            {"option": "hydrogen", "dim": "urgency", "to": 5, "reason_key": "shift.h2_urgency_up"},
        ],
        "favors": "hydrogen",
    },
]


def valid_event_keys() -> Set[str]:
    return {e["key"] for e in EVENTS}


def pick_event_for_choice(initial_choice: Optional[str]) -> Dict:
    """Выбираем событие так, чтобы оно максимально встряхивало первое решение.

    * Выбрал hybrid → показываем падение рынка гибридов (hybrid_market_falling).
    * Выбрал electric → показываем ускорение водорода (hydrogen_faster).
    * Выбрал hydrogen → показываем субсидии на EV (subsidies_electric).
    * Нет выбора → первое по списку.
    """
    mapping = {
        "hybrid": "hybrid_market_falling",
        "electric": "hydrogen_faster",
        "hydrogen": "subsidies_electric",
    }
    target = mapping.get(initial_choice or "", "subsidies_electric")
    for e in EVENTS:
        if e["key"] == target:
            return e
    return EVENTS[0]


# --------------------------- Локализованный контент ---------------------------


def get_content_for_locale(locale: str) -> Dict:
    loc = "en" if locale == "en" else "ru"
    roles = [
        {
            "key": r["key"],
            "title": r["title"][loc],
            "focus": r["focus"][loc],
            "desc": r["desc"][loc],
            "bias": dict(r["bias"]),
        }
        for r in ROLES
    ]
    options = [
        {
            "key": o["key"],
            "title": o["title"][loc],
            "short": o["short"][loc],
            "description": o["description"][loc],
            "revenue_label": o["revenue_label"][loc],
            "time_label": o["time_label"][loc],
            "expected_scores": dict(o["expected_scores"]),
            "strengths": list(o["strengths"][loc]),
            "risks": list(o["risks"][loc]),
        }
        for o in OPTIONS
    ]
    events = [
        {
            "key": e["key"],
            "title": e["title"][loc],
            "lead": e["lead"][loc],
            "shifts": [dict(s) for s in e["shifts"]],
            "favors": e["favors"],
        }
        for e in EVENTS
    ]
    return {
        "scale": list(FIBO_SCALE),
        "roles": roles,
        "options": options,
        "events": events,
        "context": {
            "title": ("Автомобильная компания на распутье"
                     if loc == "ru" else "A car company at a crossroads"),
            "lead": (
                "Вы — команда, принимающая стратегическое решение в автомобильной "
                "компании. Компания делает недорогие машины и решает, куда двигаться "
                "дальше. Ресурсы ограничены — сначала запустится только одно направление."
                if loc == "ru" else
                "You are a team making a strategic decision at a car company. The "
                "company builds affordable vehicles and is deciding where to go next. "
                "Resources are limited — only one direction starts first."
            ),
        },
    }


# --------------------------- Валидация ---------------------------


def _coerce_score(v) -> Optional[int]:
    try:
        iv = int(v)
    except Exception:
        return None
    return iv if iv in FIBO_SCALE else None


def sanitize_round(payload: Dict) -> Dict:
    """Приводит ответ пользователя к каноничному виду:

        {
          "scores": {
              "hybrid": { "value": 5, "urgency": 8, "complexity": 3 },
              ...
          },
          "choice": "electric" | "hybrid" | "hydrogen" | None
        }

    Пропущенные размерности заполняются 1 (минимум) — чтобы формула
    не падала. Выбор валидируется по списку опций.
    """
    if not isinstance(payload, dict):
        payload = {}
    raw_scores = payload.get("scores") or {}
    scores: Dict[str, Dict[str, int]] = {}
    for opt in OPTIONS:
        block = raw_scores.get(opt["key"]) if isinstance(raw_scores, dict) else None
        block = block if isinstance(block, dict) else {}
        scores[opt["key"]] = {
            "value": _coerce_score(block.get("value")) or 1,
            "urgency": _coerce_score(block.get("urgency")) or 1,
            "complexity": _coerce_score(block.get("complexity")) or 1,
        }
    choice_raw = payload.get("choice") or ""
    choice = choice_raw if choice_raw in valid_option_keys() else None
    return {"scores": scores, "choice": choice}


# --------------------------- Расчёты ---------------------------


def compute_wsjf(block: Dict) -> float:
    """priority = (value + urgency) / complexity, с защитой от деления на 0."""
    v = float(block.get("value") or 1)
    u = float(block.get("urgency") or 1)
    c = float(block.get("complexity") or 1)
    if c <= 0:
        c = 1.0
    return round((v + u) / c, 2)


def evaluate_round(role_key: str, round_data: Dict) -> Dict:
    """Считает WSJF по опциям, рекомендуемый выбор и подсвечивает типовые
    ошибки новичка.

    Возвращает:
      - wsjf:             { option_key: float }
      - ranking:          [option_key, ...] отсортированный по WSJF убыв.
      - recommended:      option_key с лучшим WSJF
      - choice:           что реально выбрал пользователь
      - errors:           список ключей типовых ошибок
      - warnings_per_opt: { option_key: [warning_key, ...] }
    """

    data = sanitize_round(round_data)
    scores = data["scores"]
    choice = data["choice"]

    wsjf = {key: compute_wsjf(scores[key]) for key in scores}
    ranking = sorted(wsjf.keys(), key=lambda k: (-wsjf[k], k))
    recommended = ranking[0] if ranking else None

    errors: List[str] = []
    warnings_per_opt: Dict[str, List[str]] = {k: [] for k in scores}

    for opt in OPTIONS:
        exp = opt["expected_scores"]
        cur = scores[opt["key"]]
        # Недооценка рисков: complexity сильно ниже, чем ожидается (разница ≥ 5).
        if exp["complexity"] - cur["complexity"] >= 5:
            warnings_per_opt[opt["key"]].append("undervalued_complexity")
        # Игнорирование срочности: поставил 1-2 там, где эксперт ждёт 8+.
        if exp["urgency"] >= 8 and cur["urgency"] <= 2:
            warnings_per_opt[opt["key"]].append("ignored_urgency")
        # Переоценка водорода как «быстрого»: complexity <=2 или time <=2 у hydrogen.
        if opt["key"] == "hydrogen" and cur["complexity"] <= 2:
            warnings_per_opt[opt["key"]].append("hydrogen_too_easy")

    # Глобальные ошибки
    for opt_key, wlist in warnings_per_opt.items():
        if "undervalued_complexity" in wlist and "undervalued_complexity" not in errors:
            errors.append("undervalued_risk")
        if "ignored_urgency" in wlist and "ignored_urgency" not in errors:
            errors.append("ignored_urgency")
    if choice and recommended and choice != recommended:
        errors.append("math_blind")
    # Ролевые смещения
    if role_key == "business" and choice == "hydrogen":
        errors.append("role_mismatch_business_hydrogen")
    if role_key == "engineer" and choice == "hydrogen" and scores["hydrogen"]["complexity"] <= 3:
        errors.append("role_mismatch_engineer_too_easy")

    return {
        "wsjf": wsjf,
        "ranking": ranking,
        "recommended": recommended,
        "choice": choice,
        "errors": errors,
        "warnings_per_option": warnings_per_opt,
    }


# --------------------------- Последствия ---------------------------


CONSEQUENCES: Dict[str, Dict] = {
    "hybrid": {
        "gained_keys": ["gain.quick_revenue", "gain.proven_tech"],
        "lost_keys": ["loss.weak_future", "loss.market_shift_risk"],
        "summary_key": "summary.hybrid",
    },
    "electric": {
        "gained_keys": ["gain.balance", "gain.market_growth", "gain.contract_secured"],
        "lost_keys": ["loss.tech_risk", "loss.capex"],
        "summary_key": "summary.electric",
    },
    "hydrogen": {
        "gained_keys": ["gain.breakthrough", "gain.first_mover"],
        "lost_keys": ["loss.long_dry_period", "loss.tech_risk_high"],
        "summary_key": "summary.hydrogen",
    },
}


def simulate_outcome(choice: Optional[str]) -> Dict:
    """Возвращает текстовый результат выбора — блок с плюсами и минусами
    варианта. Локализация на клиенте по ключам."""
    if not choice or choice not in CONSEQUENCES:
        return {"gained": [], "lost": [], "summary_key": None}
    c = CONSEQUENCES[choice]
    return {
        "gained": list(c["gained_keys"]),
        "lost": list(c["lost_keys"]),
        "summary_key": c["summary_key"],
    }


# --------------------------- Адаптация ---------------------------


def analyze_adaptation(
    initial_choice: Optional[str],
    revised_choice: Optional[str],
    event: Optional[Dict],
) -> Dict:
    """По паре первый/второй выбор и случившемуся событию возвращает
    один из статусов адаптации:

      - stayed_right:   не поменял, и решение совпало с тем, что
                        событие делает более привлекательным;
      - stayed_risky:   не поменял, хотя событие делало текущий выбор
                        менее привлекательным;
      - adapted_well:   поменял на вариант, который событие сделало
                        более привлекательным;
      - over_adjusted:  поменял, но ушёл не в ту сторону;
      - no_change:      пользователь не дошёл до пересмотра — используем
                        как дефолт.
    """
    favors = (event or {}).get("favors")
    if not revised_choice:
        status = "no_change"
    elif initial_choice == revised_choice:
        if favors and favors == initial_choice:
            status = "stayed_right"
        else:
            status = "stayed_risky"
    else:
        if favors and revised_choice == favors:
            status = "adapted_well"
        else:
            status = "over_adjusted"
    return {"status": status, "favors": favors}
