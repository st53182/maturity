"""Контент тренажёра Definition of Ready / Definition of Done.

Структура:
  - TEAM_TYPES — 3 контекста команд (IT, marketing, ops/сервис), для каждой
    задано короткое описание и набор `priority_effects` — эффектов, которые
    *особенно* важны для этого типа команды (подсвечиваются на экране 5).
  - RULES — 12 карточек правил. У каждого:
        expected_column: "dor" | "dod" | "either"  — ожидаемая колонка
                         по «классической» интерпретации DoR/DoD;
        is_critical:     нужно ли обязательно включать (чтобы хотя бы
                         минимальная дисциплина существовала);
        maps_to:         список ключей эффектов, которые это правило
                         реально создаёт (экспертная связка rule → effect).
  - EFFECTS — 9 эффектов (зачем это нужно). У одного из них
        `provocative = True` — «ускорение работы»: на самом деле DoR/DoD
        сначала *замедляют*, поэтому считать этот эффект прямым следствием
        неверно. Мы специально оставляем его в списке для провокации.

Логика скоринга (`evaluate_round`) и симуляции (`simulate_outcome`) —
чистая, без побочек, возвращает локализуемые ключи для фронта.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple


# --------------------------- Типы команд ---------------------------


TEAM_TYPES: List[Dict] = [
    {
        "key": "it",
        "title": {"ru": "IT-команда", "en": "IT team"},
        "short": {
            "ru": "Разработка цифрового продукта",
            "en": "Digital product development",
        },
        "context": {
            "ru": "Команда разрабатывает цифровой продукт. Есть разработчики, тестировщики, аналитики. Важны качество кода и минимум багов в продакшене.",
            "en": "The team builds a digital product. Developers, QAs and analysts on board. Code quality and few production bugs matter.",
        },
        # Эффекты, на которые этой команде особенно важно обратить внимание.
        "priority_effects": ["defects", "predictability", "quality", "rework"],
    },
    {
        "key": "marketing",
        "title": {"ru": "Маркетинг / контент", "en": "Marketing / content"},
        "short": {
            "ru": "Кампании и контент",
            "en": "Campaigns and content",
        },
        "context": {
            "ru": "Команда запускает рекламные кампании и создаёт контент. Важно быстро выпускать материалы, согласовывать их и не переделывать по 5 раз.",
            "en": "The team launches campaigns and creates content. Speed of release, alignment with stakeholders and no endless rework matter.",
        },
        "priority_effects": ["rework", "clear_result", "unity", "blockers"],
    },
    {
        "key": "ops",
        "title": {"ru": "Операции / сервис / гос", "en": "Ops / service / gov"},
        "short": {
            "ru": "Процессы и клиенты",
            "en": "Processes and clients",
        },
        "context": {
            "ru": "Команда работает с процессами и клиентами (например, госуслуги или сервисный центр). Важны качество, стабильность и соблюдение регламентов.",
            "en": "The team deals with processes and clients (e.g. government services or a service center). Quality, stability and compliance matter.",
        },
        "priority_effects": ["quality", "clear_result", "less_chaos", "predictability"],
    },
]


def valid_team_keys() -> Set[str]:
    return {t["key"] for t in TEAM_TYPES}


# --------------------------- Правила ---------------------------


# expected_column: "dor" | "dod" | "either"
# is_critical:     эти правила должны быть где-то — без них сложно жить.
RULES: List[Dict] = [
    {
        "key": "clear_task",
        "title": {
            "ru": "Задача понятна всей команде",
            "en": "The task is clear to the whole team",
        },
        "desc": {
            "ru": "Все понимают, что именно делаем и зачем",
            "en": "Everyone understands what we are doing and why",
        },
        "expected_column": "dor",
        "is_critical": True,
        "maps_to": ["unity", "rework", "less_chaos"],
    },
    {
        "key": "acceptance_criteria",
        "title": {"ru": "Есть критерии приёмки", "en": "Acceptance criteria exist"},
        "desc": {
            "ru": "Чёткие признаки того, что задача сделана",
            "en": "Clear signs that the task is done",
        },
        "expected_column": "dor",
        "is_critical": True,
        "maps_to": ["rework", "defects", "clear_result"],
    },
    {
        "key": "materials_ready",
        "title": {
            "ru": "Есть все необходимые материалы",
            "en": "All required materials are ready",
        },
        "desc": {
            "ru": "Макеты, доступы, контент, спецификации",
            "en": "Mockups, access, content, specs",
        },
        "expected_column": "dor",
        "is_critical": False,
        "maps_to": ["blockers", "predictability"],
    },
    {
        "key": "stakeholders_aligned",
        "title": {
            "ru": "Согласованы заинтересованные стороны",
            "en": "Stakeholders are aligned",
        },
        "desc": {
            "ru": "Все, кого касается задача, в курсе и согласны",
            "en": "Everyone impacted knows and agrees",
        },
        "expected_column": "dor",
        "is_critical": False,
        "maps_to": ["rework", "clear_result"],
    },
    {
        "key": "no_dependencies",
        "title": {"ru": "Нет блокирующих зависимостей", "en": "No blocking dependencies"},
        "desc": {
            "ru": "Нет ожидания чужой работы или внешних ответов",
            "en": "No waiting for external work or answers",
        },
        "expected_column": "dor",
        "is_critical": False,
        "maps_to": ["blockers", "predictability"],
    },
    {
        "key": "decomposed",
        "title": {"ru": "Задача декомпозирована", "en": "Task is decomposed"},
        "desc": {
            "ru": "Разбита на маленькие, управляемые шаги",
            "en": "Broken into small, manageable steps",
        },
        "expected_column": "dor",
        "is_critical": False,
        "maps_to": ["predictability", "unity"],
    },
    {
        "key": "brings_value",
        "title": {"ru": "Задача приносит ценность", "en": "The task brings value"},
        "desc": {
            "ru": "Мы понимаем, ради чего её вообще делаем",
            "en": "We know why we are doing it at all",
        },
        "expected_column": "either",
        "is_critical": False,
        "maps_to": ["less_chaos", "clear_result"],
    },
    {
        "key": "tested",
        "title": {"ru": "Задача протестирована", "en": "The task is tested"},
        "desc": {
            "ru": "Прогнали все проверки и сценарии",
            "en": "All checks and scenarios have been run",
        },
        "expected_column": "dod",
        "is_critical": True,
        "maps_to": ["defects", "quality"],
    },
    {
        "key": "peer_reviewed",
        "title": {"ru": "Результат проверен", "en": "Result is peer-reviewed"},
        "desc": {
            "ru": "Коллега проверил результат до сдачи",
            "en": "A colleague reviewed the result before delivery",
        },
        "expected_column": "dod",
        "is_critical": False,
        "maps_to": ["quality", "rework"],
    },
    {
        "key": "no_blockers",
        "title": {"ru": "Нет критических ошибок", "en": "No critical defects"},
        "desc": {
            "ru": "Ни одной блокирующей ошибки на выходе",
            "en": "No blocking defects remain",
        },
        "expected_column": "dod",
        "is_critical": True,
        "maps_to": ["quality", "defects"],
    },
    {
        "key": "documented",
        "title": {"ru": "Результат задокументирован", "en": "Result is documented"},
        "desc": {
            "ru": "Есть след работы: где, что, как использовать",
            "en": "There is a trail of work: where, what, how to use",
        },
        "expected_column": "dod",
        "is_critical": False,
        "maps_to": ["clear_result", "less_chaos"],
    },
    {
        "key": "accepted",
        "title": {"ru": "Результат принят заказчиком", "en": "Result is accepted by the client"},
        "desc": {
            "ru": "Стейкхолдер подтвердил, что всё ок",
            "en": "Stakeholder confirmed everything is ok",
        },
        "expected_column": "dod",
        "is_critical": False,
        "maps_to": ["rework", "clear_result"],
    },
    {
        "key": "risks_identified",
        "title": {"ru": "Известны основные риски", "en": "Main risks are known"},
        "desc": {
            "ru": "Команда понимает, что может пойти не так",
            "en": "The team knows what could go wrong",
        },
        "expected_column": "dor",
        "is_critical": False,
        "maps_to": ["predictability", "less_chaos"],
    },
    {
        "key": "success_metrics",
        "title": {
            "ru": "Есть метрики успеха",
            "en": "Success metrics defined",
        },
        "desc": {
            "ru": "Понятно, как измерим, что задача удалась",
            "en": "It is clear how we measure success",
        },
        "expected_column": "dor",
        "is_critical": False,
        "maps_to": ["clear_result", "unity"],
    },
    {
        "key": "estimation_done",
        "title": {
            "ru": "Задача оценена по трудоёмкости",
            "en": "Task is estimated",
        },
        "desc": {
            "ru": "Есть хотя бы грубая оценка усилий",
            "en": "There is at least a rough effort estimate",
        },
        "expected_column": "dor",
        "is_critical": False,
        "maps_to": ["predictability"],
    },
    {
        "key": "user_tested",
        "title": {
            "ru": "Проверено пользователем",
            "en": "Validated with end user",
        },
        "desc": {
            "ru": "Конечный пользователь убедился, что всё работает",
            "en": "End user confirmed it actually works",
        },
        "expected_column": "dod",
        "is_critical": False,
        "maps_to": ["rework", "clear_result"],
    },
    {
        "key": "rollback_plan",
        "title": {
            "ru": "Есть план отката",
            "en": "Rollback plan exists",
        },
        "desc": {
            "ru": "Понятно, как вернуть всё назад, если что-то сломается",
            "en": "We know how to roll back if something breaks",
        },
        "expected_column": "dod",
        "is_critical": False,
        "maps_to": ["defects", "less_chaos"],
    },
    {
        "key": "handed_off",
        "title": {
            "ru": "Результат передан в эксплуатацию",
            "en": "Handed off to operations",
        },
        "desc": {
            "ru": "Результат передан тем, кто будет с ним жить дальше",
            "en": "Handed off to whoever operates it next",
        },
        "expected_column": "dod",
        "is_critical": False,
        "maps_to": ["blockers", "clear_result"],
    },
]


def valid_rule_keys() -> Set[str]:
    return {r["key"] for r in RULES}


def _rule(key: str) -> Optional[Dict]:
    for r in RULES:
        if r["key"] == key:
            return r
    return None


# --------------------------- Эффекты ---------------------------


EFFECTS: List[Dict] = [
    {
        "key": "unity",
        "title": {"ru": "Единое понимание задачи", "en": "Shared understanding"},
        "desc": {
            "ru": "Все участники одинаково понимают, что делаем",
            "en": "Everyone understands the task the same way",
        },
        "provocative": False,
    },
    {
        "key": "rework",
        "title": {"ru": "Меньше переделок", "en": "Less rework"},
        "desc": {
            "ru": "Реже возвращаемся к тому, что уже было сделано",
            "en": "Rarely revisit what was already done",
        },
        "provocative": False,
    },
    {
        "key": "defects",
        "title": {"ru": "Меньше ошибок", "en": "Fewer defects"},
        "desc": {
            "ru": "В результат доходит меньше багов и проблем",
            "en": "Fewer bugs and issues reach the result",
        },
        "provocative": False,
    },
    {
        "key": "predictability",
        "title": {"ru": "Предсказуемые сроки", "en": "Predictable timelines"},
        "desc": {
            "ru": "Мы чаще укладываемся в договорённости",
            "en": "We hit our commitments more often",
        },
        "provocative": False,
    },
    {
        "key": "blockers",
        "title": {"ru": "Меньше блокировок", "en": "Fewer blockers"},
        "desc": {
            "ru": "Реже ждём чужой работы или внешних ответов",
            "en": "Less waiting for external work or answers",
        },
        "provocative": False,
    },
    {
        "key": "clear_result",
        "title": {"ru": "Понятный результат", "en": "Clear outcome"},
        "desc": {
            "ru": "Результат прозрачный и принимаемый",
            "en": "The result is transparent and acceptable",
        },
        "provocative": False,
    },
    {
        "key": "quality",
        "title": {"ru": "Улучшение качества", "en": "Better quality"},
        "desc": {
            "ru": "Конечный результат становится надёжнее",
            "en": "The final result is more reliable",
        },
        "provocative": False,
    },
    {
        "key": "less_chaos",
        "title": {"ru": "Снижение хаоса", "en": "Less chaos"},
        "desc": {
            "ru": "Работа идёт осознанно, меньше суеты",
            "en": "Work becomes more intentional, less frantic",
        },
        "provocative": False,
    },
    {
        "key": "speed",
        "title": {"ru": "Ускорение работы", "en": "Faster delivery"},
        "desc": {
            "ru": "Провокация: DoR/DoD часто сначала замедляют, а не ускоряют",
            "en": "Provocation: DoR/DoD usually slow things down first, not speed up",
        },
        "provocative": True,
    },
]


def valid_effect_keys() -> Set[str]:
    return {e["key"] for e in EFFECTS}


# --------------------------- Локализованный дамп ---------------------------


def get_content_for_locale(locale: str) -> Dict:
    loc = "en" if locale == "en" else "ru"
    teams = []
    for t in TEAM_TYPES:
        teams.append({
            "key": t["key"],
            "title": t["title"][loc],
            "short": t["short"][loc],
            "context": t["context"][loc],
            "priority_effects": list(t["priority_effects"]),
        })
    rules = []
    for r in RULES:
        rules.append({
            "key": r["key"],
            "title": r["title"][loc],
            "desc": r["desc"][loc],
            "expected_column": r["expected_column"],
            "is_critical": bool(r["is_critical"]),
        })
    effects = []
    for e in EFFECTS:
        effects.append({
            "key": e["key"],
            "title": e["title"][loc],
            "desc": e["desc"][loc],
            "provocative": bool(e["provocative"]),
        })
    return {
        "teams": teams,
        "rules": rules,
        "effects": effects,
    }


# --------------------------- Нормализация ответа ---------------------------


VALID_COLUMNS = {"dor", "dod"}


def _sanitize_mapping(mapping_raw: Dict) -> Dict[str, List[str]]:
    """Приводит mapping {rule_key: [effect_key, ...]} к валидному виду."""
    rule_keys = valid_rule_keys()
    eff_keys = valid_effect_keys()
    out: Dict[str, List[str]] = {}
    if not isinstance(mapping_raw, dict):
        return out
    for rk, ev in mapping_raw.items():
        if rk not in rule_keys or not isinstance(ev, list):
            continue
        seen = []
        for e in ev:
            if isinstance(e, str) and e in eff_keys and e not in seen:
                seen.append(e)
        out[rk] = seen
    return out


def sanitize_round(payload: Dict) -> Dict:
    """Берёт «сырой» JSON от фронта и возвращает каноничную структуру:

    {
      "dor": [rule_key, ...],
      "dod": [rule_key, ...],
      "mapping": { rule_key: [effect_key, ...] }
    }
    """
    if not isinstance(payload, dict):
        payload = {}
    rule_keys = valid_rule_keys()
    dor: List[str] = []
    dod: List[str] = []
    seen: Set[str] = set()
    for k in (payload.get("dor") or []):
        if isinstance(k, str) and k in rule_keys and k not in seen:
            dor.append(k)
            seen.add(k)
    for k in (payload.get("dod") or []):
        if isinstance(k, str) and k in rule_keys and k not in seen:
            dod.append(k)
            seen.add(k)
    mapping = _sanitize_mapping(payload.get("mapping") or {})
    # mapping должен содержать только правила, которые реально выбраны
    mapping = {k: v for k, v in mapping.items() if k in seen}
    return {"dor": dor, "dod": dod, "mapping": mapping}


# --------------------------- Оценка раунда ---------------------------


def _team(team_key: str) -> Optional[Dict]:
    for t in TEAM_TYPES:
        if t["key"] == team_key:
            return t
    return None


def _classify_rule_placement(rule: Dict, column: str) -> str:
    """Возвращает одно из: 'ok' | 'mismatch' | 'neutral'.

    * ok       — правило стоит там, где его традиционно ждут;
    * mismatch — стоит в явно «не своей» колонке (DoR правило в DoD или
                 наоборот). Это не «ошибка», но повод задать вопрос.
    * neutral  — правило помечено `either`, ему всё равно.
    """
    exp = rule["expected_column"]
    if exp == "either":
        return "neutral"
    if column == exp:
        return "ok"
    return "mismatch"


def evaluate_round(team_key: str, round_data: Dict) -> Dict:
    """Основная оценочная функция.

    Возвращает словарь с информацией о раскладке и качестве маппинга
    правил на эффекты. Локализация — на клиенте.

    Поля:
      - dor_count / dod_count
      - critical_missing: список ключей критичных правил, которые не
        включены ни в DoR, ни в DoD
      - mismatched: список {rule, in_column, expected} для правил,
        стоящих не в «своей» колонке
      - mapping_insights: для каждого выбранного правила — экспертно
        ожидаемые эффекты и отмеченные пользователем, разбитые на:
          * aligned   — правило ↔ эффект совпали с экспертной связкой
          * extra     — пользователь отметил эффект, которого эксперт
                        не ожидает (может быть спорным)
          * provocative — пользователь отметил провокационный эффект
                        (например «ускорение»); отдельно подсвечиваем
      - priority_effects_covered: какие priority-эффекты для типа команды
        пользователь связал хотя бы с одним выбранным правилом
      - antipatterns: ключи типичных ошибок (см. simulate_outcome)
      - score_raw / score_max — доли (для агрегаций).
    """

    data = sanitize_round(round_data)
    team = _team(team_key)
    selected: List[str] = data["dor"] + data["dod"]
    selected_set = set(selected)

    critical_missing = [
        r["key"] for r in RULES if r["is_critical"] and r["key"] not in selected_set
    ]

    mismatched = []
    for col in ("dor", "dod"):
        for rk in data[col]:
            r = _rule(rk)
            if not r:
                continue
            kind = _classify_rule_placement(r, col)
            if kind == "mismatch":
                mismatched.append({
                    "rule": rk,
                    "in_column": col,
                    "expected_column": r["expected_column"],
                })

    # Mapping insights
    mapping_insights: List[Dict] = []
    aligned_total = 0
    aligned_max = 0
    priority_effects_hit: Set[str] = set()
    provocative_picks = 0
    for rk in selected:
        r = _rule(rk)
        if not r:
            continue
        picked = list(data["mapping"].get(rk) or [])
        expected = list(r["maps_to"])
        aligned = [e for e in picked if e in expected]
        extra = [e for e in picked if e not in expected and e != "speed"]
        provocative = [e for e in picked if e == "speed"]
        aligned_total += len(aligned)
        aligned_max += len(expected)
        provocative_picks += len(provocative)
        if team:
            for e in picked:
                if e in team["priority_effects"]:
                    priority_effects_hit.add(e)
        mapping_insights.append({
            "rule": rk,
            "expected": expected,
            "picked": picked,
            "aligned": aligned,
            "extra": extra,
            "provocative": provocative,
        })

    # Антипаттерны
    antipatterns: List[str] = []
    if len(data["dor"]) >= 8:
        antipatterns.append("dor_too_strict")
    if len(data["dor"]) <= 1:
        antipatterns.append("dor_too_soft")
    if len(data["dod"]) <= 1:
        antipatterns.append("dod_too_weak")
    if len(mismatched) >= 3:
        antipatterns.append("dor_dod_mixed")
    if critical_missing:
        antipatterns.append("critical_missing")
    if provocative_picks >= 2:
        antipatterns.append("speed_illusion")
    # Правило "задача приносит ценность" упало только в DoD — теряется смысл
    if "brings_value" in data["dod"] and "brings_value" not in data["dor"]:
        antipatterns.append("value_too_late")

    score_raw = float(aligned_total)
    # штраф за mismatch (0.5) и за провокационные выборы (0.5)
    score_raw -= 0.5 * len(mismatched)
    score_raw -= 0.5 * provocative_picks
    # бонус за покрытие критичных правил
    score_raw += sum(1 for r in RULES if r["is_critical"] and r["key"] in selected_set)
    if score_raw < 0:
        score_raw = 0.0
    score_max = float(aligned_max) + sum(1 for r in RULES if r["is_critical"])
    # priority effects coverage score 0..1
    team_priority = set(team["priority_effects"]) if team else set()
    priority_coverage = (
        len(priority_effects_hit & team_priority) / len(team_priority)
        if team_priority else 0.0
    )

    return {
        "dor_count": len(data["dor"]),
        "dod_count": len(data["dod"]),
        "critical_missing": critical_missing,
        "mismatched": mismatched,
        "mapping_insights": mapping_insights,
        "priority_effects_covered": sorted(priority_effects_hit),
        "antipatterns": antipatterns,
        "score_raw": round(score_raw, 1),
        "score_max": round(score_max, 1),
        "priority_coverage": round(priority_coverage, 2),
    }


# --------------------------- Симуляция последствий ---------------------------


def simulate_outcome(team_key: str, evaluation: Dict) -> Dict:
    """Строит один из 4 исходов жизни команды на основе оценки.

    outcome: "blocked" | "rework_heavy" | "stable" | "predictable"
    """
    ap = set(evaluation.get("antipatterns") or [])
    dor_count = evaluation.get("dor_count", 0)
    dod_count = evaluation.get("dod_count", 0)
    mismatched = len(evaluation.get("mismatched") or [])
    critical_missing = len(evaluation.get("critical_missing") or [])

    if "dor_too_strict" in ap and dod_count >= 2:
        outcome = "blocked"
    elif critical_missing >= 2 or "dod_too_weak" in ap or "dor_too_soft" in ap:
        outcome = "rework_heavy"
    elif mismatched >= 3 or "dor_dod_mixed" in ap:
        outcome = "rework_heavy"
    elif 3 <= dor_count <= 6 and 3 <= dod_count <= 6 and critical_missing == 0:
        outcome = "predictable"
    else:
        outcome = "stable"

    # какие решения к этому привели (ключи причин для локализации на клиенте)
    reasons: List[str] = []
    if "dor_too_strict" in ap:
        reasons.append("reason.dor_too_strict")
    if "dor_too_soft" in ap:
        reasons.append("reason.dor_too_soft")
    if "dod_too_weak" in ap:
        reasons.append("reason.dod_too_weak")
    if "dor_dod_mixed" in ap:
        reasons.append("reason.dor_dod_mixed")
    if "critical_missing" in ap:
        reasons.append("reason.critical_missing")
    if "speed_illusion" in ap:
        reasons.append("reason.speed_illusion")
    if outcome == "predictable":
        reasons.append("reason.balanced")
    if outcome == "stable" and not reasons:
        reasons.append("reason.basic_works")

    return {
        "outcome": outcome,
        "reasons": reasons,
    }


# --------------------------- Сравнение итераций ---------------------------


def improvement_delta(first: Optional[Dict], second: Optional[Dict]) -> Dict:
    """Сравнивает две оценки (первая vs «улучшенная»). Возвращает какие
    антипаттерны ушли, какие новые появились, изменение скора."""
    first = first or {}
    second = second or {}
    a1 = set(first.get("antipatterns") or [])
    a2 = set(second.get("antipatterns") or [])
    s1 = float(first.get("score_raw") or 0)
    s2 = float(second.get("score_raw") or 0)
    return {
        "resolved": sorted(a1 - a2),
        "introduced": sorted(a2 - a1),
        "score_delta": round(s2 - s1, 1),
        "score_before": round(s1, 1),
        "score_after": round(s2, 1),
    }
