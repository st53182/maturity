"""Контент тренажёра приоритизации RICE с «грязным» контекстом.

RICE = Reach * Impact * Confidence / Effort
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set


ROLES: List[Dict] = [
    {
        "key": "growth",
        "title": {"ru": "Growth", "en": "Growth"},
        "focus": {"ru": "Быстрый рост", "en": "Fast growth"},
        "desc": {
            "ru": "Ты давишь на охват и активацию, даже если сигнал пока шумный.",
            "en": "You push reach and activation even when the signal is noisy.",
        },
    },
    {
        "key": "product",
        "title": {"ru": "Product", "en": "Product"},
        "focus": {"ru": "Ценность и устойчивость", "en": "Value and sustainability"},
        "desc": {
            "ru": "Ты балансируешь влияние на пользователя и реалистичность доставки.",
            "en": "You balance user impact and realistic delivery.",
        },
    },
    {
        "key": "engineering",
        "title": {"ru": "Engineering", "en": "Engineering"},
        "focus": {"ru": "Надёжность поставки", "en": "Delivery reliability"},
        "desc": {
            "ru": "Ты смотришь на effort, риски и техдолг, чтобы не сжечь команду.",
            "en": "You watch effort, risk, and tech debt to avoid burning the team.",
        },
    },
]


OPTIONS: List[Dict] = [
    {
        "key": "smart_onboarding",
        "title": {"ru": "Умный онбординг", "en": "Smart onboarding"},
        "short": {"ru": "Средний охват, понятный impact", "en": "Medium reach, clear impact"},
        "description": {
            "ru": "Часть аналитики противоречива: воронка проседает в 2 местах, но сегменты собраны криво.",
            "en": "Analytics is contradictory: funnel drops in two places, but segmentation is messy.",
        },
        "revenue_label": {"ru": "рост активации", "en": "activation growth"},
        "time_label": {"ru": "~4 недели", "en": "~4 weeks"},
        "expected_scores": {"reach": 5000, "impact": 2.0, "confidence": 0.7, "effort": 4},
        "rice_clues": {
            "ru": [
                "Reach: онбординг затрагивает почти весь новый трафик (~4-6k новых пользователей/мес), но часть каналов размечена криво.",
                "Impact: если убрать 2 главных шага трения, активация обычно растёт заметно; эффект средний/выше среднего.",
                "Confidence: есть поведенческие данные и записи сессий, но сегментация частично «грязная» — уверенность не максимальная.",
                "Effort: 2 клиента + 1 backend endpoint + аналитика событий; реалистично 3-5 недель.",
            ],
            "en": [
                "Reach: onboarding touches most new traffic (~4-6k new users/month), but some channels are mislabeled.",
                "Impact: removing two key friction steps usually improves activation; impact is medium to high.",
                "Confidence: there is behavioral data and session recordings, but segmentation is partly noisy.",
                "Effort: two clients + one backend endpoint + analytics events; realistically 3-5 weeks.",
            ],
        },
        "strengths": {
            "ru": ["Быстрый запуск", "Есть наблюдаемая проблема", "Низкий технологический риск"],
            "en": ["Fast launch", "Observable problem exists", "Low tech risk"],
        },
        "risks": {
            "ru": ["Данные частично грязные", "Есть сезонный шум"],
            "en": ["Data is partially noisy", "There is seasonal noise"],
        },
    },
    {
        "key": "referral_rework",
        "title": {"ru": "Пересборка рефералки", "en": "Referral rework"},
        "short": {"ru": "Большой reach, низкая уверенность", "en": "Large reach, low confidence"},
        "description": {
            "ru": "Маркетинг обещает взрывной рост, но A/B тест старый и проводился на другой аудитории.",
            "en": "Marketing promises breakout growth, but the A/B test is old and from a different audience.",
        },
        "revenue_label": {"ru": "виральный рост", "en": "viral growth"},
        "time_label": {"ru": "~7 недель", "en": "~7 weeks"},
        "expected_scores": {"reach": 14000, "impact": 1.2, "confidence": 0.45, "effort": 8},
        "rice_clues": {
            "ru": [
                "Reach: маркетинг обещает до 14k, но цифра основана на старом A/B и другой аудитории; возможен сильный оверэстимейт.",
                "Impact: виральность может дать рост MAU, но на core-ретеншн влияет слабо.",
                "Confidence: источник данных слабый (устаревший тест + сменившийся канал трафика), уверенность низкая.",
                "Effort: нужно переделывать механику и антифрод/лимиты, плюс саппорт потоков — 6-9 недель.",
            ],
            "en": [
                "Reach: marketing promises up to 14k, but the estimate is from an old A/B test on a different audience.",
                "Impact: virality can move MAU, but effect on core retention is limited.",
                "Confidence: evidence quality is weak (outdated test + changed acquisition mix), confidence should be low.",
                "Effort: mechanics rewrite + anti-fraud/rate limits + support load, typically 6-9 weeks.",
            ],
        },
        "strengths": {
            "ru": ["Потенциально высокий охват", "Понятно для коммуникации с инвестором"],
            "en": ["Potentially high reach", "Easy to communicate to investors"],
        },
        "risks": {
            "ru": ["Слабая доказательная база", "Риск накрутить некачественный трафик"],
            "en": ["Weak evidence", "Risk of low-quality traffic inflation"],
        },
    },
    {
        "key": "search_quality",
        "title": {"ru": "Качество поиска", "en": "Search quality improvement"},
        "short": {"ru": "Ниже reach, высокий impact", "en": "Lower reach, higher impact"},
        "description": {
            "ru": "Жалобы от power users подтверждены, но метрика поиска сломана на iOS после релиза SDK.",
            "en": "Power-user complaints are real, but the search metric is broken on iOS after SDK rollout.",
        },
        "revenue_label": {"ru": "удержание core", "en": "core retention"},
        "time_label": {"ru": "~6 недель", "en": "~6 weeks"},
        "expected_scores": {"reach": 3000, "impact": 3.0, "confidence": 0.6, "effort": 5},
        "rice_clues": {
            "ru": [
                "Reach: затрагивает меньший сегмент (~2.5-3.5k активных core users), а не весь MAU.",
                "Impact: для этого сегмента влияние высокое — поиск на критическом пути и напрямую бьёт в churn.",
                "Confidence: часть iOS-метрик сломана, но жалобы и тикеты саппорта подтверждают проблему.",
                "Effort: потребуется индексация + ranking + правка iOS SDK, обычно 4-6 недель.",
            ],
            "en": [
                "Reach: affects a smaller segment (~2.5-3.5k active core users), not the whole MAU.",
                "Impact: impact is high for this segment; search is on a critical path and tied to churn.",
                "Confidence: some iOS metrics are broken, but complaints and support tickets confirm the issue.",
                "Effort: indexing + ranking + iOS SDK fixes, usually 4-6 weeks.",
            ],
        },
        "strengths": {
            "ru": ["Сильный эффект на удержание", "Улучшение ключевого UX"],
            "en": ["Strong retention effect", "Improves key UX"],
        },
        "risks": {
            "ru": ["Часть телеметрии недостоверна", "Эффект сложнее продать стейкхолдерам"],
            "en": ["Part of telemetry is unreliable", "Harder to sell to stakeholders"],
        },
    },
]


EVENTS: List[Dict] = [
    {
        "key": "tracking_fixed",
        "title": {"ru": "Починили трекинг и пересобрали сегменты", "en": "Tracking fixed and segments rebuilt"},
        "lead": {
            "ru": "Оказалось, reach рефералки был переоценен почти в 2 раза.",
            "en": "Referral reach was overestimated by almost 2x.",
        },
        "favors": "smart_onboarding",
    },
    {
        "key": "investor_pressure",
        "title": {"ru": "Инвестор давит на «видимый рост»", "en": "Investor pushes for visible growth"},
        "lead": {
            "ru": "Требуют рост MAU в ближайшие 6 недель, tolerance к риску вырос.",
            "en": "They demand MAU growth in 6 weeks, risk tolerance increased.",
        },
        "favors": "referral_rework",
    },
    {
        "key": "churn_alert",
        "title": {"ru": "Алерт по churn у power users", "en": "Power-user churn alert"},
        "lead": {
            "ru": "Отток core-сегмента ускоряется, impact поиска оказался выше оценки.",
            "en": "Core-segment churn accelerates; search impact is higher than expected.",
        },
        "favors": "search_quality",
    },
]


def valid_role_keys() -> Set[str]:
    return {r["key"] for r in ROLES}


def valid_option_keys() -> Set[str]:
    return {o["key"] for o in OPTIONS}


def valid_event_keys() -> Set[str]:
    return {e["key"] for e in EVENTS}


def pick_event_for_choice(initial_choice: Optional[str]) -> Dict:
    mapping = {
        "smart_onboarding": "investor_pressure",
        "referral_rework": "tracking_fixed",
        "search_quality": "investor_pressure",
    }
    target = mapping.get(initial_choice or "", "tracking_fixed")
    for e in EVENTS:
        if e["key"] == target:
            return e
    return EVENTS[0]


def _f01(v, default: float) -> float:
    try:
        x = float(v)
    except Exception:
        return default
    return max(0.1, min(1.0, x))


def _num(v, default: int) -> int:
    try:
        return max(1, int(v))
    except Exception:
        return default


def normalize_score_block(block) -> Dict[str, float]:
    b = block if isinstance(block, dict) else {}
    return {
        "reach": float(_num(b.get("reach"), 1)),
        "impact": float(b.get("impact") if isinstance(b.get("impact"), (int, float)) else 1.0),
        "confidence": float(_f01(b.get("confidence"), 0.5)),
        "effort": float(_num(b.get("effort"), 1)),
    }


def sanitize_round(payload: Dict) -> Dict:
    payload = payload if isinstance(payload, dict) else {}
    raw_scores = payload.get("scores") or {}
    scores: Dict[str, Dict[str, float]] = {}
    for opt in OPTIONS:
        block = raw_scores.get(opt["key"]) if isinstance(raw_scores, dict) else None
        scores[opt["key"]] = normalize_score_block(block)
    choice_raw = payload.get("choice") or ""
    choice = choice_raw if choice_raw in valid_option_keys() else None
    return {"scores": scores, "choice": choice}


def compute_rice(block: Dict) -> float:
    b = normalize_score_block(block)
    score = (b["reach"] * b["impact"] * b["confidence"]) / max(1.0, b["effort"])
    return round(score, 2)


def evaluate_round(role_key: str, round_data: Dict) -> Dict:
    data = sanitize_round(round_data)
    scores = data["scores"]
    choice = data["choice"]
    rice = {key: compute_rice(scores[key]) for key in scores}
    ranking = sorted(rice.keys(), key=lambda k: (-rice[k], k))
    recommended = ranking[0] if ranking else None
    errors: List[str] = []
    warnings_per_opt: Dict[str, List[str]] = {k: [] for k in scores}

    for opt in OPTIONS:
        exp = opt["expected_scores"]
        cur = scores[opt["key"]]
        if cur["confidence"] > exp["confidence"] + 0.35:
            warnings_per_opt[opt["key"]].append("overconfident_signal")
        if cur["effort"] <= max(1, exp["effort"] - 3):
            warnings_per_opt[opt["key"]].append("effort_too_low")
    for _, wlist in warnings_per_opt.items():
        for w in wlist:
            if w not in errors:
                errors.append(w)
    if choice and recommended and choice != recommended:
        errors.append("math_blind")
    if role_key == "engineering" and choice == "referral_rework":
        errors.append("role_mismatch_engineering_growth_bet")

    # Для совместимости со старым UI оставляем ключ `wsjf`.
    return {
        "wsjf": rice,
        "ranking": ranking,
        "recommended": recommended,
        "choice": choice,
        "errors": errors,
        "warnings_per_option": warnings_per_opt,
    }


CONSEQUENCES = {
    "smart_onboarding": {
        "gained_keys": ["gain.quick_activation", "gain.clean_learning"],
        "lost_keys": ["loss.not_biggest_reach"],
        "summary_key": "summary.onboarding",
    },
    "referral_rework": {
        "gained_keys": ["gain.visible_growth"],
        "lost_keys": ["loss.low_confidence_bet", "loss.quality_risk"],
        "summary_key": "summary.referral",
    },
    "search_quality": {
        "gained_keys": ["gain.core_retention", "gain.product_quality"],
        "lost_keys": ["loss.harder_to_explain"],
        "summary_key": "summary.search",
    },
}


def simulate_outcome(choice: Optional[str]) -> Dict:
    if not choice or choice not in CONSEQUENCES:
        return {"gained": [], "lost": [], "summary_key": None}
    c = CONSEQUENCES[choice]
    return {"gained": list(c["gained_keys"]), "lost": list(c["lost_keys"]), "summary_key": c["summary_key"]}


def analyze_adaptation(initial_choice: Optional[str], revised_choice: Optional[str], event: Optional[Dict]) -> Dict:
    favors = (event or {}).get("favors")
    if not revised_choice:
        status = "no_change"
    elif initial_choice == revised_choice:
        status = "stayed_right" if favors and favors == initial_choice else "stayed_risky"
    else:
        status = "adapted_well" if favors and revised_choice == favors else "over_adjusted"
    return {"status": status, "favors": favors}


def get_content_for_locale(locale: str) -> Dict:
    loc = "en" if locale == "en" else "ru"
    return {
        "scale": [1, 2, 3, 5, 8, 13],
        "roles": [
            {"key": r["key"], "title": r["title"][loc], "focus": r["focus"][loc], "desc": r["desc"][loc]}
            for r in ROLES
        ],
        "options": [
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
                "rice_clues": list(o.get("rice_clues", {}).get(loc, [])),
            }
            for o in OPTIONS
        ],
        "events": [
            {"key": e["key"], "title": e["title"][loc], "lead": e["lead"][loc], "favors": e["favors"], "shifts": []}
            for e in EVENTS
        ],
        "context": {
            "title": "Приоритизация RICE в грязном контексте" if loc == "ru" else "RICE prioritization in a noisy context",
            "lead": (
                "Часть метрик сломана, часть гипотез устарела, стейкхолдеры давят в разные стороны. "
                "Нужно выбрать, что делать первым, не притворяясь, что данные идеальны."
                if loc == "ru"
                else "Some metrics are broken, some hypotheses are stale, and stakeholders pull in different directions. "
                     "Pick what to do first without pretending data is perfect."
            ),
        },
        "formula": "RICE = Reach × Impact × Confidence / Effort",
    }
