"""Backend командного продуктового симулятора для Product Owner'ов.

API под префиксом `/api/agile-training/pm-sim`.

Идея: команды (= группы внутри сессии тренинга) управляют простым мессенджером
20 недель. Каждую неделю — событие, решение и пересчёт метрик; каждые 2 недели
— выбор фичи или стабилизации. Цель — заработать максимум выручки и не потерять
продукт. Win/lose состояния детерминированы правилами; AI используется только
для текстовых пояснений и не меняет числа.

Multiplayer: одна запись `AgileTrainingPmSimState` на группу. Действия любого
участника меняют её через серверные эндпоинты, клиенты опрашивают `/state`.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database import db
from models import (
    AgileTrainingGroup,
    AgileTrainingParticipant,
    AgileTrainingPmSimState,
    AgileTrainingSession,
)


bp_agile_pm_sim = Blueprint(
    "agile_pm_sim", __name__, url_prefix="/api/agile-training/pm-sim"
)


# --------------------------- constants ---------------------------

TOTAL_WEEKS = 20
CYCLE_LEN = 2  # каждые 2 недели — окно выбора фичи
CAPACITY_PER_CYCLE = 100
START_BUDGET = 100_000

# --- delivery risk ---
# Если команда забивает capacity «под завязку», возрастает шанс, что фича
# опоздает на цикл (slip). Это моделирует «overcommit» в продуктовой команде:
# планируем агрессивно — рискуем не доехать к концу 2-х недель.
#
# Формула риска (в процентах, 0..RISK_MAX_PCT):
#   util_pct  = total_committed / CAPACITY_PER_CYCLE * 100   # 0..100
#   base      = max(0, util_pct - RISK_THRESHOLD_PCT) * RISK_SLOPE
#   debt_adj  = max(0, tech_debt - RISK_DEBT_NEUTRAL) * RISK_DEBT_SLOPE
#   stab_adj  = max(0, RISK_STAB_NEUTRAL - stability) * RISK_STAB_SLOPE
#   risk_pct  = clamp(base + debt_adj + stab_adj, 0, RISK_MAX_PCT)
RISK_THRESHOLD_PCT = 60     # ниже 60% утилизации — рисков нет
RISK_SLOPE = 1.5            # +1.5pp к риску за каждый +1pp утилизации сверх порога
RISK_DEBT_NEUTRAL = 40      # нейтральный tech_debt
RISK_DEBT_SLOPE = 0.4       # +0.4pp за каждый пункт долга сверх нейтрала
RISK_STAB_NEUTRAL = 70      # нейтральная stability
RISK_STAB_SLOPE = 0.3       # +0.3pp за каждый пункт стабильности ниже нейтрала
RISK_MAX_PCT = 60           # потолок на риск

PHASE_LOBBY = "lobby"
PHASE_INTRO = "intro"
PHASE_PLAYING = "playing"      # ждём resolve события или выбора фичи
PHASE_FINISHED = "finished"

ALLOWED_PHASES = {PHASE_LOBBY, PHASE_INTRO, PHASE_PLAYING, PHASE_FINISHED}

ROLE_PO = "po"
ROLE_ANALYST = "analyst"
ROLE_TECH = "tech"
ROLE_GROWTH = "growth"
ROLE_ADVOCATE = "advocate"
ALLOWED_ROLES = {ROLE_PO, ROLE_ANALYST, ROLE_TECH, ROLE_GROWTH, ROLE_ADVOCATE}

LEADERBOARD_WEEKS = (5, 10, 15, 20)

AI_CALLS_LIMIT_PER_PARTICIPANT = 12
AI_PROMPT_LIMIT_CHARS = 1600

STATUS_ALIVE = "alive"
STATUS_AT_RISK = "at_risk"
STATUS_DEAD = "dead"

# --- PO action budget ---
# PO тоже ограничен: его «инструменты» (problem-интервью, рефакторинг, ретро,
# архитектурный обзор и т.п.) — это активная работа, и за неделю их не больше
# заданного числа. Так фокус становится осознанным выбором, а не «нажму всё».
PO_ACTIONS_PER_WEEK_LIMIT = 2

# --- Quotas ---
# Эталонный баланс инвестиций PO: 50% бизнес-задачи, 30% тех. долг, 20% архитектура.
# PO может скорректировать квоты под свою стратегию, но крупное отклонение от
# заявленных квот в фактической работе цикла приводит к мягким штрафам.
QUOTA_FOCUSES = ("business", "tech_debt", "architecture")
QUOTA_DEFAULTS = {"business": 50, "tech_debt": 30, "architecture": 20}
QUOTA_DEVIATION_TOLERANCE_PCT = 18  # ±18 п.п. по каждой оси — норма
QUOTA_DEVIATION_PENALTY_HEAVY = 22   # >22 п.п. — серьёзный штраф

# --- Premium subscription pricing ---
# После релиза фичи Premium у PO открывается возможность задать цену.
# Балансировка между «дёшево — много платящих, мало с каждого» и
# «дорого — мало платящих, и платящие быстрее уходят».
PREMIUM_BASE_PRICE = 290              # ₽/мес — базовая «эталонная» цена
PREMIUM_MIN_PRICE = 49
PREMIUM_MAX_PRICE = 1990
PREMIUM_BASE_CONVERSION = 0.012       # 1.2% активных пользователей готовы платить при цене ~рынка
PREMIUM_OVERPRICE_DECAY = 1.4         # за каждое +1× к рынку конверсия падает на 1.4×
PREMIUM_UNDERPRICE_BOOST = 0.35       # за каждое 1×−px/market в плюс к конверсии (в пределах 0..1)
PREMIUM_WEEKS_PER_MONTH = 4.33        # упрощение для перевода monthly→weekly
PREMIUM_PRICE_CHANGE_COOLDOWN = 2     # PO может менять цену не чаще раза в 2 недели
PREMIUM_SUBSCRIBER_INERTIA = 0.3      # доля смещения к target за неделю (медленный отклик базы)

# --- Engineering neglect ---
# Если PO долго игнорирует архитектуру/тех. долг/стабильность, бизнес-метрики
# начинают разрушаться по-настоящему: продукт нестабилен → пользователи уходят,
# падает удовлетворённость и доверие, плюс растёт slip risk на следующий релиз.
ENG_NEGLECT_DEBT_TRIGGER = 62         # tech_debt, при котором начинаются потери
ENG_NEGLECT_DEBT_HARD = 80
ENG_NEGLECT_STAB_TRIGGER = 58         # stability, ниже которой начинаются потери
ENG_NEGLECT_STAB_HARD = 40
ENG_NEGLECT_CHURN_HARD_PCT = 2.8      # %/нед оттока при «жестком» уровне
ENG_NEGLECT_CHURN_SOFT_PCT = 1.2      # %/нед при «мягком» уровне


# --------------------------- catalog: events ---------------------------
#
# Каждое событие — словарь со структурой:
#   id, type, title, description, trigger (callable: data, week -> bool),
#   weight (int, базовая частота), once (bool), affected, options[]:
#     {id, title, description, hint, effects: {metric: delta, ...},
#      requires (optional dict), unlocks (optional str)}
#
# `effects` использует ключи метрик ниже + специальные:
#   capacity_delta, budget_delta, revenue_per_week, ad_strength, monetization_on,
#   tech_debt_delta, churn_bump, growth_bump, investor_pressure_delta.

METRIC_KEYS = (
    "users", "active_users", "satisfaction", "stability", "tech_debt",
    "trust",
)


def _ev(d: Dict[str, Any]) -> Dict[str, Any]:
    return d


# Хэлперы триггеров

def _always(_data, _week):
    return True


def _after(week_min):
    return lambda _d, w: w >= week_min


def _and(*fns):
    return lambda d, w: all(fn(d, w) for fn in fns)


def _low_stability(threshold=60):
    return lambda d, _w: d["metrics"]["stability"] < threshold or d["metrics"]["tech_debt"] > 65


def _low_satisfaction(threshold=55):
    return lambda d, _w: d["metrics"]["satisfaction"] < threshold


def _low_trust(threshold=55):
    return lambda d, _w: d["metrics"]["trust"] < threshold


def _no_revenue_pressure():
    """После 6-й недели, если выручки в неделю всё ещё нет — давление инвестора."""
    return lambda d, w: w >= 6 and not d.get("monetization_on", False)


def _competitor_pressure():
    return lambda d, w: w >= 3 and d["metrics"]["users"] >= 8000


# Каталог. Тексты EN/RU подбираются по локали; для краткости EN-варианты живут в
# параллельной структуре `_EVENTS_EN_OVERRIDES`.

_EVENTS_RU: List[Dict[str, Any]] = [
    _ev({
        "id": "notif_complaints",
        "type": "user",
        "title": "Жалобы на уведомления",
        "description": "Пользователи пропускают важные сообщения и жалуются на «шумные» уведомления.",
        "trigger": _low_satisfaction(70),
        "weight": 8,
        "options": [
            {"id": "improve", "title": "Переделать уведомления",
             "description": "Дольше, но качественно: контекстные настройки.",
             "effects": {"satisfaction": 8, "tech_debt": 5, "capacity_delta": -20}},
            {"id": "delay", "title": "Отложить",
             "description": "Сейчас не приоритет — надеемся, что само рассосётся.",
             "effects": {"satisfaction": -5, "churn_bump": 2}},
            {"id": "quick", "title": "Быстрый фикс",
             "description": "Костыль на пару дней — позже придётся переделать.",
             "effects": {"satisfaction": 3, "stability": -5, "tech_debt": 4, "capacity_delta": -8}},
            {"id": "interview", "title": "Сначала проблемное интервью",
             "description": "Поговорить с 5 пользователями: возможно, проблема не в уведомлениях, а в наполнении.",
             "effects": {"satisfaction": 2, "trust": 2, "tech_debt": -1, "capacity_delta": -8}},
        ],
    }),
    _ev({
        "id": "competitor_channels",
        "type": "competitor",
        "title": "Конкурент запустил каналы",
        "description": "Конкурент выпустил каналы для авторов и сообществ. Часть аудитории обсуждает переход.",
        "trigger": _competitor_pressure(),
        "weight": 6,
        "options": [
            {"id": "rush", "title": "Срочно повторить — выпустить каналы",
             "description": "Большой дельта-рост, но риск стабильности и техдолг.",
             "effects": {"users_pct": 8, "tech_debt": 12, "stability": -8, "capacity_delta": -30}},
            {"id": "research", "title": "Исследовать потребность",
             "description": "Сначала разберёмся — потом построим лучше.",
             "effects": {"capacity_delta": -10, "trust": 2}, "unlocks": "channels_pro"},
            {"id": "focus", "title": "Сфокусироваться на текущей аудитории",
             "description": "Не идти за конкурентом, усилить лояльность.",
             "effects": {"satisfaction": 3, "growth_pct": -3}},
            {"id": "ab_test", "title": "Запустить A/B тест каналов",
             "description": "Выкатить минимальную версию на 10% пользователей — проверим спрос без больших затрат.",
             "effects": {"satisfaction": 2, "trust": 1, "active_users_pct": 2, "tech_debt": 2, "capacity_delta": -10}},
        ],
    }),
    _ev({
        "id": "outage",
        "type": "tech",
        "title": "Падение сервиса",
        "description": "Сервис был недоступен несколько часов в час пик.",
        "trigger": _low_stability(60),
        "weight": 9,
        "options": [
            {"id": "stabilize", "title": "Заморозить фичи и стабилизировать",
             "description": "Команда чинит платформу.",
             "effects": {"stability": 15, "tech_debt": -10, "growth_pct": -3, "capacity_delta": -25}},
            {"id": "compensate", "title": "Извиниться и компенсировать",
             "description": "Премиальный статус, бонусы лояльным.",
             "effects": {"trust": 8, "budget_delta": -10000}},
            {"id": "ignore", "title": "Игнорировать",
             "description": "Сделать вид, что ничего не было.",
             "effects": {"churn_bump": 5, "trust": -10, "satisfaction": -5}},
        ],
        "applied_on_appear": {"stability": -10, "trust": -10, "satisfaction": -8},
    }),
    _ev({
        "id": "investor_money",
        "type": "business",
        "title": "Инвестор требует деньги",
        "description": "Инвестор просит показать выручку в ближайшие недели.",
        "trigger": _no_revenue_pressure(),
        "weight": 10,
        "once": False,
        "options": [
            {"id": "ads", "title": "Запустить рекламу",
             "description": "Быстро деньги, но больно по доверию.",
             "effects": {"satisfaction": -8, "trust": -3, "ad_strength": 2, "monetization_on": True,
                          "revenue_per_week": 3500}},
            {"id": "subscription", "title": "Запустить подписку Premium",
             "description": "Чище для пользователя, но нужна ценность.",
             "effects": {"satisfaction": -3, "monetization_on": True, "revenue_per_week": 2200},
             "requires": {"satisfaction": 55}},
            {"id": "delay", "title": "Отложить монетизацию",
             "description": "Доверие важнее, но инвестор давит.",
             "effects": {"trust": 2, "investor_pressure_delta": 1}},
            {"id": "traffic", "title": "Вложиться в платный трафик",
             "description": "Деньги в маркетинг: быстро прирастём, но без удержания они не задержатся.",
             "effects": {"users_pct": 8, "satisfaction": -3, "trust": -1, "ad_strength": 1, "budget_delta": -15000}},
        ],
    }),
    _ev({
        "id": "privacy_panic",
        "type": "reputation",
        "title": "Паника про приватность",
        "description": "В соцсетях спорят про безопасность мессенджеров. Пользователи спрашивают про защиту.",
        "trigger": _and(_after(3), _low_trust(75)),
        "weight": 6,
        "options": [
            {"id": "e2ee", "title": "Сделать сквозное шифрование",
             "description": "Дорого, но это сильная позиция.",
             "effects": {"trust": 15, "tech_debt": 8, "capacity_delta": -35}},
            {"id": "policy", "title": "Опубликовать политику безопасности",
             "description": "PR-ход, бюджет на коммуникации.",
             "effects": {"trust": 6, "budget_delta": -5000}},
            {"id": "ignore", "title": "Ничего не делать",
             "description": "Подождать, пока тема забудется.",
             "effects": {"trust": -10, "churn_bump": 3}},
        ],
    }),
    _ev({
        "id": "regulator",
        "type": "regulatory",
        "title": "Регулятор просит локализовать данные",
        "description": "Локальный регулятор требует хранить данные пользователей внутри страны.",
        "trigger": _after(7),
        "weight": 4,
        "options": [
            {"id": "comply", "title": "Соответствовать требованиям",
             "description": "Технически тяжёлая миграция инфраструктуры.",
             "effects": {"trust": 6, "stability": -4, "capacity_delta": -25, "budget_delta": -8000}},
            {"id": "partial", "title": "Частичное соответствие",
             "description": "Закрыть только критичные сценарии.",
             "effects": {"capacity_delta": -10, "trust": 2}},
            {"id": "lobby", "title": "Юристы пытаются договориться",
             "description": "Купить время, надеясь что норма смягчится.",
             "effects": {"budget_delta": -3000, "trust": -3}},
        ],
    }),
    _ev({
        "id": "viral_growth",
        "type": "user",
        "title": "Вирусный момент",
        "description": "Известный блогер позвал подписчиков в ваш мессенджер. Толпа новых пользователей пришла одновременно.",
        "trigger": _and(_after(4), lambda d, _w: d["metrics"]["satisfaction"] >= 60),
        "weight": 5,
        "options": [
            {"id": "scale", "title": "Срочно масштабировать",
             "description": "Поднять кластер, докупить мощности.",
             "effects": {"users_pct": 12, "stability": -3, "budget_delta": -12000, "tech_debt": 5}},
            {"id": "ride", "title": "Идти как есть",
             "description": "Принимаем нагрузку, надеемся что выдержим.",
             "effects": {"users_pct": 8, "stability": -10, "satisfaction": -3}},
            {"id": "queue", "title": "Очередь регистрации",
             "description": "Гасим хайп, бережём систему.",
             "effects": {"users_pct": 4, "trust": -2, "satisfaction": -2}},
            {"id": "solution_iv", "title": "Solution-интервью с горячими пользователями",
             "description": "Выяснить, что именно зацепило: целить в ядро ценности, а не в трафик.",
             "effects": {"satisfaction": 4, "trust": 3, "users_pct": 3, "capacity_delta": -8}},
        ],
    }),
    _ev({
        "id": "team_burnout",
        "type": "team",
        "title": "Усталость команды",
        "description": "Команда жалуется: четыре недели подряд жили в овертаймах.",
        "trigger": _and(_after(6),
                         lambda d, _w: d.get("recent_feature_count", 0) >= 3
                         and d["metrics"]["tech_debt"] > 50),
        "weight": 5,
        "options": [
            {"id": "rest", "title": "Сделать паузу — без новых фич",
             "description": "Команда отдыхает, чинит мелкое, перезаряжается.",
             "effects": {"capacity_delta": -10, "tech_debt": -8, "stability": 5, "satisfaction": 2}},
            {"id": "hire", "title": "Срочно нанять",
             "description": "Дорого и адаптация займёт время.",
             "effects": {"budget_delta": -15000, "capacity_delta": -10}, "unlocks": "capacity_boost"},
            {"id": "push", "title": "Дожать — потом отдохнём",
             "description": "Ещё один спринт ускорения, цена будет позже.",
             "effects": {"tech_debt": 8, "stability": -5, "growth_pct": 2}},
        ],
    }),
    _ev({
        "id": "data_leak",
        "type": "reputation",
        "title": "Утечка персональных данных",
        "description": "Журналисты пишут об уязвимости — куда смотреть, что чинить, как разговаривать с прессой.",
        "trigger": _and(_after(8), lambda d, _w: d["metrics"]["tech_debt"] > 60 or d["metrics"]["stability"] < 55),
        "weight": 4,
        "applied_on_appear": {"trust": -12, "satisfaction": -6},
        "options": [
            {"id": "transparent", "title": "Прозрачный пост-мортем",
             "description": "Признать проблему, показать, что чините.",
             "effects": {"trust": 8, "capacity_delta": -15, "tech_debt": -5}},
            {"id": "lawyers", "title": "Юристы и тишина",
             "description": "Минимум комментариев, максимум NDA.",
             "effects": {"trust": -8, "budget_delta": -7000}},
            {"id": "fix_only", "title": "Молча всё починить",
             "description": "Главное — устранить, остальное переживём.",
             "effects": {"stability": 5, "tech_debt": -8, "trust": -3, "capacity_delta": -20}},
        ],
    }),
    _ev({
        "id": "growth_dip",
        "type": "user",
        "title": "Рост остановился",
        "description": "Подключения новых пользователей упали — нужна новая идея удержания или активации.",
        "trigger": _and(_after(6), lambda d, _w: d["metrics"]["satisfaction"] < 65),
        "weight": 5,
        "options": [
            {"id": "onboarding", "title": "Переделать онбординг",
             "description": "Внимательнее провести нового пользователя.",
             "effects": {"satisfaction": 4, "growth_pct": 3, "capacity_delta": -15}},
            {"id": "referral", "title": "Реферальная программа",
             "description": "Платить пользователям за приглашения.",
             "effects": {"users_pct": 5, "budget_delta": -6000, "trust": 1}},
            {"id": "wait", "title": "Ничего не делать",
             "description": "Сосредоточиться на других задачах.",
             "effects": {"growth_pct": -2}},
        ],
    }),
    _ev({
        "id": "ads_backlash",
        "type": "user",
        "title": "Реакция на рекламу",
        "description": "Пользователи открыто пишут, что реклама в мессенджере — это слишком.",
        "trigger": lambda d, _w: d.get("ad_strength", 0) >= 1 and d["metrics"]["satisfaction"] < 65,
        "weight": 6,
        "options": [
            {"id": "soften", "title": "Снизить агрессивность рекламы",
             "description": "Меньше денег, больше доверия.",
             "effects": {"ad_strength": -1, "satisfaction": 5, "trust": 4, "revenue_per_week": -1500}},
            {"id": "double", "title": "Усилить таргетинг",
             "description": "Больше денег сейчас — больше боли потом.",
             "effects": {"ad_strength": 1, "revenue_per_week": 2000, "satisfaction": -7, "trust": -3}},
            {"id": "explain", "title": "Объяснить, зачем реклама",
             "description": "Открытая позиция: «без неё не выжить».",
             "effects": {"trust": 2, "satisfaction": 1}},
        ],
    }),
    _ev({
        "id": "support_overload",
        "type": "user",
        "title": "Поддержка не справляется",
        "description": "Очередь обращений выросла, ответы стали медленнее, пользователи злятся.",
        "trigger": _and(_after(5), lambda d, _w: d["metrics"]["users"] >= 12000),
        "weight": 4,
        "options": [
            {"id": "scale_support", "title": "Расширить поддержку",
             "description": "Нанять, обучить, поставить SLA.",
             "effects": {"satisfaction": 5, "trust": 3, "budget_delta": -8000}},
            {"id": "ai_bot", "title": "Запустить AI-бота",
             "description": "Снять рутину, рискнуть на сложных кейсах.",
             "effects": {"satisfaction": 1, "capacity_delta": -10, "budget_delta": -3000}},
            {"id": "fyi", "title": "Поставить FAQ и забыть",
             "description": "Самая дешёвая опция.",
             "effects": {"satisfaction": -4, "trust": -3}},
        ],
    }),
    _ev({
        "id": "flaky_login",
        "type": "tech",
        "title": "Флаки на логине",
        "description": "Часть пользователей не может зайти после обновления — отчёты по разным платформам.",
        "trigger": _after(2),
        "weight": 5,
        "applied_on_appear": {"trust": -4, "satisfaction": -3},
        "options": [
            {"id": "hotfix", "title": "Срочный хотфикс",
             "description": "Откат + патч за 1 день. Команда отвлечётся от спринта.",
             "effects": {"stability": 6, "trust": 4, "capacity_delta": -10}},
            {"id": "investigate", "title": "Полноценное расследование",
             "description": "Берём 3 дня, чиним корневую причину, добавляем алёрт.",
             "effects": {"stability": 10, "tech_debt": -4, "capacity_delta": -18}},
            {"id": "communicate_only", "title": "Сообщить, не чинить",
             "description": "Извиниться, попросить переустановить — само рассосётся.",
             "effects": {"trust": -4, "satisfaction": -3}},
        ],
    }),
    _ev({
        "id": "key_dev_offer",
        "type": "team",
        "title": "Ключевому инженеру делают оффер",
        "description": "Один из ведущих инженеров получил оффер. От него зависят 2 крупных компонента.",
        "trigger": _after(6),
        "weight": 4,
        "options": [
            {"id": "counter_offer", "title": "Контр-оффер и план роста",
             "description": "Удерживаем человека: премия, рост, понятные следующие 6 месяцев.",
             "effects": {"trust": 3, "satisfaction": 3, "budget_delta": -12000}},
            {"id": "share_knowledge", "title": "Запустить knowledge sharing",
             "description": "Не удерживаем любой ценой — разносим экспертизу по команде.",
             "effects": {"tech_debt": -4, "stability": 3, "capacity_delta": -10}},
            {"id": "let_go", "title": "Отпустить",
             "description": "Решаем, что справимся. Риск сильно подскочит.",
             "effects": {"stability": -8, "tech_debt": 8, "satisfaction": -2}},
        ],
    }),
    _ev({
        "id": "pricing_pressure",
        "type": "business",
        "title": "Конкуренты снизили цены",
        "description": "Главный конкурент сделал тариф на 30% дешевле. Часть платящих пользователей задаёт вопросы.",
        "trigger": _and(_after(8), lambda d, _w: d.get("monetization_on")),
        "weight": 5,
        "options": [
            {"id": "match_price", "title": "Снизить цену",
             "description": "Догнать рынок: меньше выручки, но не теряем платящих.",
             "effects": {"revenue_per_week": -1500, "satisfaction": 3, "trust": 2}},
            {"id": "value_pack", "title": "Добавить ценность в тариф",
             "description": "Не трогаем цену, докладываем фичи в платный пакет.",
             "effects": {"satisfaction": 4, "tech_debt": 4, "capacity_delta": -10}},
            {"id": "ignore_market", "title": "Не реагировать",
             "description": "Цена и так оправдана — пусть рынок решит.",
             "effects": {"churn_bump": 2, "trust": -2}},
        ],
    }),
    _ev({
        "id": "partner_integration",
        "type": "business",
        "title": "Крупный партнёр предлагает интеграцию",
        "description": "Известный сервис хочет встроить ваш мессенджер у себя — это тысячи новых пользователей, но ресурс на интеграцию.",
        "trigger": _and(_after(7), lambda d, _w: d["metrics"]["users"] >= 10000),
        "weight": 4,
        "options": [
            {"id": "build_integration", "title": "Сделать интеграцию",
             "description": "2 недели команды на API, документацию и SLA.",
             "effects": {"users_pct": 10, "trust": 3, "capacity_delta": -22, "tech_debt": 4}},
            {"id": "minimal_api", "title": "Минимальный публичный API",
             "description": "Открываем endpoints как есть — пусть партнёр сам встраивает.",
             "effects": {"users_pct": 4, "tech_debt": 6, "capacity_delta": -8}},
            {"id": "decline", "title": "Отказаться",
             "description": "Сейчас не наш приоритет — сосредоточимся на ядре продукта.",
             "effects": {"trust": -1}},
        ],
    }),
    _ev({
        "id": "analytics_blind",
        "type": "user",
        "title": "Слепые зоны в аналитике",
        "description": "Команда понимает: непонятно, какие фичи реально используются. Решения принимаются «на ощущениях».",
        "trigger": _and(_after(4), lambda d, _w: d.get("recent_feature_count", 0) >= 2),
        "weight": 4,
        "options": [
            {"id": "instrument", "title": "Внедрить продуктовую аналитику",
             "description": "События, воронки, дашборды — теперь видим, как реально пользуются.",
             "effects": {"tech_debt": 2, "capacity_delta": -12, "trust": 1, "satisfaction": 1}},
            {"id": "user_panel", "title": "Собрать панель пользователей",
             "description": "Регулярные интервью с фиксированной группой — поймём поведение качественно.",
             "effects": {"trust": 3, "satisfaction": 2, "budget_delta": -3000}},
            {"id": "trust_gut", "title": "Полагаться на интуицию",
             "description": "Решаем, что хватит и так — двигаемся по ощущениям команды.",
             "effects": {"tech_debt": 2, "trust": -2}},
        ],
    }),
    _ev({
        "id": "accessibility_complaint",
        "type": "reputation",
        "title": "Жалоба по доступности",
        "description": "Пользователь с особыми потребностями написал публичный пост: «вашим продуктом невозможно пользоваться».",
        "trigger": _after(5),
        "weight": 3,
        "applied_on_appear": {"trust": -3},
        "options": [
            {"id": "fix_a11y", "title": "Исправить ключевые проблемы",
             "description": "Контраст, размер кнопок, screen-reader на главных экранах.",
             "effects": {"trust": 6, "satisfaction": 3, "capacity_delta": -12}},
            {"id": "audit_only", "title": "Заказать аудит",
             "description": "Команда продолжает работу, аудит покажет масштаб проблемы.",
             "effects": {"trust": 2, "budget_delta": -3500}},
            {"id": "deflect", "title": "Ответить шаблоном",
             "description": "PR-отписка: «спасибо за обратную связь, мы работаем над этим».",
             "effects": {"trust": -5, "satisfaction": -2}},
        ],
    }),
    _ev({
        "id": "appstore_review",
        "type": "regulatory",
        "title": "AppStore просит изменить продукт",
        "description": "Магазин требует убрать одну из фич или переработать политику данных, иначе релиз не пропустят.",
        "trigger": _after(9),
        "weight": 3,
        "options": [
            {"id": "comply_quick", "title": "Согласиться и доработать",
             "description": "Команда быстро адаптирует продукт под требования.",
             "effects": {"capacity_delta": -15, "trust": 2, "stability": 2}},
            {"id": "negotiate", "title": "Юристы пытаются переубедить",
             "description": "Тратим время и деньги на переговоры — релиз задержится.",
             "effects": {"budget_delta": -6000, "trust": -2}},
            {"id": "remove_feature", "title": "Убрать фичу из стора",
             "description": "Самый быстрый путь — потеря части пользователей.",
             "effects": {"users_pct": -3, "satisfaction": -2}},
        ],
    }),
    _ev({
        "id": "infra_cost_spike",
        "type": "business",
        "title": "Скачок инфраструктурных затрат",
        "description": "Облачный счёт на этот месяц вырос в 1.7 раза — рост трафика и неудачные конфиги.",
        "trigger": _and(_after(7), lambda d, _w: d["metrics"]["users"] >= 8000),
        "weight": 4,
        "options": [
            {"id": "optimize", "title": "Оптимизировать инфраструктуру",
             "description": "Команда садится за конфиги, кэши, размер инстансов.",
             "effects": {"capacity_delta": -12, "tech_debt": -4, "stability": 3}},
            {"id": "reserve", "title": "Купить резервы",
             "description": "Контракт со скидкой за объём — экономим на проде.",
             "effects": {"budget_delta": -10000, "stability": 2}},
            {"id": "absorb", "title": "Просто платить больше",
             "description": "Не отвлекаем команду — но дыра в бюджете растёт.",
             "effects": {"budget_delta": -8000, "investor_pressure_delta": 1}},
        ],
    }),
    _ev({
        "id": "payment_outage_crisis",
        "type": "crisis",
        "title": "Кризис: платежи нестабильны",
        "description": "После релиза монетизации часть списаний проходит дважды, часть не проходит вовсе. Поддержка и соцсети кипят.",
        "trigger": _and(
            _after(6),
            lambda d, _w: d.get("monetization_on")
            and (d["metrics"]["stability"] < 78 or d["metrics"]["tech_debt"] > 35),
        ),
        "weight": 5,
        "applied_on_appear": {"trust": -6, "satisfaction": -4, "budget_delta": -4000},
        "options": [
            {"id": "war_room", "title": "Собрать crisis war-room",
             "description": "Заморозить часть roadmap и чинить инцидент вместе с саппортом и финком.",
             "effects": {"stability": 8, "trust": 4, "capacity_delta": -22, "budget_delta": -7000, "tech_debt": -3}},
            {"id": "rollback_payments", "title": "Откатить платёжный релиз",
             "description": "Временно выключить проблемный поток, потерять деньги, но вернуть контроль.",
             "effects": {"revenue_per_week": -2200, "satisfaction": 3, "trust": 4, "tech_debt": -2}},
            {"id": "deny_issue", "title": "Списать на «единичные кейсы»",
             "description": "Публично минимизировать масштаб и не останавливать продажи.",
             "effects": {"trust": -12, "satisfaction": -7, "churn_bump": 5}},
        ],
    }),
    _ev({
        "id": "security_zero_day_crisis",
        "type": "crisis",
        "title": "Кризис: zero-day в проде",
        "description": "Обнаружена критичная уязвимость: потенциально можно читать часть личных данных через цепочку старых сервисов.",
        "trigger": _and(
            _after(9),
            lambda d, _w: d["metrics"]["tech_debt"] > 45 or d["metrics"]["stability"] < 65,
        ),
        "weight": 4,
        "applied_on_appear": {"trust": -10, "satisfaction": -5},
        "options": [
            {"id": "containment", "title": "Изоляция и аварийный патч",
             "description": "Срочно отрезать рискованные контуры, выпустить патч и жить с ограничениями.",
             "effects": {"stability": 6, "trust": 3, "users_pct": -3, "capacity_delta": -18, "tech_debt": -4}},
            {"id": "full_audit", "title": "Полный security-аудит + bug bounty",
             "description": "Дорого и долго, но радикально снижает повторяемость подобных инцидентов.",
             "effects": {"trust": 8, "stability": 3, "tech_debt": -10, "capacity_delta": -25, "budget_delta": -12000}},
            {"id": "quiet_fix", "title": "Тихо починить без публичного признания",
             "description": "Экономим лицо сейчас, рискуем репутацией, если всплывёт позже.",
             "effects": {"trust": -14, "satisfaction": -6, "churn_bump": 6}},
        ],
    }),
    _ev({
        "id": "funding_crunch_crisis",
        "type": "crisis",
        "title": "Кризис: кассовый разрыв",
        "description": "Денежный буфер тает быстрее плана: инвестор требует жёсткий план экономии и доказательства дисциплины.",
        "trigger": _and(
            _after(10),
            lambda d, _w: d.get("budget", 0) < 75_000 or d.get("investor_pressure", 0) >= 2,
        ),
        "weight": 4,
        "applied_on_appear": {"trust": -4, "satisfaction": -2},
        "options": [
            {"id": "cost_freeze", "title": "Режим жёсткой экономии",
             "description": "Сократить активности, сфокусироваться на выживаемости unit-экономики.",
             "effects": {"budget_delta": 12000, "capacity_delta": -12, "satisfaction": -3, "trust": -2}},
            {"id": "bridge_round", "title": "Поднять bridge-раунд",
             "description": "Купить время за счёт новой договорённости с инвестором и более жёстких KPI.",
             "effects": {"budget_delta": 25000, "trust": -3, "investor_pressure_delta": 1}},
            {"id": "cut_people", "title": "Сократить команду",
             "description": "Быстрый финансовый эффект ценой морального и технического удара.",
             "effects": {"budget_delta": 18000, "stability": -10, "trust": -8, "satisfaction": -6}},
        ],
    }),
]


# --------------------------- catalog: features ---------------------------

_FEATURES_RU: List[Dict[str, Any]] = [
    {"key": "reactions", "title": "Реакции на сообщения",
     "description": "Простой способ ответить эмоцией без сообщения.",
     "capacity": 20, "budget": 0, "focus": "business",
     "effects": {"users_pct": 3, "satisfaction": 5, "tech_debt": 3}},
    {"key": "voice", "title": "Голосовые сообщения",
     "description": "Самая ожидаемая просьба пользователей.",
     "capacity": 35, "budget": 0, "focus": "business",
     "effects": {"active_users_pct": 6, "satisfaction": 4, "stability": -3, "tech_debt": 5}},
    {"key": "channels", "title": "Каналы для сообществ",
     "description": "Большая фича — авторы получают подписчиков.",
     "capacity": 50, "budget": 0, "focus": "business",
     "effects": {"users_pct": 12, "tech_debt": 10, "stability": -5, "revenue_potential": 8000}},
    {"key": "premium", "title": "Подписка Premium",
     "description": "Платный пакет: облачное хранение, темы, эмодзи.",
     "capacity": 40, "budget": 0, "focus": "business",
     "effects": {"satisfaction": -2, "monetization_on": True, "revenue_per_week": 4000},
     "requires": {"week_min": 3, "satisfaction": 52}},
    {"key": "ads", "title": "Реклама в каналах",
     "description": "Быстрый источник денег.",
     "capacity": 20, "budget": 0, "focus": "business",
     "effects": {"satisfaction": -10, "trust": -5, "monetization_on": True,
                  "revenue_per_week": 5000, "ad_strength": 1}},
    {"key": "e2ee", "title": "Сквозное шифрование",
     "description": "Доверие вырастет, но фича дорогая.",
     "capacity": 45, "budget": 0, "focus": "architecture",
     "effects": {"trust": 18, "satisfaction": 4, "tech_debt": 8}},
    {"key": "stabilize", "title": "Стабилизация платформы",
     "description": "Не фича, а вложение в качество.",
     "capacity": 35, "budget": 0, "focus": "tech_debt",
     "effects": {"stability": 15, "tech_debt": -10}},
    {"key": "redesign", "title": "Редизайн интерфейса",
     "description": "Свежий вид и переосмысление навигации.",
     "capacity": 30, "budget": 0, "focus": "business",
     "effects": {"satisfaction": 8, "active_users_pct": 3, "first_week_satisfaction_dip": 3}},
    {"key": "stickers", "title": "Маркетплейс стикеров",
     "description": "Контент-фича + чуть денег от продаж.",
     "capacity": 25, "budget": 0, "focus": "business",
     "effects": {"satisfaction": 4, "users_pct": 2, "revenue_per_week": 1200, "monetization_on": True}},
    {"key": "analytics", "title": "Аналитика для авторов",
     "description": "Поддерживает каналы — авторы остаются дольше.",
     "capacity": 30, "budget": 0, "focus": "business",
     "effects": {"satisfaction": 2, "active_users_pct": 4, "tech_debt": 4},
     "requires": {"feature": "channels"}},
    # --- Engineering / architecture фичи: усиливают платформу.
    {"key": "observability", "title": "Метрики и observability",
     "description": "Сбор телеметрии и алёрты: видим продакшн, ловим инциденты до пользователей.",
     "capacity": 25, "budget": 0, "focus": "architecture",
     "effects": {"stability": 7, "tech_debt": -3, "trust": 2}},
    {"key": "platform_split", "title": "Разделить монолит",
     "description": "Большая инвестиция в архитектуру: сервис на сервисы. Снимает долг и рост стабильности, но дорогая.",
     "capacity": 50, "budget": 0, "focus": "architecture",
     "effects": {"stability": 10, "tech_debt": -15, "capacity_delta": -5},
     "requires": {"satisfaction": 55}},
    {"key": "ci_cd", "title": "CI/CD и автотесты",
     "description": "Автоматический пайплайн поставки. Команда быстрее доезжает до релиза, меньше регрессий.",
     "capacity": 30, "budget": 0, "focus": "tech_debt",
     "effects": {"stability": 5, "tech_debt": -7, "capacity_delta": 0}},
    # --- Дополнительный пул фич: подмешиваются, если PO провёл product
    # discovery (problem_interview / solution_interview) и расширил пул.
    {"key": "onboarding", "title": "Онбординг для новичков",
     "description": "Шаги первого знакомства: подсказки, чек-лист, первый «aha»-момент за 90 секунд.",
     "capacity": 25, "budget": 0, "focus": "business",
     "effects": {"satisfaction": 6, "active_users_pct": 5, "trust": 2}},
    {"key": "search", "title": "Умный поиск по сообщениям",
     "description": "Быстрый, контекстный поиск — пользователи реже теряют ценные диалоги.",
     "capacity": 30, "budget": 0, "focus": "business",
     "effects": {"satisfaction": 7, "active_users_pct": 4, "tech_debt": 3}},
    {"key": "moderation", "title": "Инструменты модерации",
     "description": "Жалобы, отчёты, авто-фильтр спама. Снижает риск массовых проблем в каналах.",
     "capacity": 35, "budget": 0, "focus": "tech_debt",
     "effects": {"trust": 9, "satisfaction": 3, "stability": 3, "tech_debt": -2},
     "requires": {"feature": "channels"}},
    {"key": "referral", "title": "Реферальная программа",
     "description": "Пользователи приводят друзей за бонус. Дешевле платного трафика, если есть удержание.",
     "capacity": 25, "budget": 0, "focus": "business",
     "effects": {"users_pct": 7, "active_users_pct": 3, "satisfaction": 1},
     "requires": {"satisfaction": 55}},
    {"key": "data_export", "title": "Экспорт данных пользователя",
     "description": "Скачать переписку и медиа одним архивом. Бьёт прямо в страх «застрять» в продукте — доверие растёт.",
     "capacity": 20, "budget": 0, "focus": "architecture",
     "effects": {"trust": 12, "satisfaction": 3}},
    {"key": "translate", "title": "Перевод сообщений",
     "description": "Автоперевод подписей и сообщений: открывает международную аудиторию.",
     "capacity": 30, "budget": 0, "focus": "business",
     "effects": {"users_pct": 6, "satisfaction": 4, "tech_debt": 4},
     "requires": {"satisfaction": 50}},
    {"key": "mobile_perf", "title": "Оптимизация мобильного клиента",
     "description": "Быстрее открытие чатов, меньше батареи, плавнее скролл. Незаметно — и поэтому ценно.",
     "capacity": 25, "budget": 0, "focus": "tech_debt",
     "effects": {"stability": 6, "satisfaction": 5, "tech_debt": -4}},
    {"key": "private_groups", "title": "Приватные группы по приглашению",
     "description": "Закрытые сообщества с инвайтами и модерацией — премиальный сегмент.",
     "capacity": 30, "budget": 0, "focus": "business",
     "effects": {"trust": 6, "satisfaction": 4, "active_users_pct": 4},
     "requires": {"feature": "channels"}},
    {"key": "user_testing", "title": "Юзабилити-тесты ключевых сценариев",
     "description": "Прогон 5 пользователей через 3 сценария — находим узкие места до релиза.",
     "capacity": 15, "budget": 0, "focus": "business",
     "effects": {"satisfaction": 4, "trust": 2, "tech_debt": -1}},
    {"key": "mini_app_sdk", "title": "SDK для мини-приложений",
     "description": "Открываем платформу для сторонних разработчиков. Большая инвестиция в экосистему.",
     "capacity": 50, "budget": 0, "focus": "architecture",
     "effects": {"users_pct": 10, "satisfaction": 3, "tech_debt": 6, "stability": -2},
     "requires": {"satisfaction": 60}},
    {"key": "smart_notifications", "title": "Умные уведомления",
     "description": "Приоритетные пуши и тихие часы: меньше шума, больше пользы.",
     "capacity": 25, "budget": 0, "focus": "business",
     "effects": {"satisfaction": 5, "active_users_pct": 3, "tech_debt": 2}},
    {"key": "threaded_replies", "title": "Треды в чатах",
     "description": "Ответы по веткам помогают держать длинные обсуждения в порядке.",
     "capacity": 30, "budget": 0, "focus": "business",
     "effects": {"satisfaction": 4, "active_users_pct": 3, "tech_debt": 3}},
    {"key": "anti_spam_ml", "title": "ML-антиспам",
     "description": "Машинное обучение для фильтрации спама и подозрительных аккаунтов.",
     "capacity": 35, "budget": 0, "focus": "tech_debt",
     "effects": {"trust": 7, "stability": 3, "tech_debt": -2}},
    {"key": "backup_restore", "title": "Резервные копии и восстановление",
     "description": "Автобэкапы пользовательских данных и безопасное восстановление.",
     "capacity": 30, "budget": 0, "focus": "architecture",
     "effects": {"trust": 8, "satisfaction": 2, "stability": 3}},
    {"key": "team_admin_panel", "title": "Панель администрирования команд",
     "description": "Роли, права и аудит действий администраторов для B2B-клиентов.",
     "capacity": 25, "budget": 0, "focus": "business",
     "effects": {"users_pct": 4, "trust": 3, "tech_debt": 2}},
    {"key": "sla_monitoring", "title": "SLA-мониторинг",
     "description": "Публичные SLA-метрики и внутренние алерты по деградациям.",
     "capacity": 20, "budget": 0, "focus": "architecture",
     "effects": {"stability": 5, "trust": 3, "tech_debt": -2}},
    {"key": "message_scheduling", "title": "Отложенные сообщения",
     "description": "Планирование отправки сообщений на нужное время.",
     "capacity": 20, "budget": 0, "focus": "business",
     "effects": {"satisfaction": 4, "active_users_pct": 2}},
    {"key": "offline_mode", "title": "Офлайн-режим",
     "description": "Черновики и кэш переписки без сети с автосинхронизацией.",
     "capacity": 35, "budget": 0, "focus": "tech_debt",
     "effects": {"satisfaction": 5, "stability": 4, "tech_debt": -3}},
    {"key": "crm_integration", "title": "Интеграция с CRM",
     "description": "Связка с CRM и автоматические карточки клиентов в диалоге.",
     "capacity": 30, "budget": 0, "focus": "business",
     "effects": {"users_pct": 5, "revenue_per_week": 1400, "trust": 2}},
    {"key": "api_rate_limits", "title": "Rate limits и API-ключи",
     "description": "Ограничение API по ключам и защита от злоупотреблений.",
     "capacity": 20, "budget": 0, "focus": "architecture",
     "effects": {"stability": 4, "trust": 2, "tech_debt": -1}},
    {"key": "dark_mode_plus", "title": "Продвинутый тёмный режим",
     "description": "Тонкие настройки темы, шрифтов и контраста для долгой работы.",
     "capacity": 15, "budget": 0, "focus": "business",
     "effects": {"satisfaction": 3, "active_users_pct": 2}},
    {"key": "voice_transcription", "title": "Расшифровка голосовых",
     "description": "Автоматическая транскрибация голосовых сообщений в текст.",
     "capacity": 30, "budget": 0, "focus": "business",
     "effects": {"satisfaction": 4, "active_users_pct": 3, "tech_debt": 2}},
    {"key": "incident_playbooks", "title": "Плейбуки инцидентов",
     "description": "Стандартизированные сценарии реагирования на прод-инциденты.",
     "capacity": 25, "budget": 0, "focus": "tech_debt",
     "effects": {"stability": 6, "tech_debt": -4, "trust": 1}},
    {"key": "tenant_isolation", "title": "Изоляция tenant-ов",
     "description": "Более строгая изоляция данных клиентов в мультиарендной схеме.",
     "capacity": 40, "budget": 0, "focus": "architecture",
     "effects": {"trust": 9, "stability": 3, "tech_debt": 2}},
    {"key": "cost_optimizer", "title": "Оптимизация инфраструктурных затрат",
     "description": "Авто-подбор инстансов, кэши и более дешёвые профили нагрузки.",
     "capacity": 25, "budget": 0, "focus": "tech_debt",
     "effects": {"budget_delta": 12000, "stability": 2, "tech_debt": -3}},
    {"key": "knowledge_base", "title": "База знаний в продукте",
     "description": "Встроенная self-service база знаний для быстрого самообслуживания.",
     "capacity": 20, "budget": 0, "focus": "business",
     "effects": {"satisfaction": 3, "trust": 2, "capacity_delta": 3}},
    {"key": "compliance_audit", "title": "Аудит соответствия и комплаенс",
     "description": "Проверка политики хранения данных, доступов и юридических требований.",
     "capacity": 30, "budget": 0, "focus": "architecture",
     "effects": {"trust": 7, "stability": 2, "budget_delta": -4000}},
]


# --------------------------- catalog: PO toolkit actions ---------------------------
#
# Это «продуктовые ходы» (discovery / growth / pivot) и Scrum-события
# (Daily / Refinement / Review / Retro). Их PO применяет ПАРАЛЛЕЛЬНО с
# решением события — один клик, мгновенный эффект, кулдаун. Идея: тренируем
# мышление PO о ритуалах Scrum и об инвестициях в product discovery.
#
# Каждое действие:
#   - title / description (RU/EN)
#   - category: discovery | growth | pivot | scrum
#   - cap_cost / budget_cost
#   - cooldown_weeks (через сколько можно повторить)
#   - max_per_game (None = без лимита)
#   - effects: применяются через _apply_metric_delta (тот же словарь, что у фич)
#   - requires: { week_min, satisfaction, ... } — мягкие ограничения

PO_ACTIONS: Dict[str, Dict[str, Any]] = {
    # --- Discovery (focus = business: разбираемся в ценности продукта) ---
    "problem_interview": {
        "title_ru": "Провести проблемное интервью",
        "title_en": "Run problem interviews",
        "description_ru": "Поговорить с 5 пользователями о их реальной боли. Это не тренинг, а исследование: после интервью лучше понимаешь, какую проблему стоит решать. Следующая фича попадёт точнее.",
        "description_en": "Talk to 5 users about their real pain. It's research, not coaching: after interviews you'll know which problem is worth solving. The next feature lands closer to value.",
        "category": "discovery",
        "focus": "business",
        "icon": "🎤",
        "cap_cost": 0,
        "budget_cost": 0,
        "cooldown_weeks": 2,
        "po_action_cost": 1,
        "max_per_game": None,
        "effects": {"satisfaction": 2, "trust": 2, "tech_debt": -1},
    },
    "solution_interview": {
        "title_ru": "Провести solution-интервью",
        "title_en": "Run solution interviews",
        "description_ru": "Показать прототип — проверить, решит ли он проблему. Снижает риск опоздать со следующим релизом. Сначала нужны проблемные интервью.",
        "description_en": "Show a prototype — after problem interviews, check that it solves the need. Lowers slip risk on the next release.",
        "category": "discovery",
        "focus": "business",
        "icon": "🧪",
        "cap_cost": 0,
        "budget_cost": 0,
        "cooldown_weeks": 2,
        "po_action_cost": 1,
        "requires": {"after_action": "problem_interview"},
        "effects": {"satisfaction": 1, "stability": 2, "tech_debt": -1},
        "side_effects": {"next_release_risk_buff": 12},
    },
    "ab_test": {
        "title_ru": "Запустить A/B тест",
        "title_en": "Run an A/B test",
        "description_ru": "Маленький эксперимент вместо большой ставки. Низкий риск, но и эффект скромнее.",
        "description_en": "A small experiment instead of a big bet. Low risk, modest reward.",
        "category": "discovery",
        "focus": "business",
        "icon": "🆎",
        "cap_cost": 0,
        "budget_cost": 0,
        "cooldown_weeks": 2,
        "po_action_cost": 1,
        "effects": {"satisfaction": 2, "trust": 1, "active_users_pct": 2, "tech_debt": 2},
    },
    # --- Growth (focus = business) ---
    "traffic_invest": {
        "title_ru": "Вложиться в платный трафик",
        "title_en": "Invest in paid traffic",
        "description_ru": "Платный трафик: пользователей быстро прибавится, но без удержания они уйдут с разочарованием.",
        "description_en": "Paid traffic: quick user spike. Without retention they churn back disappointed.",
        "category": "growth",
        "focus": "business",
        "icon": "💸",
        "cap_cost": 0,
        "budget_cost": 15000,
        "cooldown_weeks": 3,
        "po_action_cost": 1,
        "effects": {"users_pct": 8, "satisfaction": -3, "trust": -1, "ad_strength": 1},
        "requires": {"satisfaction": 50},
    },
    "pivot": {
        "title_ru": "Сделать пивот",
        "title_en": "Pivot",
        "description_ru": "Большая ставка на переосмысление продукта. Дорого, требует фокуса, но восстанавливает доверие и снимает долг.",
        "description_en": "A big bet on rethinking the product. Costly and disruptive, but restores trust and pays off debt.",
        "category": "pivot",
        "focus": "business",
        "icon": "🔄",
        "cap_cost": 40,
        "budget_cost": 10000,
        "cooldown_weeks": 0,
        "po_action_cost": 2,
        "max_per_game": 1,
        "requires": {"week_min": 5},
        "effects": {"satisfaction": 6, "trust": 8, "tech_debt": -12, "stability": 4, "users_pct": -5},
    },
    # --- Stakeholders & business hygiene (focus = business) ---
    "stakeholder_sync": {
        "title_ru": "Стейкхолдер-синк",
        "title_en": "Stakeholder sync",
        "description_ru": "Встреча с заказчиком и стейкхолдерами: показать roadmap, обсудить риски, договориться о приоритетах. Снимает напряжение давления инвестора.",
        "description_en": "Meet with the customer and stakeholders: show the roadmap, discuss risks, align priorities. Eases investor pressure.",
        "category": "business",
        "focus": "business",
        "icon": "🤝",
        "cap_cost": 0,
        "budget_cost": 0,
        "cooldown_weeks": 2,
        "po_action_cost": 1,
        "effects": {"trust": 4, "satisfaction": 1},
        "side_effects": {"investor_pressure_release": 1},
    },
    "prioritization_workshop": {
        "title_ru": "Воркшоп по приоритизации",
        "title_en": "Prioritization workshop",
        "description_ru": "Команда вместе сортирует беклог по ценности и риску. Следующий цикл идёт точнее, меньше переделок.",
        "description_en": "The team sorts the backlog by value and risk together. The next cycle is sharper, with less rework.",
        "category": "business",
        "focus": "business",
        "icon": "🗂️",
        "cap_cost": 0,
        "budget_cost": 0,
        "cooldown_weeks": 3,
        "po_action_cost": 1,
        "effects": {"capacity_delta": 4, "satisfaction": 1, "tech_debt": -1},
        "side_effects": {"next_release_risk_buff": 6},
    },
    # --- Engineering: tech debt (focus = tech_debt) ---
    "tech_debt_sprint": {
        "title_ru": "Спринт по техдолгу",
        "title_en": "Tech-debt sprint",
        "description_ru": "Команда фокусированно режет долг: рефакторинг, чистка флагов, медленные запросы. Дорого по capacity, но даёт стабильность.",
        "description_en": "A focused tech-debt push: refactors, flag cleanup, slow queries. Pricey on capacity, but builds stability.",
        "category": "engineering",
        "focus": "tech_debt",
        "icon": "🧹",
        "cap_cost": 18,
        "budget_cost": 0,
        "cooldown_weeks": 4,
        "po_action_cost": 1,
        "max_per_game": 3,
        "effects": {"tech_debt": -10, "stability": 6, "satisfaction": -1},
    },
    "team_one_on_one": {
        "title_ru": "1:1 с инженерами",
        "title_en": "Engineering 1:1s",
        "description_ru": "Поговорить с инженерами: где буксуем, что мешает, какие риски не видны на дайли. Маленькое снижение долга и риск-баффа на следующий релиз.",
        "description_en": "Quick 1:1s with engineers: where we get stuck, what's invisible at standup. Small debt reduction and a risk buffer for the next release.",
        "category": "engineering",
        "focus": "tech_debt",
        "icon": "👂",
        "cap_cost": 0,
        "budget_cost": 0,
        "cooldown_weeks": 2,
        "po_action_cost": 1,
        "effects": {"tech_debt": -2, "satisfaction": 1, "trust": 1},
        "side_effects": {"next_release_risk_buff": 5},
    },
    # --- Engineering: architecture (focus = architecture) ---
    "arch_review": {
        "title_ru": "Архитектурный обзор",
        "title_en": "Architecture review",
        "description_ru": "Сессия с тех-лидом: смотрим узкие места, точки отказа, что готово ли к нагрузке. Снижает риск опоздать с релизом.",
        "description_en": "A session with the tech lead: bottlenecks, failure points, scaling readiness. Lowers slip risk on the next release.",
        "category": "engineering",
        "focus": "architecture",
        "icon": "🏛️",
        "cap_cost": 0,
        "budget_cost": 0,
        "cooldown_weeks": 2,
        "po_action_cost": 1,
        "effects": {"stability": 2, "tech_debt": -1, "trust": 1},
        "side_effects": {"next_release_risk_buff": 8},
    },
    "arch_decision": {
        "title_ru": "Принять архитектурное решение",
        "title_en": "Architecture decision",
        "description_ru": "Сделать выбор по большому архитектурному вопросу (база, очередь, разбиение сервиса). Долгий хвост на стабильности и долге.",
        "description_en": "Commit to a big architectural decision (DB, queue, service split). Pays off in stability and debt over time.",
        "category": "engineering",
        "focus": "architecture",
        "icon": "🧭",
        "cap_cost": 12,
        "budget_cost": 0,
        "cooldown_weeks": 3,
        "po_action_cost": 1,
        "max_per_game": 3,
        "effects": {"stability": 4, "tech_debt": -4, "trust": 1},
    },
    # --- Scrum events (process, focus не учитываем в квотах) ---
    "daily": {
        "title_ru": "Сходить на Daily Stand-up",
        "title_en": "Attend Daily Stand-up",
        "description_ru": "Синк по поставке: статус, риски, зависимости. Без дайли PO не в курсе части ситуации с поставкой и слеп к части рисков в работе.",
        "description_en": "Sync on delivery, risks, and dependencies. Without it the PO misses part of the story and is blind to some delivery issues.",
        "category": "scrum",
        "focus": None,
        "icon": "🧍",
        "cap_cost": 0,
        "budget_cost": 0,
        "cooldown_weeks": 1,
        "po_action_cost": 0,
        "effects": {"capacity_delta": 2},
        "side_effects": {"mark_daily": True},
    },
    "refinement": {
        "title_ru": "Провести Backlog Refinement",
        "title_en": "Run Backlog Refinement",
        "description_ru": "Уточняешь беклог с командой. Следующий цикл получит немного больше capacity — оценки точнее.",
        "description_en": "Refine the backlog with the team. The next cycle gets a small capacity bump — estimates get sharper.",
        "category": "scrum",
        "focus": None,
        "icon": "📋",
        "cap_cost": 0,
        "budget_cost": 0,
        "cooldown_weeks": 1,
        "po_action_cost": 1,
        "effects": {"capacity_delta": 5, "tech_debt": -1},
    },
    "sprint_review": {
        "title_ru": "Провести Sprint Review",
        "title_en": "Run Sprint Review",
        "description_ru": "Смотрите приращение, собирайте фидбэк. Без обзора PO не получает сигнала от стейкхолдеров — выше риск принять неверный продуктовый курс на следующем цикле.",
        "description_en": "See the increment and collect feedback. Without it, the PO lacks external signal — product bets get riskier.",
        "category": "scrum",
        "focus": None,
        "icon": "🔍",
        "cap_cost": 0,
        "budget_cost": 0,
        "cooldown_weeks": 2,
        "po_action_cost": 0,
        "requires": {"cycle_end_week": True},
        "effects": {"trust": 4, "satisfaction": 2, "stability": 1},
        "side_effects": {"mark_sprint_review": True},
    },
    "retro": {
        "title_ru": "Провести Retrospective",
        "title_en": "Run Retrospective",
        "description_ru": "Процесс и качество сотрудничества. Без ретро команда не снимает трения — работа в следующем цикле заметно медленнее и дороже по ретворку.",
        "description_en": "Process and team health. Without it friction sticks — the next cycle costs more in rework and drag.",
        "category": "scrum",
        "focus": None,
        "icon": "🔧",
        "cap_cost": 0,
        "budget_cost": 0,
        "cooldown_weeks": 2,
        "po_action_cost": 0,
        "requires": {"cycle_end_week": True},
        "effects": {"tech_debt": -5, "stability": 3, "satisfaction": 1},
        "side_effects": {"mark_retro": True},
    },
}


def _localize_action(action_id: str, action: Dict[str, Any], locale: str) -> Dict[str, Any]:
    title = action.get("title_en") if locale == "en" else action.get("title_ru")
    desc = action.get("description_en") if locale == "en" else action.get("description_ru")
    return {
        "id": action_id,
        "title": title,
        "description": desc,
        "category": action.get("category"),
        "focus": action.get("focus"),
        "icon": action.get("icon"),
        "cap_cost": int(action.get("cap_cost", 0)),
        "budget_cost": int(action.get("budget_cost", 0)),
        "cooldown_weeks": int(action.get("cooldown_weeks", 0)),
        "po_action_cost": int(action.get("po_action_cost", 0)),
        "max_per_game": action.get("max_per_game"),
        "requires": action.get("requires") or {},
        "effects": action.get("effects") or {},
    }


# --------------------------- english strings ---------------------------
# Перевод заголовков/описаний для основных текстов; ключи стабильные.

_EVENT_TITLES_EN: Dict[str, Dict[str, str]] = {
    "notif_complaints": {"title": "Notification complaints",
        "description": "Users miss important messages and complain about noisy notifications."},
    "competitor_channels": {"title": "Competitor launched channels",
        "description": "A competitor shipped channels for creators and communities. Some users discuss leaving."},
    "outage": {"title": "Service outage",
        "description": "The service was down for hours during peak time."},
    "investor_money": {"title": "Investor pushes for revenue",
        "description": "The investor wants to see real money in the next few weeks."},
    "privacy_panic": {"title": "Privacy panic",
        "description": "Social media argues whether messengers are safe. Users ask about data protection."},
    "regulator": {"title": "Regulator wants data localization",
        "description": "Local regulator requires user data to stay inside the country."},
    "viral_growth": {"title": "Viral moment",
        "description": "A famous blogger invited their audience. A wave of new users hits at once."},
    "team_burnout": {"title": "Team burnout",
        "description": "The team complains: four straight weeks of overtime."},
    "data_leak": {"title": "Data leak headlines",
        "description": "Journalists wrote about a vulnerability — fix it, talk to press, decide tone."},
    "growth_dip": {"title": "Growth stalled",
        "description": "New signups dropped — you need a new activation or retention idea."},
    "ads_backlash": {"title": "Ads backlash",
        "description": "Users openly complain that ads in a messenger are too much."},
    "support_overload": {"title": "Support overloaded",
        "description": "The queue grew, replies are slow, users are angry."},
    "flaky_login": {"title": "Flaky login",
        "description": "Some users can't sign in after the latest update — reports across platforms."},
    "key_dev_offer": {"title": "Key engineer got an offer",
        "description": "A senior engineer got an offer. Two big components depend on them."},
    "pricing_pressure": {"title": "Competitor cut prices",
        "description": "The main rival cut their plan by 30%. Some paying users start asking questions."},
    "partner_integration": {"title": "Big partner wants integration",
        "description": "A well-known service wants to embed your messenger — thousands of new users, but engineering work."},
    "analytics_blind": {"title": "Blind spots in analytics",
        "description": "The team realises: nobody knows which features are actually used. Decisions are made on hunches."},
    "accessibility_complaint": {"title": "Accessibility complaint",
        "description": "A user with special needs posted publicly: 'your product is impossible to use'."},
    "appstore_review": {"title": "AppStore wants product changes",
        "description": "The store demands you remove a feature or rework the data policy, otherwise no release."},
    "infra_cost_spike": {"title": "Infrastructure cost spike",
        "description": "This month's cloud bill is up 1.7× — traffic growth and bad configs."},
    "payment_outage_crisis": {"title": "Crisis: payments unstable",
        "description": "After monetization launch, some charges are duplicated while others fail. Support and social channels are on fire."},
    "security_zero_day_crisis": {"title": "Crisis: zero-day in production",
        "description": "A critical vulnerability surfaced: parts of private data could be exposed through legacy service chains."},
    "funding_crunch_crisis": {"title": "Crisis: funding crunch",
        "description": "Cash runway is shrinking faster than planned: investors demand hard cost discipline and proof of execution."},
}

_EVENT_OPTIONS_EN: Dict[str, Dict[str, Dict[str, str]]] = {
    "notif_complaints": {
        "improve": {"title": "Redo notifications", "description": "Slower, but properly contextual."},
        "delay": {"title": "Delay", "description": "Not a priority right now."},
        "quick": {"title": "Quick fix", "description": "A workaround for a couple of days."},
        "interview": {"title": "Run problem interviews first", "description": "Talk to 5 users — maybe the issue isn't notifications, it's the content."},
    },
    "competitor_channels": {
        "rush": {"title": "Rush channels out", "description": "Big growth, big risk."},
        "research": {"title": "Research the need", "description": "Understand first, build better."},
        "focus": {"title": "Double down on current users", "description": "Don't chase the competitor."},
        "ab_test": {"title": "Run an A/B test for channels", "description": "Ship a minimal version to 10% of users — measure demand cheaply."},
    },
    "outage": {
        "stabilize": {"title": "Freeze features and stabilize", "description": "Team fixes the platform."},
        "compensate": {"title": "Apologize and compensate", "description": "Loyalty bonuses."},
        "ignore": {"title": "Ignore", "description": "Pretend nothing happened."},
    },
    "investor_money": {
        "ads": {"title": "Launch ads", "description": "Fast money, painful trust hit."},
        "subscription": {"title": "Launch Premium", "description": "Cleaner, but value matters."},
        "delay": {"title": "Delay monetization", "description": "Trust over revenue, investor pushes back."},
        "traffic": {"title": "Invest in paid traffic", "description": "Budget into marketing: quick growth, but without retention they'll churn."},
    },
    "privacy_panic": {
        "e2ee": {"title": "Ship end-to-end encryption", "description": "Expensive, strong stance."},
        "policy": {"title": "Publish a security policy", "description": "PR move, comms budget."},
        "ignore": {"title": "Do nothing", "description": "Wait until the topic fades."},
    },
    "regulator": {
        "comply": {"title": "Comply", "description": "Heavy infra migration."},
        "partial": {"title": "Partial compliance", "description": "Cover only critical scenarios."},
        "lobby": {"title": "Lawyers buy time", "description": "Hope the rule softens."},
    },
    "viral_growth": {
        "scale": {"title": "Scale fast", "description": "Spin up the cluster, buy capacity."},
        "ride": {"title": "Ride the wave", "description": "Hope the system survives."},
        "queue": {"title": "Signup queue", "description": "Cool the hype, save the system."},
        "solution_iv": {"title": "Solution interviews with hot users", "description": "Find out what hooked them — aim at the value core, not just traffic."},
    },
    "team_burnout": {
        "rest": {"title": "Pause new features", "description": "Rest and small fixes."},
        "hire": {"title": "Hire quickly", "description": "Expensive and slow to ramp up."},
        "push": {"title": "Push through", "description": "One more sprint, pay the price later."},
    },
    "data_leak": {
        "transparent": {"title": "Transparent post-mortem", "description": "Own it, show the fix."},
        "lawyers": {"title": "Lawyers and silence", "description": "Minimal comments, NDAs."},
        "fix_only": {"title": "Fix it quietly", "description": "Just patch and move on."},
    },
    "growth_dip": {
        "onboarding": {"title": "Rebuild onboarding", "description": "Better first-time experience."},
        "referral": {"title": "Referral program", "description": "Pay for invites."},
        "wait": {"title": "Do nothing", "description": "Focus on other things."},
    },
    "ads_backlash": {
        "soften": {"title": "Soften the ads", "description": "Less money, more trust."},
        "double": {"title": "Double down on targeting", "description": "More money now, more pain later."},
        "explain": {"title": "Explain why ads exist", "description": "Open stance: 'we need them to survive'."},
    },
    "support_overload": {
        "scale_support": {"title": "Scale support", "description": "Hire, train, set SLAs."},
        "ai_bot": {"title": "Launch an AI bot", "description": "Cover routine, risk on edge cases."},
        "fyi": {"title": "Just a FAQ", "description": "Cheapest path."},
    },
    "flaky_login": {
        "hotfix": {"title": "Urgent hotfix", "description": "Rollback + patch in 1 day. Distracts the team from the sprint."},
        "investigate": {"title": "Full investigation", "description": "Take 3 days, fix the root cause, add an alert."},
        "communicate_only": {"title": "Communicate, don't fix", "description": "Apologise, ask people to reinstall — it'll fade."},
    },
    "key_dev_offer": {
        "counter_offer": {"title": "Counter-offer + growth plan", "description": "Keep them: bonus, growth track, clear next 6 months."},
        "share_knowledge": {"title": "Spread the knowledge", "description": "Don't keep them at any cost — distribute the expertise."},
        "let_go": {"title": "Let them go", "description": "We'll cope. Risk goes up sharply."},
    },
    "pricing_pressure": {
        "match_price": {"title": "Lower the price", "description": "Catch up to the market: less revenue, but no churn."},
        "value_pack": {"title": "Add value to the plan", "description": "Don't touch price, ship more features into the paid tier."},
        "ignore_market": {"title": "Don't react", "description": "Our price is justified — let the market decide."},
    },
    "partner_integration": {
        "build_integration": {"title": "Build the integration", "description": "Two weeks of team time on API, docs, SLAs."},
        "minimal_api": {"title": "Minimal public API", "description": "Open endpoints as-is — let the partner integrate themselves."},
        "decline": {"title": "Decline", "description": "Not our priority right now — focus on the core product."},
    },
    "analytics_blind": {
        "instrument": {"title": "Roll out product analytics", "description": "Events, funnels, dashboards — see how it's actually used."},
        "user_panel": {"title": "Set up a user panel", "description": "Recurring interviews with a fixed cohort — qualitative depth."},
        "trust_gut": {"title": "Trust the team's gut", "description": "Decide we have enough — keep moving on intuition."},
    },
    "accessibility_complaint": {
        "fix_a11y": {"title": "Fix the key issues", "description": "Contrast, button size, screen-reader support on main screens."},
        "audit_only": {"title": "Order an audit", "description": "Team keeps building; the audit will reveal the scope."},
        "deflect": {"title": "Reply with a template", "description": "PR brush-off: 'thanks for the feedback, we're working on it'."},
    },
    "appstore_review": {
        "comply_quick": {"title": "Comply and ship", "description": "Team quickly adapts to the requirements."},
        "negotiate": {"title": "Lawyers try to negotiate", "description": "Time and money on talks — release will slip."},
        "remove_feature": {"title": "Pull the feature", "description": "Quickest path — lose part of the user base."},
    },
    "infra_cost_spike": {
        "optimize": {"title": "Optimise infrastructure", "description": "Team digs into configs, caches, instance sizes."},
        "reserve": {"title": "Buy reserves", "description": "Volume contract — save on prod."},
        "absorb": {"title": "Just keep paying", "description": "Don't distract the team — but the budget hole grows."},
    },
    "payment_outage_crisis": {
        "war_room": {"title": "Run a crisis war room", "description": "Freeze part of the roadmap and fix the incident with support and finance together."},
        "rollback_payments": {"title": "Roll back payment release", "description": "Temporarily disable the broken flow: lose money, regain control."},
        "deny_issue": {"title": "Call it isolated cases", "description": "Publicly minimise the scope and keep pushing sales."},
    },
    "security_zero_day_crisis": {
        "containment": {"title": "Containment + emergency patch", "description": "Isolate risky flows fast, ship a patch, accept temporary limits."},
        "full_audit": {"title": "Full security audit + bug bounty", "description": "Expensive and heavy, but sharply reduces repeat incidents."},
        "quiet_fix": {"title": "Quiet fix without public statement", "description": "Save face now, risk bigger fallout if it leaks later."},
    },
    "funding_crunch_crisis": {
        "cost_freeze": {"title": "Hard cost freeze", "description": "Cut non-core activities, focus only on unit-economics survival."},
        "bridge_round": {"title": "Raise a bridge round", "description": "Buy time via investor deal with tougher KPIs."},
        "cut_people": {"title": "Cut the team", "description": "Fast financial relief with heavy morale and engineering damage."},
    },
}

_FEATURE_EN: Dict[str, Dict[str, str]] = {
    "reactions": {"title": "Message reactions", "description": "Reply with an emotion in one tap."},
    "voice": {"title": "Voice messages", "description": "The most requested ask."},
    "channels": {"title": "Communities & channels", "description": "Big feature — creators get audiences."},
    "premium": {"title": "Premium subscription", "description": "Cloud storage, themes, emoji."},
    "ads": {"title": "Ads in channels", "description": "Fast money."},
    "e2ee": {"title": "End-to-end encryption", "description": "Trust grows, expensive build."},
    "stabilize": {"title": "Platform stabilization", "description": "Not a feature — investment in quality."},
    "redesign": {"title": "UI redesign", "description": "Fresh look, better navigation."},
    "stickers": {"title": "Stickers marketplace", "description": "Content + a bit of revenue."},
    "analytics": {"title": "Author analytics", "description": "Supports channels — authors stick around."},
    "observability": {"title": "Metrics & observability",
        "description": "Telemetry + alerts: spot incidents before users do."},
    "platform_split": {"title": "Break the monolith",
        "description": "Big architecture investment: split into services. Pays off debt, raises stability."},
    "ci_cd": {"title": "CI/CD & autotests",
        "description": "Automated delivery pipeline. Faster releases, fewer regressions."},
    "onboarding": {"title": "First-run onboarding",
        "description": "Tooltips, checklist, the first 'aha' moment in 90 seconds."},
    "search": {"title": "Smart message search",
        "description": "Fast, contextual search — users stop losing valuable threads."},
    "moderation": {"title": "Moderation tools",
        "description": "Reports, complaints, auto-spam filter. Lowers the risk of channel-wide blow-ups."},
    "referral": {"title": "Referral program",
        "description": "Users invite friends for a perk. Cheaper than paid traffic if retention holds."},
    "data_export": {"title": "User data export",
        "description": "Download all chats and media as an archive. Trust grows because the lock-in feels lighter."},
    "translate": {"title": "Message translation",
        "description": "Auto-translate captions and messages: opens up an international audience."},
    "mobile_perf": {"title": "Mobile client optimisation",
        "description": "Faster chat open, less battery drain, smoother scroll. Invisible — and therefore valuable."},
    "private_groups": {"title": "Invite-only private groups",
        "description": "Closed communities with invites and moderation — a premium segment."},
    "user_testing": {"title": "Usability tests on key flows",
        "description": "5 users through 3 scenarios — find friction before release."},
    "mini_app_sdk": {"title": "Mini-apps SDK",
        "description": "Open the platform to third-party developers. A big ecosystem bet."},
    "smart_notifications": {"title": "Smart notifications",
        "description": "Priority pushes and quiet hours: less noise, more value."},
    "threaded_replies": {"title": "Threaded replies",
        "description": "Structured reply threads keep long discussions readable."},
    "anti_spam_ml": {"title": "ML anti-spam",
        "description": "Machine-learning spam detection and suspicious account filtering."},
    "backup_restore": {"title": "Backup and restore",
        "description": "Automatic backups and safer restore flows for user data."},
    "team_admin_panel": {"title": "Team admin panel",
        "description": "Roles, permissions, and admin audit logs for B2B teams."},
    "sla_monitoring": {"title": "SLA monitoring",
        "description": "Public SLA dashboards and internal degradation alerts."},
    "message_scheduling": {"title": "Scheduled messages",
        "description": "Compose now, send later — improved communication control."},
    "offline_mode": {"title": "Offline mode",
        "description": "Drafts and chat cache without network, with auto-sync later."},
    "crm_integration": {"title": "CRM integration",
        "description": "Connect CRM data and customer context directly in chats."},
    "api_rate_limits": {"title": "API keys and rate limits",
        "description": "Protect APIs from abuse with scoped keys and throttling."},
    "dark_mode_plus": {"title": "Advanced dark mode",
        "description": "Theme, font and contrast controls for long daily usage."},
    "voice_transcription": {"title": "Voice transcription",
        "description": "Automatic speech-to-text for voice messages."},
    "incident_playbooks": {"title": "Incident playbooks",
        "description": "Standardized incident response procedures for production outages."},
    "tenant_isolation": {"title": "Tenant isolation",
        "description": "Stronger data isolation in multi-tenant architecture."},
    "cost_optimizer": {"title": "Infra cost optimizer",
        "description": "Autoscaling and right-sizing to reduce cloud spend."},
    "knowledge_base": {"title": "In-app knowledge base",
        "description": "Self-service help center embedded into the product."},
    "compliance_audit": {"title": "Compliance audit",
        "description": "Data access, retention and policy checks for regulatory readiness."},
}


# --------------------------- helpers ---------------------------


def _uid() -> int:
    return int(get_jwt_identity())


def _resolve_locale(explicit: Optional[str], session: Optional[AgileTrainingSession]) -> str:
    lc = (explicit or "").strip().lower()
    if lc in {"ru", "en"}:
        return lc
    lc = (getattr(session, "locale", None) or "ru") if session else "ru"
    return lc if lc in {"ru", "en"} else "ru"


def _group_by_slug(slug: str) -> Optional[AgileTrainingGroup]:
    return AgileTrainingGroup.query.filter_by(slug=(slug or "").strip()).first()


def _group_and_session(slug: str):
    g = _group_by_slug(slug)
    if not g:
        return None, None
    sess = AgileTrainingSession.query.get(g.session_id)
    return g, sess


def _require_participant(group: AgileTrainingGroup, token: str) -> Optional[AgileTrainingParticipant]:
    if not token:
        return None
    return (
        AgileTrainingParticipant.query
        .filter_by(group_id=group.id, participant_token=token)
        .first()
    )


def _safe_json_load(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        v = json.loads(raw)
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _clamp(v: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, v))


def _clamp_text(value, limit: int = 1200) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    return s[:limit]


# --------------------------- localization ---------------------------


def _localize_event(ev: Dict[str, Any], locale: str) -> Dict[str, Any]:
    """Возвращает событие с применёнными EN-строками (если locale=en)."""
    if locale != "en":
        return ev
    eid = ev["id"]
    titles = _EVENT_TITLES_EN.get(eid, {})
    options_en = _EVENT_OPTIONS_EN.get(eid, {})
    out = dict(ev)
    if "title" in titles:
        out["title"] = titles["title"]
    if "description" in titles:
        out["description"] = titles["description"]
    out_options = []
    for opt in ev.get("options", []):
        oid = opt["id"]
        en = options_en.get(oid, {})
        out_options.append({
            **opt,
            "title": en.get("title", opt["title"]),
            "description": en.get("description", opt["description"]),
        })
    out["options"] = out_options
    return out


def _localize_feature(f: Dict[str, Any], locale: str) -> Dict[str, Any]:
    if locale != "en":
        return f
    en = _FEATURE_EN.get(f["key"], {})
    return {**f, "title": en.get("title", f["title"]), "description": en.get("description", f["description"])}


# --------------------------- engine ---------------------------


def _initial_state() -> Dict[str, Any]:
    return {
        "version": 1,
        "phase": PHASE_LOBBY,
        "current_week": 0,
        "scenario": "messenger",
        "metrics": {
            "users": 10000,
            "active_users": 4000,
            "satisfaction": 65,
            "stability": 72,
            "tech_debt": 20,
            "trust": 68,
        },
        "revenue_total": 0,
        "revenue_per_week": 0,
        "ad_strength": 0,
        "monetization_on": False,
        "investor_pressure": 0,
        "budget": START_BUDGET,
        "capacity_left": CAPACITY_PER_CYCLE,
        "cycle_index": 1,         # 1..10 (по 2 недели каждый)
        "feature_choice_open": False,
        "feature_options": [],
        "feature_releases": [],
        "pending_releases": [],   # фичи, которые не доехали и поедут в след. цикл
        "unlocked_feature_keys": [],
        "last_event_id": None,    # id события прошлой недели — для антиповтора
        "current_event": None,
        "event_resolved": True,
        "votes": {"event": {}, "feature": {}},
        "vote_by_token": {"event": {}, "feature": {}},
        "history": [],
        "metrics_history": [],
        "weekly_recaps": [],
        "pending_recap_week": None,
        "did_daily_this_week": False,
        "skipped_daily_last_week": False,
        "po_actions": {},          # {action_id: {last_used_week, count}}
        "po_action_log": [],       # история всех применений PO-действий
        "po_actions_used_this_week": 0,
        "po_actions_per_week_limit": PO_ACTIONS_PER_WEEK_LIMIT,
        # Квоты PO: эталон 50/30/20 (бизнес/тех. долг/архитектура).
        "quotas": dict(QUOTA_DEFAULTS),
        "quota_history": [],            # [{cycle, actual_pct: {...}, deviations: {...}, penalty: {..}}]
        "cycle_focus_load": {f: 0 for f in QUOTA_FOCUSES},  # cap, потраченный по фокусам в текущем цикле
        "next_release_risk_buff_pct": 0.0,  # бафф от solution_interview
        "next_release_slip_penalty_pct": 0.0,  # штраф: не ходил на review / т.п.
        "next_week_cap_adj": 0,  # снимаем со «свежей» ёмкости следующей недели
        "scrum_by_cycle": {},  # { "1": { "review": true, "retro": false }, ... }
        "status": STATUS_ALIVE,
        "death_reason": None,
        "leaderboard_unlocked_weeks": [],
        "facilitator_comments": [],
        "ai_calls": {},
        "roles": {},
        "participants": {},
        "consequences_text": "",
        "recent_feature_count": 0,
        "weeks_without_revenue_after_monetization": 0,
        "weekly_metric_log": [],   # per-metric reasoning: почему изменилась метрика
        # --- Premium subscription pricing ---
        # Активируется после релиза фичи `premium`. До релиза price=None и
        # фронт прячет панель цены.
        "premium_unlocked": False,
        "premium_price": PREMIUM_BASE_PRICE,
        "premium_subscribers": 0,           # текущая платящая база (медленно меняется)
        "premium_revenue_per_week": 0,      # сколько Premium приносит в неделю
        "premium_price_history": [],        # [{week, price}]
        "premium_last_changed_week": 0,     # для cooldown
        "updated_at": _now_iso(),
    }


def _seeded_random(group_id: int, week: int, salt: str = "") -> random.Random:
    raw = f"{group_id}:{week}:{salt}".encode("utf-8")
    seed = int(hashlib.sha256(raw).hexdigest()[:12], 16)
    return random.Random(seed)


def _apply_metric_delta(
    data: Dict[str, Any],
    delta: Dict[str, Any],
    struct: Optional[List[Dict[str, Any]]] = None,
    source: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Применяет числовой эффект варианта/фичи к data, возвращает человеческие лейблы изменений.

    Если передан `struct` — заполняет его машинно-читаемыми записями вида
    ``{"key": "satisfaction", "delta": 5, "type": "metric"}``. Это нужно фронту,
    чтобы локализовать названия метрик (RU/EN), а не показывать английские ключи.

    Если передан `source` — каждое заполненное в `struct` событие также
    регистрируется в `data["weekly_metric_log"]` с указанием источника
    (decision / feature_release / po_action / passive / scrum_penalty).
    Используется для построения «почему изменилась метрика» в recap.
    """
    m = data["metrics"]
    notes: List[str] = []
    track = struct if struct is not None else None
    week_log = data.setdefault("weekly_metric_log", []) if source else None

    def push_struct(record: Dict[str, Any]) -> None:
        if track is not None:
            track.append(record)
        if week_log is not None:
            log_rec = dict(record)
            log_rec["week"] = int(source.get("week", data.get("current_week", 0)) or 0)
            log_rec["source"] = source.get("source")
            if "source_id" in source:
                log_rec["source_id"] = source["source_id"]
            if "source_title" in source:
                log_rec["source_title"] = source["source_title"]
            week_log.append(log_rec)

    def bump(name: str, value: float, lo=0, hi=100, fmt="±{v}"):
        cur = m[name]
        new = _clamp(cur + value, lo, hi)
        if abs(new - cur) >= 0.01:
            m[name] = round(new, 1) if isinstance(new, float) else int(new)
            applied = int(round(new - cur))
            notes.append(f"{name} {fmt.format(v=int(round(value)))}")
            push_struct({"type": "metric", "key": name, "delta": applied})

    for k in METRIC_KEYS:
        if k in delta:
            bump(k, float(delta[k]))

    if "users_pct" in delta:
        cur = m["users"]
        diff = int(round(cur * float(delta["users_pct"]) / 100.0))
        m["users"] = max(0, cur + diff)
        m["active_users"] = max(0, m["active_users"] + int(diff * 0.4))
        notes.append(f"users {'+' if diff >= 0 else ''}{diff}")
        push_struct({"type": "users", "key": "users", "delta": diff})

    if "active_users_pct" in delta:
        cur = m["active_users"]
        diff = int(round(cur * float(delta["active_users_pct"]) / 100.0))
        m["active_users"] = max(0, cur + diff)
        notes.append(f"active_users {'+' if diff >= 0 else ''}{diff}")
        push_struct({"type": "users", "key": "active_users", "delta": diff})

    if "churn_bump" in delta:
        pct = float(delta["churn_bump"])
        cur = m["users"]
        lost = int(round(cur * pct / 100.0))
        m["users"] = max(0, cur - lost)
        m["active_users"] = max(0, m["active_users"] - int(lost * 0.5))
        notes.append(f"churn -{lost}")
        push_struct({"type": "churn", "key": "users", "delta": -lost})

    if "growth_pct" in delta:
        data["pending_growth_pct"] = float(data.get("pending_growth_pct", 0)) + float(delta["growth_pct"])

    if "capacity_delta" in delta:
        data["capacity_left"] = max(0, int(data.get("capacity_left", CAPACITY_PER_CYCLE)) + int(delta["capacity_delta"]))
        notes.append(f"capacity {int(delta['capacity_delta']):+d}")
        push_struct({"type": "capacity", "key": "capacity", "delta": int(delta["capacity_delta"])})

    if "budget_delta" in delta:
        data["budget"] = int(data.get("budget", 0)) + int(delta["budget_delta"])
        notes.append(f"budget {int(delta['budget_delta']):+d}")
        push_struct({"type": "budget", "key": "budget", "delta": int(delta["budget_delta"])})

    if "revenue_per_week" in delta:
        data["revenue_per_week"] = max(0, int(data.get("revenue_per_week", 0)) + int(delta["revenue_per_week"]))
        notes.append(f"revenue/week → {data['revenue_per_week']}")
        push_struct({"type": "revenue_rate", "key": "revenue_per_week", "delta": int(delta["revenue_per_week"]),
                     "value": int(data["revenue_per_week"])})

    if "monetization_on" in delta and delta["monetization_on"]:
        data["monetization_on"] = True

    if "ad_strength" in delta:
        prev = int(data.get("ad_strength", 0))
        data["ad_strength"] = max(0, prev + int(delta["ad_strength"]))
        push_struct({"type": "ad_strength", "key": "ad_strength", "delta": int(delta["ad_strength"])})

    if "investor_pressure_delta" in delta:
        data["investor_pressure"] = int(data.get("investor_pressure", 0)) + int(delta["investor_pressure_delta"])
        push_struct({"type": "investor_pressure", "key": "investor_pressure",
                     "delta": int(delta["investor_pressure_delta"])})

    if "tech_debt_delta" in delta:
        bump("tech_debt", float(delta["tech_debt_delta"]))

    return notes


def _push_metric_log(
    data: Dict[str, Any],
    *,
    week: int,
    metric: str,
    delta: int,
    source: str,
    source_id: Optional[str] = None,
    source_title: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Дописывает в `weekly_metric_log` запись «метрика X изменилась на Y из-за Z».

    Используется для пассивных и системных эффектов, которые не идут через
    `_apply_metric_delta` (рост/отток, штрафы за пропуск Scrum-ритуалов и т.п.).
    """
    if not metric or delta == 0:
        return
    rec = {
        "week": int(week or 0),
        "type": "metric",
        "key": metric,
        "delta": int(delta),
        "source": source,
    }
    if source_id is not None:
        rec["source_id"] = source_id
    if source_title is not None:
        rec["source_title"] = source_title
    if extra:
        rec.update(extra)
    data.setdefault("weekly_metric_log", []).append(rec)


def _apply_passive_week(data: Dict[str, Any]) -> None:
    """Пассивный шаг недели: рост/отток, выручка, давление техдолга."""
    m = data["metrics"]
    week_now = int(data.get("current_week", 0) or 0)
    # active ratio тяготеет к функции от satisfaction & stability
    target_ratio = 0.30 + 0.30 * (m["satisfaction"] / 100.0) + 0.10 * (m["stability"] / 100.0)
    target_ratio = _clamp(target_ratio, 0.15, 0.85)
    target_active = int(m["users"] * target_ratio)
    m["active_users"] = int(round(0.6 * m["active_users"] + 0.4 * target_active))

    # органический рост от satisfaction/trust
    base_growth = (m["satisfaction"] - 58) * 0.0010 + (m["trust"] - 62) * 0.0007
    base_growth += float(data.get("pending_growth_pct", 0)) / 100.0
    data["pending_growth_pct"] = float(data.get("pending_growth_pct", 0)) * 0.5  # затухает
    # отток от низкой удовлетворенности и доверия
    churn = max(0.0, (58 - m["satisfaction"]) * 0.0045) + max(0.0, (58 - m["trust"]) * 0.0028)
    churn += max(0.0, (data.get("ad_strength", 0)) * 0.004)

    delta_users = int(round(m["users"] * (base_growth - churn)))
    if delta_users != 0:
        # Понятное «почему»: положительная дельта — органический рост от
        # satisfaction/trust; отрицательная — отток. Источник один,
        # просто разные знаки.
        if base_growth >= churn:
            _push_metric_log(data, week=week_now, metric="users", delta=delta_users,
                             source="passive", source_id="organic_growth")
        else:
            _push_metric_log(data, week=week_now, metric="users", delta=delta_users,
                             source="passive", source_id="churn")
    m["users"] = max(0, m["users"] + delta_users)
    m["active_users"] = min(m["active_users"], m["users"])

    # техдолг медленно растёт сам по себе
    prev_debt = int(m["tech_debt"])
    m["tech_debt"] = int(_clamp(m["tech_debt"] + 0.8, 0, 100))
    if int(m["tech_debt"]) > prev_debt:
        _push_metric_log(data, week=week_now, metric="tech_debt",
                         delta=int(m["tech_debt"]) - prev_debt,
                         source="passive", source_id="time_drift")

    # стабильность зависит от техдолга
    if m["tech_debt"] > 65 and m["stability"] > 25:
        stab_decay = -2 if m["tech_debt"] > 80 else -1
        m["stability"] = int(_clamp(m["stability"] + stab_decay, 0, 100))
        _push_metric_log(data, week=week_now, metric="stability", delta=stab_decay,
                        source="passive", source_id="high_tech_debt")

    # При очень высоких значениях метрики постепенно «разъезжаются» сами по себе:
    # удерживать 95-100 без дисциплины сложно.
    for metric in ("satisfaction", "stability", "trust"):
        cur = int(m.get(metric, 0))
        decay = -2 if cur >= 96 else (-1 if cur >= 88 else 0)
        if decay:
            m[metric] = int(_clamp(cur + decay, 0, 100))
            _push_metric_log(data, week=week_now, metric=metric, delta=decay,
                            source="passive", source_id="high_baseline_decay")

    # Premium pricing — пересчёт подписчиков и недельной выручки от Premium.
    _premium_tick(data)
    # Engineering neglect — разрушение бизнес-метрик при долгом игноре платформы.
    _engineering_neglect_tick(data)

    # выручка
    rev = int(data.get("revenue_per_week", 0))
    # реклама даёт надбавку, пропорциональную active_users
    rev += int((data.get("ad_strength", 0)) * (m["active_users"] / 1000) * 30)
    # Premium subscription добавляет к недельной выручке.
    rev += int(data.get("premium_revenue_per_week", 0) or 0)
    if data.get("monetization_on") and rev <= 0:
        data["weeks_without_revenue_after_monetization"] = int(data.get("weeks_without_revenue_after_monetization", 0)) + 1
    elif rev > 0:
        data["weeks_without_revenue_after_monetization"] = 0
    data["revenue_total"] = int(data.get("revenue_total", 0)) + rev
    data["revenue_this_week"] = rev


def _premium_market_price(week: int) -> int:
    """«Цена на рынке» для Premium-подписки.

    Маленькая синусоида ±10% вокруг базовой — даёт понятный публичный
    ориентир и слегка сдвигается по неделям, как в реальности.
    """
    base = PREMIUM_BASE_PRICE
    swing = 0.1
    factor = 1.0 + swing * math.sin(week / 4.0)
    return int(round(base * factor / 5.0)) * 5  # округляем до 5 ₽


def _premium_conversion_factor(price: int, market: int) -> float:
    """Множитель к базовой конверсии активных пользователей.

    `1.0` — цена ≈ рынок. Выше — конверсия падает (overprice). Ниже —
    немного растёт, но не безгранично (underprice). Возвращает >= 0.
    """
    if market <= 0:
        return 1.0
    ratio = float(price) / float(market)
    if ratio >= 1.0:
        # Над-цена: 1.5× → 0.30; 2.0× → 0.0
        factor = 1.0 - (ratio - 1.0) * PREMIUM_OVERPRICE_DECAY
        return max(0.0, factor)
    # Под-цена: 0.5× → 1.30
    factor = 1.0 + (1.0 - ratio) * PREMIUM_UNDERPRICE_BOOST
    return factor


def _premium_target_subscribers(data: Dict[str, Any], week: int) -> int:
    """Сколько подписчиков должно быть при текущей цене и активной базе."""
    if not data.get("premium_unlocked"):
        return 0
    m = data.get("metrics") or {}
    active = max(0, int(m.get("active_users", 0)))
    market = _premium_market_price(week)
    price = int(data.get("premium_price") or PREMIUM_BASE_PRICE)
    conv = _premium_conversion_factor(price, market) * PREMIUM_BASE_CONVERSION
    # Доверие/удовлетворённость влияют на готовность платить
    sat = int(m.get("satisfaction", 60))
    trust = int(m.get("trust", 60))
    morale = (sat + trust) / 200.0  # 0..1
    morale_factor = 0.4 + morale * 1.2  # 0.4..1.6
    return int(round(active * conv * morale_factor))


def _premium_tick(data: Dict[str, Any]) -> None:
    """Каждую неделю: subscribers подтягиваются к target, начисляется выручка
    Premium, и при сильной над-цене падают satisfaction/trust (платящие злятся).
    """
    if not data.get("premium_unlocked"):
        data["premium_revenue_per_week"] = 0
        return
    week = int(data.get("current_week", 0) or 0)
    target = _premium_target_subscribers(data, week)
    cur = int(data.get("premium_subscribers", 0) or 0)
    new = int(round(cur + (target - cur) * PREMIUM_SUBSCRIBER_INERTIA))
    new = max(0, new)
    data["premium_subscribers"] = new
    price = int(data.get("premium_price") or PREMIUM_BASE_PRICE)
    weekly_rev = int(round(new * price / PREMIUM_WEEKS_PER_MONTH))
    # Premium revenue заходит в общую выручку (revenue_per_week приплюсуется
    # ниже в _apply_passive_week к итоговому rev). Чтобы не задваивать,
    # хранится отдельно и складывается с базовой rate.
    data["premium_revenue_per_week"] = weekly_rev

    # Над-цена → недовольство платящих, отток. Применяем мягко еженедельно.
    market = _premium_market_price(week)
    if price > market:
        over = (price - market) / float(market)
        if over > 0.15:
            sat_delta = -int(round(min(6, over * 6)))
            trust_delta = -int(round(min(4, over * 4)))
            m = data["metrics"]
            m["satisfaction"] = int(_clamp(m["satisfaction"] + sat_delta, 0, 100))
            m["trust"] = int(_clamp(m["trust"] + trust_delta, 0, 100))
            if sat_delta:
                _push_metric_log(data, week=week, metric="satisfaction", delta=sat_delta,
                                 source="passive", source_id="premium_overpriced")
            if trust_delta:
                _push_metric_log(data, week=week, metric="trust", delta=trust_delta,
                                 source="passive", source_id="premium_overpriced")


def _has_recent_engineering_investment(data: Dict[str, Any], week: int, *, lookback_weeks: int = 4) -> bool:
    """Есть ли в последние `lookback_weeks` явные вложения в техдолг/архитектуру.

    Считаем как PO-действия (focus=tech_debt|architecture), так и релизы
    соответствующих фич. Нужен, чтобы отличать «долг растёт, но мы лечим» от
    «долг растёт, и мы уже давно туда не смотрим».
    """
    if lookback_weeks <= 0:
        return False
    from_week = max(1, int(week) - int(lookback_weeks) + 1)

    for rec in (data.get("po_action_log") or []):
        r_week = int(rec.get("week", 0) or 0)
        if r_week < from_week:
            continue
        if rec.get("focus") in {"tech_debt", "architecture"}:
            return True

    for rel in (data.get("feature_releases") or []):
        r_week = int(rel.get("delivered_at_week", rel.get("week", 0)) or 0)
        if r_week < from_week:
            continue
        if rel.get("focus") in {"tech_debt", "architecture"}:
            return True
    return False


def _engineering_neglect_tick(data: Dict[str, Any]) -> None:
    """Каждую неделю: если PO долго игнорирует архитектуру/тех.долг/
    стабильность — продукт «реально начинает разваливаться».

    Теперь штрафы начинаются рано: уже при tech_debt > 20, особенно если
    команда несколько недель почти не инвестирует в tech_debt/architecture.
    Это даёт запрошенный «capacity падает, пользователи уходят», но сохраняет
    путь выхода: регулярные инженерные инвестиции заметно смягчают урон.
    """
    m = data.get("metrics") or {}
    debt = int(m.get("tech_debt", 0))
    stab = int(m.get("stability", 100))
    week = int(data.get("current_week", 0) or 0)
    recent_eng_investment = _has_recent_engineering_investment(data, week, lookback_weeks=4)

    hard = debt > ENG_NEGLECT_DEBT_HARD or stab < ENG_NEGLECT_STAB_HARD
    soft = (debt > ENG_NEGLECT_DEBT_TRIGGER or stab < ENG_NEGLECT_STAB_TRIGGER) and not hard

    # Ранний порог: debt > 20 уже «съедает» delivery-скорость и retention.
    # Если команда инвестирует в тех. основание, штрафы сильно мягче.
    early_debt = debt > 20
    arch_ignored = (week >= 5) and (not recent_eng_investment)

    churn_pct = 0.0
    sat_d = 0
    trust_d = 0
    slip_bump = 0.0
    cap_adj = 0
    source_id = "early_debt"

    if hard:
        churn_pct = ENG_NEGLECT_CHURN_HARD_PCT
        sat_d = -4
        trust_d = -4
        slip_bump = 18.0
        cap_adj = 16
        source_id = "hard"
    elif soft:
        churn_pct = ENG_NEGLECT_CHURN_SOFT_PCT
        sat_d = -2
        trust_d = -2
        slip_bump = 8.0
        cap_adj = 8
        source_id = "soft"
    elif early_debt:
        if debt >= 55:
            churn_pct = 1.8
            sat_d = -3
            trust_d = -3
            slip_bump = 8.0
            cap_adj = 14
            source_id = "debt_55"
        elif debt >= 35:
            churn_pct = 1.2
            sat_d = -2
            trust_d = -2
            slip_bump = 5.0
            cap_adj = 10
            source_id = "debt_35"
        else:  # 21..34
            churn_pct = 0.8
            sat_d = -1
            trust_d = -1
            slip_bump = 3.0
            cap_adj = 6
            source_id = "debt_20"
        # Инвестировали в инженерку недавно — всё ещё больно, но заметно мягче.
        if recent_eng_investment:
            churn_pct *= 0.5
            sat_d = int(round(sat_d * 0.5))
            trust_d = int(round(trust_d * 0.5))
            slip_bump *= 0.5
            cap_adj = int(round(cap_adj * 0.5))
            source_id = f"{source_id}_mitigated"

    if not (hard or soft or early_debt):
        return

    if arch_ignored:
        # «Долго не смотрим в архитектуру» — дополнительный системный налог.
        sat_d -= 1
        trust_d -= 1
        churn_pct += 0.4
        slip_bump += 3.0
        cap_adj += 4
        source_id = f"{source_id}_arch_ignored"

    cur_users = max(0, int(m.get("users", 0)))
    lost = int(round(cur_users * churn_pct / 100.0))
    if lost > 0:
        m["users"] = max(0, cur_users - lost)
        m["active_users"] = max(0, int(m.get("active_users", 0)) - int(lost * 0.5))
        _push_metric_log(data, week=week, metric="users", delta=-lost,
                         source="engineering_neglect",
                         source_id=source_id)
    if sat_d:
        m["satisfaction"] = int(_clamp(m["satisfaction"] + sat_d, 0, 100))
        _push_metric_log(data, week=week, metric="satisfaction", delta=sat_d,
                         source="engineering_neglect",
                         source_id=source_id)
    if trust_d:
        m["trust"] = int(_clamp(m["trust"] + trust_d, 0, 100))
        _push_metric_log(data, week=week, metric="trust", delta=trust_d,
                         source="engineering_neglect",
                         source_id=source_id)
    prev = float(data.get("next_release_slip_penalty_pct", 0) or 0)
    data["next_release_slip_penalty_pct"] = min(40.0, prev + slip_bump)
    if cap_adj > 0:
        # На следующей неделе команда «тушит пожары», эффективная емкость ниже.
        prev_cap_adj = int(data.get("next_week_cap_adj", 0) or 0)
        data["next_week_cap_adj"] = min(70, prev_cap_adj + int(cap_adj))


def _premium_state_view(data: Dict[str, Any]) -> Dict[str, Any]:
    """Сериализованное состояние pricing-панели для фронта."""
    week = int(data.get("current_week", 0) or 0)
    last_changed = int(data.get("premium_last_changed_week", 0) or 0)
    cd_left = max(0, (last_changed + PREMIUM_PRICE_CHANGE_COOLDOWN) - week) if last_changed else 0
    market = _premium_market_price(week)
    price = int(data.get("premium_price") or PREMIUM_BASE_PRICE)
    target = _premium_target_subscribers(data, week) if data.get("premium_unlocked") else 0
    return {
        "unlocked": bool(data.get("premium_unlocked")),
        "price": price,
        "min_price": PREMIUM_MIN_PRICE,
        "max_price": PREMIUM_MAX_PRICE,
        "base_price": PREMIUM_BASE_PRICE,
        "market_price": market,
        "subscribers": int(data.get("premium_subscribers", 0) or 0),
        "subscribers_target": int(target),
        "weekly_revenue": int(data.get("premium_revenue_per_week", 0) or 0),
        "monthly_revenue": int(round(int(data.get("premium_revenue_per_week", 0) or 0) * PREMIUM_WEEKS_PER_MONTH)),
        "cooldown_left_weeks": int(cd_left),
        "cooldown_total_weeks": int(PREMIUM_PRICE_CHANGE_COOLDOWN),
        "last_changed_week": int(last_changed) if last_changed else None,
        "history": list(data.get("premium_price_history") or [])[-10:],
        "conversion_factor": round(_premium_conversion_factor(price, market), 3),
    }


def _evaluate_status(data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    m = data["metrics"]
    reasons = []
    if m["users"] < 2000:
        reasons.append("users<2000")
    if m["satisfaction"] < 25:
        reasons.append("satisfaction<25")
    if m["stability"] < 20:
        reasons.append("stability<20")
    if m["trust"] < 20:
        reasons.append("trust<20")
    if m["tech_debt"] > 95:
        reasons.append("tech_debt>95")
    if data.get("monetization_on") and data.get("weeks_without_revenue_after_monetization", 0) >= 4:
        reasons.append("no_revenue_4_weeks")
    if reasons:
        return STATUS_DEAD, ",".join(reasons)
    risk = []
    if m["users"] < 4000:
        risk.append("users")
    if m["satisfaction"] < 40:
        risk.append("satisfaction")
    if m["stability"] < 40:
        risk.append("stability")
    if m["trust"] < 40:
        risk.append("trust")
    if m["tech_debt"] > 80:
        risk.append("tech_debt")
    if risk:
        return STATUS_AT_RISK, ",".join(risk)
    return STATUS_ALIVE, None


def _eligible_events(data: Dict[str, Any], week: int) -> List[Dict[str, Any]]:
    """События, валидные на этой неделе (триггеры срабатывают, ещё не использованы).

    Жёсткое правило: одно событие = один раз за игру. В каталоге уже больше
    `TOTAL_WEEKS` уникальных событий, так что повторы не нужны.
    """
    used_ids = {h.get("event", {}).get("id") for h in data.get("history", []) if h.get("event")}
    out = []
    for ev in _EVENTS_RU:
        if ev["id"] in used_ids:
            continue
        try:
            if ev["trigger"](data, week):
                out.append(ev)
        except Exception:
            continue
    return out


def _strip_callables(obj: Any) -> Any:
    """Удаляет callable-поля (например, `trigger`-лямбды), чтобы dict можно было сохранить в JSON."""
    if isinstance(obj, dict):
        return {k: _strip_callables(v) for k, v in obj.items() if not callable(v)}
    if isinstance(obj, list):
        return [_strip_callables(v) for v in obj]
    if isinstance(obj, tuple):
        return [_strip_callables(v) for v in obj]
    return obj


def _pick_event(data: Dict[str, Any], week: int, group_id: int) -> Dict[str, Any]:
    """Подбирает событие на неделю.

    Главное правило: за одну игру каждое событие — максимум один раз.
    Сначала смотрим события, у которых уже сработал триггер (есть контекст).
    Если на этой неделе ничего не подошло по триггерам — берём любое из ещё
    не использованных (мягкий fallback). Если все 20+ событий уже были —
    вынужденно повторяем (теоретически невозможно при TOTAL_WEEKS=20).
    """
    rnd = _seeded_random(group_id, week, salt="event")
    used_ids = {h.get("event", {}).get("id") for h in data.get("history", []) if h.get("event")}
    candidates = _eligible_events(data, week)
    if not candidates:
        # Fallback: берём из всех неиспользованных, игнорируя триггеры.
        candidates = [e for e in _EVENTS_RU if e["id"] not in used_ids]
    if not candidates:
        # Совсем последний резерв — каталог исчерпан, разрешаем повтор.
        candidates = list(_EVENTS_RU)

    last_id = data.get("last_event_id")
    if last_id and len(candidates) > 1:
        filtered = [c for c in candidates if c["id"] != last_id]
        if filtered:
            candidates = filtered

    weights = [max(1, int(c.get("weight", 5))) for c in candidates]
    chosen = rnd.choices(candidates, weights=weights, k=1)[0]
    return _strip_callables(chosen)


def _apply_event_appearance(data: Dict[str, Any], ev: Dict[str, Any]) -> None:
    """Эффекты, которые применяются в момент появления события (до решения)."""
    if "applied_on_appear" in ev:
        _apply_metric_delta(
            data,
            ev["applied_on_appear"],
            source={"source": "event_appearance", "source_id": ev.get("id"), "source_title": ev.get("title")},
        )


def _resolve_event_decision(
    data: Dict[str, Any],
    ev: Dict[str, Any],
    option_id: str,
    locale: str,
) -> Tuple[Dict[str, Any], List[str], List[Dict[str, Any]]]:
    chosen = next((o for o in ev["options"] if o["id"] == option_id), None)
    if not chosen:
        chosen = ev["options"][0]
    struct: List[Dict[str, Any]] = []
    notes = _apply_metric_delta(
        data,
        chosen.get("effects", {}),
        struct,
        source={
            "source": "event_decision",
            "source_id": ev.get("id"),
            "source_title": chosen.get("title") or ev.get("title"),
        },
    )

    if chosen.get("unlocks"):
        data.setdefault("unlocked_feature_keys", []).append(chosen["unlocks"])
    return chosen, notes, struct


def _eligible_features(data: Dict[str, Any], locale: str) -> List[Dict[str, Any]]:
    """Список фич, доступных в текущем состоянии."""
    released = {f["key"] for f in data.get("feature_releases", [])}
    sat = data["metrics"]["satisfaction"]
    week = int(data.get("current_week", 0) or 0)
    out = []
    for f in _FEATURES_RU:
        if f["key"] in released:
            continue
        req = f.get("requires") or {}
        if "week_min" in req and week < int(req["week_min"]):
            continue
        if "satisfaction" in req and sat < float(req["satisfaction"]):
            continue
        if "feature" in req and req["feature"] not in released:
            continue
        out.append(_localize_feature(f, locale))
    # ограничим до 5 случайных по seed (но stabilize всегда показываем)
    return out


def _feature_pool_caps(data: Dict[str, Any]) -> Dict[str, int]:
    """Размер пула фич и сколько из них можно пометить как recommended.

    Базово показываем 5 опций. Каждое продуктовое действие из тулкита PO,
    сделанное хотя бы один раз, расширяет «понимание контекста» и открывает
    дополнительные опции:

      problem_interview      → +3 опций (PO лучше понимает аудиторию)
      solution_interview     → +2 + 2 ⭐ recommended (попадание в боль)
      ab_test                → +1 + 1 ⭐ recommended (если ещё нет)
      prioritization_workshop→ +1 бизнес-опция
      stakeholder_sync       → +1 бизнес-опция (узнали ожидания)
      arch_review            → +1 архитектурная опция
      tech_debt_sprint       → +1 архитектурная опция
      team_one_on_one        → +1 архитектурная опция (инженеры подсказали)
      pivot (хотя бы раз)    → +1 ⭐ recommended (свежий взгляд)

    Жёсткий потолок — 14. Идея в том, что PO видит «прямую связь» между
    тем, что он делает с тулкитом, и тем, какой выбор у него на следующем
    цикле. Это держит мотивацию пробовать разные инструменты.

    Возвращает также `reasons` — список ключей причин расширения пула,
    чтобы фронт мог показать «откуда у вас столько опций».
    """
    actions = data.get("po_actions") or {}

    def has_done(action_id: str) -> bool:
        ent = actions.get(action_id) or {}
        return int(ent.get("count", 0) or 0) >= 1

    base_count = 5
    recommended_slots = 0
    bonus_extra_arch = 0
    bonus_extra_business = 0
    reasons: List[str] = []

    if has_done("problem_interview"):
        base_count += 3
        reasons.append("problem_interview")
    if has_done("solution_interview"):
        base_count += 2
        recommended_slots = 2
        reasons.append("solution_interview")
    if has_done("ab_test"):
        base_count += 1
        if recommended_slots < 1:
            recommended_slots = 1
        reasons.append("ab_test")
    if has_done("prioritization_workshop"):
        bonus_extra_business += 1
        reasons.append("prioritization_workshop")
    if has_done("stakeholder_sync"):
        bonus_extra_business += 1
        reasons.append("stakeholder_sync")
    if has_done("arch_review"):
        bonus_extra_arch += 1
        reasons.append("arch_review")
    if has_done("tech_debt_sprint"):
        bonus_extra_arch += 1
        reasons.append("tech_debt_sprint")
    if has_done("team_one_on_one"):
        bonus_extra_arch += 1
        reasons.append("team_one_on_one")
    if has_done("pivot"):
        recommended_slots = max(recommended_slots, 1) + 1
        reasons.append("pivot")
    total = min(14, base_count + bonus_extra_arch + bonus_extra_business)
    return {
        "total": int(total),
        "recommended_slots": int(recommended_slots),
        "bonus_extra_arch": int(bonus_extra_arch),
        "bonus_extra_business": int(bonus_extra_business),
        "reasons": reasons,
    }


def _score_feature_impact(data: Dict[str, Any], f: Dict[str, Any]) -> float:
    """Оценка «потенциальной полезности» фичи в текущем состоянии метрик.

    Используется для выбора recommended-кандидатов после solution-интервью.
    Идея: если у нас низкое доверие — фичи, дающие trust, ценнее; если
    проседает stability — ценнее техдолговые/архитектурные.
    """
    eff = f.get("effects") or {}
    m = data.get("metrics") or {}
    score = 0.0
    score += float(eff.get("satisfaction", 0)) * (1.0 + max(0, 60 - int(m.get("satisfaction", 60))) / 30.0)
    score += float(eff.get("trust", 0)) * (1.0 + max(0, 60 - int(m.get("trust", 60))) / 30.0)
    score += float(eff.get("stability", 0)) * (1.0 + max(0, 60 - int(m.get("stability", 60))) / 30.0)
    score -= float(eff.get("tech_debt", 0)) * (0.7 + max(0, int(m.get("tech_debt", 30)) - 30) / 40.0)
    score += float(eff.get("active_users_pct", 0)) * 1.4
    score += float(eff.get("users_pct", 0)) * 1.0
    score += float(eff.get("revenue_per_week", 0)) / 1500.0
    score -= max(0, int(f.get("capacity", 0)) - 30) * 0.05
    if f.get("key") == "stabilize" and (m.get("stability", 100) < 55 or m.get("tech_debt", 0) > 65):
        score += 4
    return score


def _select_feature_options(data: Dict[str, Any], group_id: int, week: int, locale: str) -> List[Dict[str, Any]]:
    """Собираем опции для окна выбора фич.

    Размер пула зависит от тулкит-активности PO (см. `_feature_pool_caps`):
    минимум 5, максимум 12. Если PO провёл solution-интервью — две фичи
    с лучшим «попаданием в текущие проблемы» помечаются ⭐ recommended.

    Правила:
      • «Стабилизация» всегда внутри пула.
      • Гарантируем минимум две «маленькие» фичи (cap < 40).
      • Поднимаем хотя бы одну architecture и одну tech_debt опцию.
      • Бустеры из тулкита (`prioritization_workshop`, `arch_review`,
        `tech_debt_sprint`) добавляют дополнительный слот в нужном фокусе.
      • Остаток заполняется случайными вариантами по сиду.
    """
    rnd = _seeded_random(group_id, week, salt="features")
    pool = _eligible_features(data, locale)
    by_key = {f["key"]: f for f in pool}

    caps = _feature_pool_caps(data)
    target_total = caps["total"]
    rec_slots = caps["recommended_slots"]

    def take(predicate, count, picked_keys):
        out: List[Dict[str, Any]] = []
        candidates = [f for f in pool if predicate(f) and f["key"] not in picked_keys]
        rnd.shuffle(candidates)
        for f in candidates[:count]:
            out.append(f)
            picked_keys.add(f["key"])
        return out

    picked: List[Dict[str, Any]] = []
    picked_keys: set = set()

    if "stabilize" in by_key:
        picked.append(by_key["stabilize"])
        picked_keys.add("stabilize")

    picked.extend(take(lambda f: int(f.get("capacity", 0)) < 40 and f["key"] != "stabilize", 2, picked_keys))
    picked.extend(take(lambda f: f.get("focus") == "architecture", 1 + caps["bonus_extra_arch"], picked_keys))
    picked.extend(take(lambda f: f.get("focus") == "tech_debt", 1, picked_keys))
    picked.extend(take(lambda f: f.get("focus") == "business" and f["key"] not in picked_keys,
                      caps["bonus_extra_business"], picked_keys))

    while len(picked) < target_total:
        rest = [f for f in pool if f["key"] not in picked_keys]
        if not rest:
            break
        rnd.shuffle(rest)
        f = rest[0]
        picked.append(f)
        picked_keys.add(f["key"])

    # Помечаем recommended после solution-интервью.
    if rec_slots > 0:
        scored = sorted(
            [f for f in picked if f.get("key") != "stabilize"],
            key=lambda f: _score_feature_impact(data, f),
            reverse=True,
        )
        rec_keys = {f["key"] for f in scored[:rec_slots]}
        for f in picked:
            if f["key"] in rec_keys:
                f = dict(f)  # не мутируем _FEATURES_RU
            # Фактически нужно мутировать локальную копию: пересоберём список.
        # Перебираем заново, чтобы реально проставить флаг в копиях.
        marked: List[Dict[str, Any]] = []
        for f in picked:
            if f["key"] in rec_keys:
                marked.append({**f, "recommended": True})
            else:
                marked.append(f)
        picked = marked

    rnd.shuffle(picked)
    if "stabilize" in picked_keys:
        stab = next(f for f in picked if f["key"] == "stabilize")
        picked = [stab] + [f for f in picked if f["key"] != "stabilize"]
    return picked[:target_total]


def _delivery_risk_pct(data: Dict[str, Any], total_committed_cap: int) -> float:
    """Сколько процентов риска того, что фича опоздает на цикл.

    Чем плотнее забили capacity — тем выше риск; ещё подбавляют tech_debt и
    низкая stability. Возвращаем число 0..RISK_MAX_PCT.
    """
    if total_committed_cap <= 0:
        return 0.0
    util_pct = (float(total_committed_cap) / max(1, CAPACITY_PER_CYCLE)) * 100.0
    base = max(0.0, util_pct - RISK_THRESHOLD_PCT) * RISK_SLOPE
    m = data.get("metrics") or {}
    debt = float(m.get("tech_debt", RISK_DEBT_NEUTRAL))
    stab = float(m.get("stability", RISK_STAB_NEUTRAL))
    debt_adj = max(0.0, debt - RISK_DEBT_NEUTRAL) * RISK_DEBT_SLOPE
    stab_adj = max(0.0, RISK_STAB_NEUTRAL - stab) * RISK_STAB_SLOPE
    return max(0.0, min(float(RISK_MAX_PCT), base + debt_adj + stab_adj))


def _focus_load_add(data: Dict[str, Any], focus: Optional[str], cap_used: int) -> None:
    """Учитывает потраченный capacity по нужной оси (business / tech_debt / architecture).

    Действия без focus (Scrum-события и т.п.) и с неположительным cap_used
    игнорируются: они не относятся к продуктовым инвестициям и не должны
    искажать квоты.
    """
    if not focus or focus not in QUOTA_FOCUSES:
        return
    cap_used = int(cap_used or 0)
    if cap_used <= 0:
        return
    bucket = data.setdefault("cycle_focus_load", {f: 0 for f in QUOTA_FOCUSES})
    bucket[focus] = int(bucket.get(focus, 0) or 0) + cap_used


def _quota_evaluation_for_cycle(
    data: Dict[str, Any],
    cycle_index: int,
) -> Optional[Dict[str, Any]]:
    """Сверяет фактическое распределение текущего цикла с квотами PO.

    Возвращает структурированный «отчёт по балансу» и применяет мягкие
    последствия к метрикам: похвала за баланс, мягкий штраф за крупный перекос.
    """
    bucket = data.get("cycle_focus_load") or {}
    total = sum(int(bucket.get(f, 0) or 0) for f in QUOTA_FOCUSES)
    quotas = data.get("quotas") or dict(QUOTA_DEFAULTS)
    if total <= 0:
        return None
    actual_pct: Dict[str, int] = {}
    for f in QUOTA_FOCUSES:
        actual_pct[f] = int(round((int(bucket.get(f, 0) or 0) / float(total)) * 100.0))
    deviations: Dict[str, int] = {f: int(actual_pct[f] - int(quotas.get(f, 0))) for f in QUOTA_FOCUSES}
    abs_dev = {f: abs(d) for f, d in deviations.items()}
    max_dev = max(abs_dev.values()) if abs_dev else 0
    penalty: Dict[str, int] = {}
    struct: List[Dict[str, Any]] = []

    if max_dev <= QUOTA_DEVIATION_TOLERANCE_PCT:
        delta = {"trust": 1, "satisfaction": 1}
        _apply_metric_delta(data, delta, struct, source={"source": "quota_balance"})
        penalty = {"kind": "balance_bonus", "trust": 1, "satisfaction": 1}
    elif max_dev >= QUOTA_DEVIATION_PENALTY_HEAVY:
        # Кто перегнут — туда и боль. Если сильно загнули в business, страдает
        # стабильность и долг копится. Если ушли в tech/arch — давление от
        # инвестора и недовольство пользователей.
        delta: Dict[str, Any] = {}
        biz_dev = deviations.get("business", 0)
        debt_dev = deviations.get("tech_debt", 0)
        arch_dev = deviations.get("architecture", 0)
        if biz_dev >= QUOTA_DEVIATION_PENALTY_HEAVY:
            delta["stability"] = -3
            delta["tech_debt"] = 4
            penalty = {"kind": "biz_overshoot", "stability": -3, "tech_debt": 4}
        elif debt_dev >= QUOTA_DEVIATION_PENALTY_HEAVY:
            delta["satisfaction"] = -2
            delta["investor_pressure_delta"] = 1
            penalty = {"kind": "debt_overshoot", "satisfaction": -2, "investor_pressure": 1}
        elif arch_dev >= QUOTA_DEVIATION_PENALTY_HEAVY:
            delta["satisfaction"] = -2
            delta["users_pct"] = -1
            penalty = {"kind": "arch_overshoot", "satisfaction": -2, "users_pct": -1}
        else:
            # сильно недобрали в чём-то — мягкий штраф по доверию
            delta["trust"] = -2
            penalty = {"kind": "neglect", "trust": -2}
        _apply_metric_delta(data, delta, struct, source={"source": "quota_overshoot",
                                                         "source_id": (penalty or {}).get("kind")})
    else:
        penalty = {"kind": "ok"}

    report = {
        "cycle": int(cycle_index),
        "actual_pct": actual_pct,
        "quotas": dict(quotas),
        "deviations": deviations,
        "max_deviation": int(max_dev),
        "penalty": penalty,
        "struct": struct,
        "ts": _now_iso(),
    }
    data.setdefault("quota_history", []).append(report)
    if len(data["quota_history"]) > 12:
        del data["quota_history"][: len(data["quota_history"]) - 12]
    return report


def _bump_recent_feature_count(data: Dict[str, Any], fkey: str) -> None:
    if fkey == "stabilize":
        data["recent_feature_count"] = max(0, int(data.get("recent_feature_count", 0)) - 1)
    else:
        data["recent_feature_count"] = int(data.get("recent_feature_count", 0)) + 1


def _release_feature(
    data: Dict[str, Any],
    fkey: str,
    week: int,
    locale: str,
    *,
    total_committed_cap: int = 0,
    rnd: Optional[random.Random] = None,
) -> Optional[Dict[str, Any]]:
    """Списать capacity и попытаться отгрузить фичу.

    Если рисковый бросок (по `_delivery_risk_pct`) попадает — фича опаздывает
    на цикл: попадает в `pending_releases`, эффекты не применяются. Capacity
    при этом всё равно списывается (команда работала, но не доехала).
    Когда начнётся следующий цикл — `_process_due_pending_releases` применит
    эффекты и допишет запись в `feature_releases`.
    """
    f = next((x for x in _FEATURES_RU if x["key"] == fkey), None)
    if not f:
        return None
    cap = int(f.get("capacity", 0))
    if data.get("capacity_left", 0) < cap:
        return None
    data["capacity_left"] = int(data["capacity_left"]) - cap

    # Помечена ли эта фича как recommended (например, после solution_interview)?
    opts_by_key = {opt.get("key"): opt for opt in (data.get("feature_options") or [])}
    is_recommended = bool((opts_by_key.get(fkey) or {}).get("recommended"))

    risk_pct = _delivery_risk_pct(data, total_committed_cap or cap)
    risk_buff = float(data.get("next_release_risk_buff_pct", 0) or 0)
    if risk_buff > 0:
        risk_pct = max(0.0, risk_pct - risk_buff)
    slip_pen = float(data.get("next_release_slip_penalty_pct", 0) or 0)
    if slip_pen > 0:
        risk_pct = min(float(RISK_MAX_PCT), risk_pct + slip_pen)
    if is_recommended:
        # Выбор «по подсказке после solution-интервью» — стабильнее.
        risk_pct = max(0.0, risk_pct - 6.0)
    slipped = False
    if risk_pct > 0 and rnd is not None:
        slipped = (rnd.random() * 100.0) < risk_pct
    # бафф/штраф «израсходованы» одним релизом
    data["next_release_risk_buff_pct"] = 0.0
    data["next_release_slip_penalty_pct"] = 0.0

    cur_cycle = int(data.get("cycle_index", 1))
    base_rec = {
        "key": fkey,
        "title": _localize_feature(f, locale)["title"],
        "capacity": cap,
        "started_week": week,
        "started_cycle": cur_cycle,
        "delivery_cycle": cur_cycle,
        "risk_pct": round(risk_pct, 1),
        "slipped": False,
        "recommended": is_recommended,
    }

    focus = f.get("focus")
    base_rec["focus"] = focus
    # Капасити команды списали — это уже инвестиция в выбранную ось,
    # даже если фича опаздывает (она всё равно «съела» работу команды).
    _focus_load_add(data, focus, cap)

    if slipped:
        # Фича уехала в следующий цикл: эффектов пока нет, висит в pending.
        base_rec["slipped"] = True
        base_rec["delivery_cycle"] = cur_cycle + 1
        data.setdefault("pending_releases", []).append(base_rec)
        return base_rec

    effects = dict(f.get("effects", {}) or {})
    bonuses_struct: List[Dict[str, Any]] = []
    if is_recommended:
        # Рекомендованная фича после discovery — небольшой бонус: «попадание в боль».
        # Бонусы применяем как отдельный delta, чтобы фронт мог показать их
        # отдельной строкой «потому что вы сделали solution-интервью».
        boost: Dict[str, Any] = {}
        for k in ("satisfaction", "trust"):
            if effects.get(k, 0):
                boost[k] = max(1, int(round(float(effects[k]) * 0.25)))
        if effects.get("active_users_pct", 0):
            boost["active_users_pct"] = max(1, int(round(float(effects["active_users_pct"]) * 0.3)))
        if not boost:
            boost = {"satisfaction": 1}
        _apply_metric_delta(
            data, boost, bonuses_struct,
            source={"source": "po_action_synergy", "source_id": "solution_interview",
                    "source_title": _localize_feature(f, locale).get("title")},
        )
        for rec_struct in bonuses_struct:
            rec_struct["source"] = "po_action_synergy"
            rec_struct["source_id"] = "solution_interview"

    struct: List[Dict[str, Any]] = []
    notes = _apply_metric_delta(
        data, effects, struct,
        source={"source": "feature_release", "source_id": fkey,
                "source_title": _localize_feature(f, locale).get("title")},
    )
    _bump_recent_feature_count(data, fkey)
    if fkey == "premium":
        # Premium subscription теперь активна — открываем PO панель цены.
        data["premium_unlocked"] = True
        if not data.get("premium_price"):
            data["premium_price"] = PREMIUM_BASE_PRICE
    rec = dict(base_rec)
    rec["week"] = week
    rec["cycle"] = cur_cycle
    rec["delivered_at_week"] = week
    rec["notes"] = notes
    rec["notes_struct"] = struct
    rec["bonus_struct"] = bonuses_struct
    data.setdefault("feature_releases", []).append(rec)
    return rec


def _process_due_pending_releases(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """В начале нового цикла — отгрузить фичи, которые опоздали в прошлый.

    Эффекты применяются только сейчас, а в `feature_releases` появляется
    запись с пометкой «доехало с опозданием».

    Лог per-metric reasons помечается прошлой неделей (week_closed = cur_week-1),
    чтобы попасть в свежий weekly recap, который показывается пользователю
    сразу после закрытия недели.
    """
    cur_cycle = int(data.get("cycle_index", 1))
    cur_week = int(data.get("current_week", 0))
    log_week = max(0, cur_week - 1)
    pending = data.get("pending_releases") or []
    if not pending:
        return []
    delivered: List[Dict[str, Any]] = []
    keep: List[Dict[str, Any]] = []
    for rec in pending:
        if int(rec.get("delivery_cycle", 0)) != cur_cycle:
            keep.append(rec)
            continue
        f = next((x for x in _FEATURES_RU if x["key"] == rec.get("key")), None)
        if not f:
            continue
        struct: List[Dict[str, Any]] = []
        notes = _apply_metric_delta(
            data, f.get("effects", {}), struct,
            source={"source": "feature_release_late", "source_id": rec.get("key"),
                    "source_title": rec.get("title"), "week": log_week},
        )
        _bump_recent_feature_count(data, rec.get("key", ""))
        if rec.get("key") == "premium":
            data["premium_unlocked"] = True
            if not data.get("premium_price"):
                data["premium_price"] = PREMIUM_BASE_PRICE
        bonuses_struct: List[Dict[str, Any]] = []
        if rec.get("recommended"):
            # Опоздавшая, но рекомендованная фича всё равно даёт бонус —
            # она была подобрана под боль, просто доехала позже.
            effects = f.get("effects") or {}
            boost: Dict[str, Any] = {}
            for k in ("satisfaction", "trust"):
                if effects.get(k, 0):
                    boost[k] = max(1, int(round(float(effects[k]) * 0.25)))
            if not boost:
                boost = {"satisfaction": 1}
            _apply_metric_delta(
                data, boost, bonuses_struct,
                source={"source": "po_action_synergy", "source_id": "solution_interview",
                        "source_title": rec.get("title"), "week": log_week},
            )
            for rec_struct in bonuses_struct:
                rec_struct["source"] = "po_action_synergy"
                rec_struct["source_id"] = "solution_interview"
        out = dict(rec)
        out["week"] = cur_week
        out["cycle"] = cur_cycle
        out["delivered_at_week"] = cur_week
        out["notes"] = notes
        out["notes_struct"] = struct
        out["bonus_struct"] = bonuses_struct
        data.setdefault("feature_releases", []).append(out)
        delivered.append(out)
    data["pending_releases"] = keep
    return delivered


def _start_new_cycle_if_needed(data: Dict[str, Any]) -> None:
    """В начале цикла (нечётная неделя) — открываем выбор фичи и пополняем capacity.

    Если из прошлого цикла остались pending фичи — они «доедут» сейчас:
    их cap съедает часть capacity нового цикла (команда всё ещё их доделывает),
    а эффекты применяются ровно в этот момент.
    """
    w = int(data.get("current_week", 0))
    if w == 0 or w > TOTAL_WEEKS:
        return
    if w % CYCLE_LEN == 1:  # неделя 1, 3, 5, ... — старт цикла
        new_cycle = (w + 1) // CYCLE_LEN  # 1..10
        data["cycle_index"] = new_cycle
        # Сбрасываем счётчик распределения по фокусам — стартуем чистый цикл.
        data["cycle_focus_load"] = {f: 0 for f in QUOTA_FOCUSES}
        # Pending releases, которые «дозреют» именно в этом цикле
        carry_cap = sum(
            int(r.get("capacity", 0))
            for r in (data.get("pending_releases") or [])
            if int(r.get("delivery_cycle", 0)) == new_cycle
        )
        data["capacity_left"] = max(0, CAPACITY_PER_CYCLE - carry_cap)
        data["feature_choice_open"] = True
        delivered = _process_due_pending_releases(data)
        if delivered:
            data.setdefault("history", []).append({
                "week": w,
                "kind": "delivery",
                "delivered": delivered,
                "ts": _now_iso(),
            })
        # сами опции пополняются ленивым вызовом, см. /state


def _serialize_state(
    row: AgileTrainingPmSimState,
    data: Dict[str, Any],
    locale: str,
    participant_token: Optional[str],
    is_facilitator: bool = False,
) -> Dict[str, Any]:
    ev = data.get("current_event")
    public_event = None
    if ev:
        public_event = _localize_event(ev, locale)
    feature_opts = data.get("feature_options") or []
    if data.get("feature_choice_open") and not feature_opts:
        feature_opts = []  # фронт запросит ещё раз
    leaderboard_weeks = sorted(set(int(w) for w in (data.get("leaderboard_unlocked_weeks") or [])))
    return {
        "version": int(data.get("version", 0)),
        "phase": data.get("phase", PHASE_LOBBY),
        "current_week": int(data.get("current_week", 0)),
        "total_weeks": TOTAL_WEEKS,
        "cycle_len": CYCLE_LEN,
        "cycle_index": int(data.get("cycle_index", 1)),
        "scenario": data.get("scenario", "messenger"),
        "status": data.get("status", STATUS_ALIVE),
        "death_reason": data.get("death_reason"),
        "metrics": data.get("metrics", {}),
        "revenue_total": int(data.get("revenue_total", 0)),
        "revenue_per_week": int(data.get("revenue_per_week", 0)),
        "revenue_this_week": int(data.get("revenue_this_week", 0)),
        "monetization_on": bool(data.get("monetization_on", False)),
        "ad_strength": int(data.get("ad_strength", 0)),
        "investor_pressure": int(data.get("investor_pressure", 0)),
        "budget": int(data.get("budget", 0)),
        "capacity_left": int(data.get("capacity_left", 0)),
        "feature_choice_open": bool(data.get("feature_choice_open", False)),
        "feature_options": [_localize_feature(f, locale) for f in feature_opts],
        "feature_pool_caps": _feature_pool_caps(data),
        "feature_releases": data.get("feature_releases", []),
        "pending_releases": data.get("pending_releases", []),
        "risk_factors": {
            "capacity_per_cycle": CAPACITY_PER_CYCLE,
            "threshold_pct": RISK_THRESHOLD_PCT,
            "slope": RISK_SLOPE,
            "debt_neutral": RISK_DEBT_NEUTRAL,
            "debt_slope": RISK_DEBT_SLOPE,
            "stab_neutral": RISK_STAB_NEUTRAL,
            "stab_slope": RISK_STAB_SLOPE,
            "max_pct": RISK_MAX_PCT,
        },
        "unlocked_feature_keys": data.get("unlocked_feature_keys", []),
        "current_event": public_event,
        "event_resolved": bool(data.get("event_resolved", True)),
        "votes": data.get("votes", {"event": {}, "feature": {}}),
        "my_vote": {
            "event": (data.get("vote_by_token", {}).get("event", {}) or {}).get(participant_token or "") if participant_token else None,
            "feature": (data.get("vote_by_token", {}).get("feature", {}) or {}).get(participant_token or "") if participant_token else None,
        },
        "history": data.get("history", []),
        "metrics_history": data.get("metrics_history", []),
        "weekly_recaps": data.get("weekly_recaps", []),
        "pending_recap_week": data.get("pending_recap_week"),
        "did_daily_this_week": bool(data.get("did_daily_this_week")),
        "skipped_daily_last_week": bool(data.get("skipped_daily_last_week")),
        "po_actions": data.get("po_actions", {}),
        "po_action_log": (data.get("po_action_log") or [])[-30:],
        "po_action_catalog": _localize_actions_for_state(data, locale),
        "po_actions_used_this_week": int(data.get("po_actions_used_this_week", 0) or 0),
        "po_actions_per_week_limit": int(
            data.get("po_actions_per_week_limit", PO_ACTIONS_PER_WEEK_LIMIT) or PO_ACTIONS_PER_WEEK_LIMIT
        ),
        "quotas": data.get("quotas") or dict(QUOTA_DEFAULTS),
        "quota_defaults": dict(QUOTA_DEFAULTS),
        "quota_focuses": list(QUOTA_FOCUSES),
        "quota_history": (data.get("quota_history") or [])[-6:],
        "cycle_focus_load": data.get("cycle_focus_load") or {f: 0 for f in QUOTA_FOCUSES},
        "premium": _premium_state_view(data),
        "consequences_struct": data.get("consequences_struct") or [],
        "next_release_risk_buff_pct": float(data.get("next_release_risk_buff_pct", 0)),
        "next_release_slip_penalty_pct": float(data.get("next_release_slip_penalty_pct", 0) or 0),
        "next_week_cap_adj": int(data.get("next_week_cap_adj", 0) or 0),
        "scrum_by_cycle": data.get("scrum_by_cycle", {}),
        "leaderboard_unlocked_weeks": leaderboard_weeks,
        "facilitator_comments": data.get("facilitator_comments", []),
        "consequences_text": data.get("consequences_text", ""),
        "participants": data.get("participants", {}),
        "roles": data.get("roles", {}),
        "my": {
            "token": participant_token,
            "role": (data.get("roles", {}) or {}).get(participant_token or ""),
            "is_po": (data.get("roles", {}) or {}).get(participant_token or "") == ROLE_PO,
            "ai_calls": int((data.get("ai_calls", {}) or {}).get(participant_token or "", 0)),
            "ai_calls_limit": AI_CALLS_LIMIT_PER_PARTICIPANT,
        } if participant_token else None,
        "is_facilitator_view": bool(is_facilitator),
    }


def _get_or_init_state(group: AgileTrainingGroup) -> Tuple[AgileTrainingPmSimState, Dict[str, Any]]:
    row = AgileTrainingPmSimState.query.filter_by(group_id=group.id).first()
    if row is None:
        data = _initial_state()
        row = AgileTrainingPmSimState(
            group_id=group.id,
            phase=data["phase"],
            current_week=0,
            status=STATUS_ALIVE,
            revenue_total=0,
            version=1,
            paused=False,
            data_json=json.dumps(data, ensure_ascii=False),
        )
        db.session.add(row)
        db.session.commit()
        return row, data
    data = _safe_json_load(row.data_json) or _initial_state()
    # Лёгкая миграция: подсыпаем поля, которые могли отсутствовать в старых
    # сейвах (квоты, лимит действий PO, focus_load). Делаем без сохранения —
    # запишется при следующем save.
    if "quotas" not in data:
        data["quotas"] = dict(QUOTA_DEFAULTS)
    if "quota_history" not in data:
        data["quota_history"] = []
    if "cycle_focus_load" not in data:
        data["cycle_focus_load"] = {f: 0 for f in QUOTA_FOCUSES}
    if "po_actions_used_this_week" not in data:
        data["po_actions_used_this_week"] = 0
    if "po_actions_per_week_limit" not in data:
        data["po_actions_per_week_limit"] = PO_ACTIONS_PER_WEEK_LIMIT
    if "weekly_metric_log" not in data:
        data["weekly_metric_log"] = []
    if "premium_unlocked" not in data:
        # Если в текущей игре уже зарелизили Premium — открываем pricing-панель.
        released_keys = {f.get("key") for f in (data.get("feature_releases") or [])}
        data["premium_unlocked"] = "premium" in released_keys
        data.setdefault("premium_price", PREMIUM_BASE_PRICE)
        data.setdefault("premium_subscribers", 0)
        data.setdefault("premium_revenue_per_week", 0)
        data.setdefault("premium_price_history", [])
        data.setdefault("premium_last_changed_week", 0)
    return row, data


def _po_action_status(data: Dict[str, Any], action_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
    """Доступно ли действие сейчас? Если нет — почему."""
    week = int(data.get("current_week", 1) or 1)
    log = (data.get("po_actions") or {}).get(action_id) or {}
    last = int(log.get("last_used_week", 0) or 0)
    count = int(log.get("count", 0) or 0)
    cd = int(action.get("cooldown_weeks", 0) or 0)
    cd_left = max(0, (last + cd) - week) if last else 0

    requires = action.get("requires") or {}
    reasons: List[str] = []
    if cd_left > 0:
        reasons.append(f"cooldown:{cd_left}")
    if action.get("max_per_game") is not None and count >= int(action["max_per_game"]):
        reasons.append("max_per_game")
    cap_left = int(data.get("capacity_left", 0) or 0)
    cap_cost = int(action.get("cap_cost", 0) or 0)
    if cap_cost > 0 and cap_left < cap_cost:
        # Команда уже занята фичами — её sprint capacity недостаточно для
        # этого действия. У PO свой бюджет внимания (po_weekly_limit) — если
        # team capacity мало, а PO-бюджет ещё есть, значит выбираем что-то
        # «лёгкое» из тулкита (discovery / scrum), которое не съедает
        # команду. Имя ошибки сужено, чтобы фронт мог показать понятный текст.
        reasons.append("not_enough_team_capacity")
    budget = int(data.get("budget", 0) or 0)
    bcost = int(action.get("budget_cost", 0) or 0)
    if bcost > 0 and budget < bcost:
        reasons.append("not_enough_budget")

    # PO action budget per week — у PO своё «капасити» внимания.
    po_cost = int(action.get("po_action_cost", 0) or 0)
    used = int(data.get("po_actions_used_this_week", 0) or 0)
    limit = int(data.get("po_actions_per_week_limit", PO_ACTIONS_PER_WEEK_LIMIT) or PO_ACTIONS_PER_WEEK_LIMIT)
    if po_cost > 0 and (used + po_cost) > limit:
        reasons.append("po_weekly_limit")
    if "week_min" in requires and week < int(requires["week_min"]):
        reasons.append("too_early")
    if requires.get("cycle_end_week"):
        # «Конец цикла» = чётная неделя (w2, w4, …)
        if week % CYCLE_LEN != 0:
            reasons.append("only_at_cycle_end")
    if "satisfaction" in requires:
        sat = int((data.get("metrics") or {}).get("satisfaction", 0))
        if sat < int(requires["satisfaction"]):
            reasons.append("low_satisfaction")
    if requires.get("after_action"):
        need_id = str(requires["after_action"])
        prev_ent = (data.get("po_actions") or {}).get(need_id) or {}
        prev_cnt = int(prev_ent.get("count", 0) or 0)
        if prev_cnt < 1:
            reasons.append("need_problem_interview")

    phase = data.get("phase")
    if phase != PHASE_PLAYING:
        reasons.append("not_playing")
    return {
        "available": not reasons,
        "blocked_reasons": reasons,
        "cooldown_left_weeks": cd_left,
        "used_count": count,
        "last_used_week": last or None,
    }


def _localize_actions_for_state(data: Dict[str, Any], locale: str) -> List[Dict[str, Any]]:
    out = []
    for aid, a in PO_ACTIONS.items():
        loc = _localize_action(aid, a, locale)
        loc["status"] = _po_action_status(data, aid, a)
        out.append(loc)
    return out


def _apply_po_action(
    data: Dict[str, Any],
    action_id: str,
    locale: str,
) -> Dict[str, Any]:
    """Применяет PO-действие. Возвращает запись для лога."""
    action = PO_ACTIONS[action_id]
    week = int(data.get("current_week", 1) or 1)

    cap_cost = int(action.get("cap_cost", 0) or 0)
    if cap_cost > 0:
        data["capacity_left"] = max(0, int(data.get("capacity_left", 0)) - cap_cost)
    bcost = int(action.get("budget_cost", 0) or 0)
    if bcost > 0:
        data["budget"] = max(0, int(data.get("budget", 0)) - bcost)

    # Учитываем потраченное капасити в выбранной оси (фокусе) — это влияет на
    # сверку с квотами в конце цикла.
    focus = action.get("focus")
    _focus_load_add(data, focus, cap_cost)

    struct: List[Dict[str, Any]] = []
    notes = _apply_metric_delta(
        data, action.get("effects") or {}, struct,
        source={"source": "po_action", "source_id": action_id,
                "source_title": (action.get("title_en") if locale == "en" else action.get("title_ru"))},
    )

    side = action.get("side_effects") or {}
    if side.get("mark_daily"):
        data["did_daily_this_week"] = True
        data["skipped_daily_last_week"] = False
    if side.get("mark_sprint_review"):
        c = int(data.get("cycle_index", 1) or 1)
        b = data.setdefault("scrum_by_cycle", {})
        e = dict(b.get(str(c)) or {})
        e["review"] = True
        b[str(c)] = e
    if side.get("mark_retro"):
        c = int(data.get("cycle_index", 1) or 1)
        b = data.setdefault("scrum_by_cycle", {})
        e = dict(b.get(str(c)) or {})
        e["retro"] = True
        b[str(c)] = e
    if "next_release_risk_buff" in side:
        data["next_release_risk_buff_pct"] = float(data.get("next_release_risk_buff_pct", 0)) + float(side["next_release_risk_buff"])
    if side.get("investor_pressure_release"):
        cur = int(data.get("investor_pressure", 0) or 0)
        data["investor_pressure"] = max(0, cur - int(side["investor_pressure_release"]))

    # PO action budget per week.
    po_cost = int(action.get("po_action_cost", 0) or 0)
    if po_cost > 0:
        data["po_actions_used_this_week"] = int(data.get("po_actions_used_this_week", 0) or 0) + po_cost

    # cooldown / counter
    log = data.setdefault("po_actions", {})
    entry = log.get(action_id) or {}
    entry["last_used_week"] = week
    entry["count"] = int(entry.get("count", 0)) + 1
    log[action_id] = entry

    title = action.get("title_en") if locale == "en" else action.get("title_ru")
    rec = {
        "week": week,
        "action_id": action_id,
        "title": title,
        "category": action.get("category"),
        "focus": focus,
        "icon": action.get("icon"),
        "consequences": notes,
        "consequences_struct": struct,
        "cap_cost": cap_cost,
        "budget_cost": bcost,
        "po_action_cost": po_cost,
        "ts": _now_iso(),
    }
    data.setdefault("po_action_log", []).append(rec)
    data.setdefault("history", []).append({
        "week": week,
        "kind": "po_action",
        "action": {"id": action_id, "title": title, "category": action.get("category"),
                   "focus": focus, "icon": action.get("icon")},
        "consequences": notes,
        "consequences_struct": struct,
        "cap_cost": cap_cost,
        "budget_cost": bcost,
        "po_action_cost": po_cost,
        "ts": _now_iso(),
    })
    return rec


def _save_state(row: AgileTrainingPmSimState, data: Dict[str, Any]) -> None:
    data["version"] = int(data.get("version", 1)) + 1
    data["updated_at"] = _now_iso()
    row.version = data["version"]
    row.phase = data.get("phase") or PHASE_LOBBY
    row.current_week = int(data.get("current_week", 0))
    row.status = data.get("status", STATUS_ALIVE)
    row.revenue_total = int(data.get("revenue_total", 0))
    row.paused = bool(data.get("paused", False))
    row.data_json = json.dumps(data, ensure_ascii=False)
    db.session.commit()


def _touch_participant(data: Dict[str, Any], p: AgileTrainingParticipant) -> None:
    token = p.participant_token
    plist = data.setdefault("participants", {})
    entry = plist.get(token) or {}
    entry["name"] = p.display_name or entry.get("name") or "…"
    entry["role"] = (data.get("roles", {}) or {}).get(token) or entry.get("role")
    entry["last_seen"] = _now_iso()
    entry.setdefault("joined_at", _now_iso())
    plist[token] = entry


def _ensure_event_for_week(data: Dict[str, Any], group_id: int, locale: str) -> None:
    # На неделю нужно одно событие, ни больше, ни меньше. После решения мы
    # НЕ обнуляем `current_event` — это делает только `_close_week_and_advance`
    # при тике следующей недели. Так что наличие любого `current_event` —
    # сигнал «событие на этой неделе уже выдано» и второй раз его создавать
    # не нужно (раньше тут была дыра: на старте цикла, где неделя не тикает
    # до релиза фич, /state повторно выдавал новые события на ту же неделю).
    if data.get("current_event"):
        return
    week = int(data["current_week"])
    if week < 1 or week > TOTAL_WEEKS:
        return
    ev = _pick_event(data, week, group_id)
    data["current_event"] = ev
    data["event_resolved"] = False
    data["votes"] = data.get("votes") or {"event": {}, "feature": {}}
    data["votes"]["event"] = {}
    data.setdefault("vote_by_token", {})["event"] = {}
    _apply_event_appearance(data, ev)


def _ensure_feature_options(data: Dict[str, Any], group_id: int, locale: str) -> None:
    """Поддерживает актуальность пула фич в окне выбора.

    Вызывается каждый раз, когда отдаём `/state` пользователю. Если окно
    выбора закрыто — ничего не делаем. Если ещё не было пула — собираем
    с нуля. Если пул уже есть, но PO между делом сделал тулкит-действия
    и `_feature_pool_caps` подрос — **дополняем** существующий пул, не
    выбрасывая уже видимые карточки и не теряя голоса.
    """
    if not data.get("feature_choice_open"):
        return
    week = int(data.get("current_week", 0) or 0)
    existing = data.get("feature_options") or []
    if not existing:
        data["feature_options"] = _select_feature_options(data, group_id, week, locale)
        data.setdefault("votes", {})["feature"] = {}
        data.setdefault("vote_by_token", {})["feature"] = {}
        return

    caps = _feature_pool_caps(data)
    target_total = int(caps["total"])
    rec_slots = int(caps["recommended_slots"])
    existing_keys = {f.get("key") for f in existing if isinstance(f, dict)}
    current_recommended = sum(1 for f in existing if isinstance(f, dict) and f.get("recommended"))
    needs_more = len(existing) < target_total
    needs_recs = rec_slots > current_recommended
    if not needs_more and not needs_recs:
        return

    rnd = _seeded_random(group_id, week, salt="features-extend")
    pool = _eligible_features(data, locale)

    if needs_more:
        # Сначала пробуем закрыть бизнес/арх/техдолг бонусные слоты, потом
        # добираем случайно. Стабилизацию и уже выбранные не повторяем.
        def take_extra(predicate, count):
            cands = [f for f in pool if predicate(f) and f["key"] not in existing_keys]
            rnd.shuffle(cands)
            out: List[Dict[str, Any]] = []
            for f in cands[:count]:
                out.append(f)
                existing_keys.add(f["key"])
            return out

        slots_left = target_total - len(existing)
        if slots_left > 0:
            existing.extend(take_extra(lambda f: f.get("focus") == "business", min(slots_left, int(caps["bonus_extra_business"]))))
            slots_left = target_total - len(existing)
        if slots_left > 0:
            existing.extend(take_extra(lambda f: f.get("focus") == "architecture", min(slots_left, int(caps["bonus_extra_arch"]))))
            slots_left = target_total - len(existing)
        # любые оставшиеся
        if slots_left > 0:
            rest = [f for f in pool if f["key"] not in existing_keys]
            rnd.shuffle(rest)
            for f in rest[:slots_left]:
                existing.append(f)
                existing_keys.add(f["key"])

    if rec_slots > 0:
        # Пересчитаем «попадание в боль» для актуального списка и помечаем
        # топ rec_slots среди не-стабилизационных фич. Работаем с копиями,
        # чтобы не мутировать _FEATURES_RU.
        non_stab = [f for f in existing if f.get("key") != "stabilize"]
        scored = sorted(non_stab, key=lambda f: _score_feature_impact(data, f), reverse=True)
        rec_keys = {f["key"] for f in scored[:rec_slots]}
        for i, f in enumerate(existing):
            if not isinstance(f, dict):
                continue
            should_be_rec = f.get("key") in rec_keys
            if should_be_rec and not f.get("recommended"):
                existing[i] = {**f, "recommended": True}
            elif not should_be_rec and f.get("recommended"):
                # Если раньше была помечена, но решение по топу сменилось —
                # снимаем флаг.
                cleared = dict(f)
                cleared.pop("recommended", None)
                existing[i] = cleared

    # Гарантируем порядок: «Стабилизация» — первая.
    existing.sort(key=lambda f: 0 if f.get("key") == "stabilize" else 1)
    data["feature_options"] = existing


def _record_metrics_snapshot(data: Dict[str, Any]) -> None:
    m = data["metrics"]
    snap = {
        "week": int(data["current_week"]),
        "users": int(m["users"]),
        "active_users": int(m["active_users"]),
        "satisfaction": int(m["satisfaction"]),
        "stability": int(m["stability"]),
        "tech_debt": int(m["tech_debt"]),
        "trust": int(m["trust"]),
        "revenue_total": int(data.get("revenue_total", 0)),
        "revenue_this_week": int(data.get("revenue_this_week", 0)),
        "status": data.get("status"),
    }
    data.setdefault("metrics_history", []).append(snap)


_RECAP_KEEP = 8  # сколько последних recap'ов хранить


def _snapshot_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    m = data.get("metrics") or {}
    return {
        "users": int(m.get("users", 0)),
        "active_users": int(m.get("active_users", 0)),
        "satisfaction": int(m.get("satisfaction", 0)),
        "stability": int(m.get("stability", 0)),
        "tech_debt": int(m.get("tech_debt", 0)),
        "trust": int(m.get("trust", 0)),
        "revenue_total": int(data.get("revenue_total", 0)),
        "revenue_per_week": int(data.get("revenue_per_week", 0)),
        "capacity_left": int(data.get("capacity_left", 0)),
        "budget": int(data.get("budget", 0)),
    }


def _focus_for_next_week(data: Dict[str, Any], next_week: int) -> Dict[str, Any]:
    """Подсказка PO: куда смотреть на следующей неделе, что не упустить."""
    m = data.get("metrics") or {}
    tech_debt = int(m.get("tech_debt", 0))
    sat = int(m.get("satisfaction", 0))
    trust = int(m.get("trust", 0))
    stab = int(m.get("stability", 0))
    users = int(m.get("users", 0))
    rev = int(data.get("revenue_per_week", 0))
    monetized = bool(data.get("monetization_on", False))
    skipped_daily = bool(data.get("skipped_daily_last_week"))
    focus_key = "balanced"
    if stab < 50 or tech_debt > 65:
        focus_key = "stabilize"
    elif sat < 50:
        focus_key = "discovery"
    elif trust < 50:
        focus_key = "trust"
    elif monetized and rev <= 0:
        focus_key = "monetize_check"
    elif not monetized and next_week >= 9:
        focus_key = "monetize"
    elif users < 6000 and next_week >= 6:
        focus_key = "growth"
    return {
        "key": focus_key,
        "reasons": {
            "tech_debt": tech_debt,
            "stability": stab,
            "satisfaction": sat,
            "trust": trust,
            "users": users,
            "revenue_per_week": rev,
            "skipped_daily_last_week": skipped_daily,
        },
    }


def _build_metric_reasons(data: Dict[str, Any], week: int) -> Dict[str, List[Dict[str, Any]]]:
    """Группирует журнал per-metric изменений за указанную неделю по метрикам.

    Возвращает {metric_key: [ {delta, source, source_id, source_title}, ... ]} —
    готовая для UI «расшифровка», почему каждая метрика поменялась за неделю.
    Чтобы не показывать слишком длинные списки, ужимаем одинаковые источники.
    """
    log = data.get("weekly_metric_log") or []
    out: Dict[str, List[Dict[str, Any]]] = {}
    for rec in log:
        if int(rec.get("week", -1)) != int(week):
            continue
        key = rec.get("key")
        delta = int(rec.get("delta") or 0)
        if not key or delta == 0:
            continue
        bucket = out.setdefault(key, [])
        # Если в этой группе уже есть запись с тем же source/source_id —
        # суммируем, чтобы не плодить дубликаты «satisfaction +2 (release X) ×3».
        merged = None
        for prev in bucket:
            if prev.get("source") == rec.get("source") and prev.get("source_id") == rec.get("source_id"):
                merged = prev
                break
        if merged:
            merged["delta"] = int(merged["delta"]) + delta
        else:
            bucket.append({
                "delta": delta,
                "source": rec.get("source"),
                "source_id": rec.get("source_id"),
                "source_title": rec.get("source_title"),
            })
    # сортируем по убыванию модуля — самые значимые первыми
    for k in list(out.keys()):
        out[k].sort(key=lambda r: -abs(int(r.get("delta") or 0)))
        # отсекаем нулевые после слияния
        out[k] = [r for r in out[k] if int(r.get("delta") or 0) != 0]
        if not out[k]:
            del out[k]
    return out


def _build_weekly_recap(
    data: Dict[str, Any],
    week: int,
    before: Dict[str, Any],
    after: Dict[str, Any],
    extras: Dict[str, Any],
) -> Dict[str, Any]:
    """Сводка по только что закрытой неделе для PO-pop-up на старте следующей."""
    diffs = {}
    for k, v_after in after.items():
        v_before = before.get(k, 0)
        if v_after != v_before:
            diffs[k] = {"before": v_before, "after": v_after, "delta": v_after - v_before}
    next_week = min(TOTAL_WEEKS, week + 1)
    metric_reasons = _build_metric_reasons(data, week)
    return {
        "week": week,
        "next_week": next_week,
        "before": before,
        "after": after,
        "deltas": diffs,
        "metric_reasons": metric_reasons,
        "event": extras.get("event"),
        "decision": extras.get("decision"),
        "decision_notes": extras.get("decision_notes") or [],
        "decision_notes_struct": extras.get("decision_notes_struct") or [],
        "released_features": extras.get("released_features") or [],
        "late_deliveries": extras.get("late_deliveries") or [],
        "scrum_penalty": extras.get("scrum_penalty") or [],
        "quota_report": extras.get("quota_report"),
        "focus": _focus_for_next_week(data, next_week),
        "ts": _now_iso(),
    }


def _apply_next_week_cap_adj(data: Dict[str, Any]) -> None:
    """Штраф capacity, накопленный при закрытии прошлой недели, снимается
    после перехода на новую неделю и (если было) пополнения в _start_new_cycle_if_needed.
    """
    adj = int(data.get("next_week_cap_adj", 0) or 0)
    if adj <= 0:
        return
    data["capacity_left"] = max(0, int(data.get("capacity_left", 0)) - adj)
    data["next_week_cap_adj"] = 0


def _apply_scrum_penalty_if_needed(data: Dict[str, Any], week_closed: int) -> List[Dict[str, Any]]:
    """Scrum: Daily; на чётных неделях — отметки Review/Retro за завершившийся цикл."""
    notes: List[Dict[str, Any]] = []
    m = data.setdefault("metrics", {})
    cap_adj = 0

    if not data.get("did_daily_this_week"):
        m["tech_debt"] = int(_clamp(m.get("tech_debt", 0) + 1, 0, 100))
        m["trust"] = int(_clamp(m.get("trust", 0) - 1, 0, 100))
        cap_adj += 3
        data["skipped_daily_last_week"] = True
        _push_metric_log(data, week=week_closed, metric="tech_debt", delta=1,
                         source="scrum_penalty", source_id="no_daily")
        _push_metric_log(data, week=week_closed, metric="trust", delta=-1,
                         source="scrum_penalty", source_id="no_daily")
        notes.append(
            {
                "reason": "no_daily",
                "narrative_key": "no_daily",
                "tech_debt": 1,
                "trust": -1,
                "next_cap_adj": 3,
            }
        )
    else:
        data["skipped_daily_last_week"] = False

    if week_closed > 0 and week_closed % CYCLE_LEN == 0:
        ended_c = week_closed // CYCLE_LEN
        sc = (data.get("scrum_by_cycle") or {}).get(str(ended_c)) or {}
        if not sc.get("review"):
            m["trust"] = int(_clamp(m.get("trust", 0) - 2, 0, 100))
            prev = float(data.get("next_release_slip_penalty_pct", 0) or 0)
            data["next_release_slip_penalty_pct"] = min(25.0, prev + 5.0)
            _push_metric_log(data, week=week_closed, metric="trust", delta=-2,
                             source="scrum_penalty", source_id="no_sprint_review")
            notes.append(
                {
                    "reason": "no_sprint_review",
                    "narrative_key": "no_review",
                    "trust": -2,
                    "slip_penalty_add": 5.0,
                }
            )
        if not sc.get("retro"):
            m["tech_debt"] = int(_clamp(m.get("tech_debt", 0) + 2, 0, 100))
            cap_adj += 2
            _push_metric_log(data, week=week_closed, metric="tech_debt", delta=2,
                             source="scrum_penalty", source_id="no_retro")
            notes.append(
                {
                    "reason": "no_retro",
                    "narrative_key": "no_retro",
                    "tech_debt": 2,
                    "next_cap_adj": 2,
                }
            )

    data["next_week_cap_adj"] = cap_adj
    data["did_daily_this_week"] = False
    return notes


def _close_week_and_advance(data: Dict[str, Any], group_id: int, locale: str) -> None:
    """Заканчиваем текущую неделю: пассивные эффекты, статус, переход на следующую."""
    week_closed = int(data["current_week"])
    before_metrics = _snapshot_metrics(data)
    last_event = (data.get("current_event") or {}) if data.get("current_event") else None
    last_decision = next(
        (h for h in reversed(data.get("history") or []) if h.get("kind") == "event" and int(h.get("week", -1)) == week_closed),
        None,
    )
    last_feature = next(
        (h for h in reversed(data.get("history") or []) if h.get("kind") == "feature" and int(h.get("week", -1)) == week_closed),
        None,
    )

    _apply_passive_week(data)
    scrum_penalty = _apply_scrum_penalty_if_needed(data, week_closed)

    # Если только что закрылась чётная неделя — это конец цикла. Сверим
    # фактическое распределение работы по фокусам с заявленными квотами.
    quota_report: Optional[Dict[str, Any]] = None
    if week_closed > 0 and week_closed % CYCLE_LEN == 0:
        quota_report = _quota_evaluation_for_cycle(data, int(data.get("cycle_index", 1)))
        if quota_report:
            data.setdefault("history", []).append({
                "week": week_closed,
                "kind": "quota_check",
                "report": quota_report,
                "ts": _now_iso(),
            })

    status, reason = _evaluate_status(data)
    data["status"] = status
    if status == STATUS_DEAD:
        data["death_reason"] = reason
        data["phase"] = PHASE_FINISHED
        _record_metrics_snapshot(data)
        # Финальный recap
        recap = _build_weekly_recap(
            data, week_closed, before_metrics, _snapshot_metrics(data),
            {
                "event": _summarize_event_decision(last_event, last_decision),
                "decision": (last_decision or {}).get("option"),
                "decision_notes": (last_decision or {}).get("consequences"),
                "decision_notes_struct": (last_decision or {}).get("consequences_struct"),
                "released_features": (last_feature or {}).get("released"),
                "scrum_penalty": scrum_penalty,
                "quota_report": quota_report,
            },
        )
        _push_recap(data, recap)
        return
    _record_metrics_snapshot(data)
    if int(data["current_week"]) >= TOTAL_WEEKS:
        data["phase"] = PHASE_FINISHED
        recap = _build_weekly_recap(
            data, week_closed, before_metrics, _snapshot_metrics(data),
            {
                "event": _summarize_event_decision(last_event, last_decision),
                "decision": (last_decision or {}).get("option"),
                "decision_notes": (last_decision or {}).get("consequences"),
                "decision_notes_struct": (last_decision or {}).get("consequences_struct"),
                "released_features": (last_feature or {}).get("released"),
                "scrum_penalty": scrum_penalty,
                "quota_report": quota_report,
            },
        )
        _push_recap(data, recap)
        return
    data["current_week"] = int(data["current_week"]) + 1
    data["current_event"] = None
    data["event_resolved"] = True
    # Бюджет действий PO обновляется каждую неделю.
    data["po_actions_used_this_week"] = 0
    # Запоминаем какие фичи поедут «с опозданием» именно сейчас (до старта цикла)
    pending_for_new_cycle = [
        dict(r) for r in (data.get("pending_releases") or [])
        if int(r.get("delivery_cycle", 0)) == int(data.get("cycle_index", 1)) + 1
    ]
    _start_new_cycle_if_needed(data)
    _apply_next_week_cap_adj(data)
    _ensure_event_for_week(data, group_id, locale)
    _ensure_feature_options(data, group_id, locale)
    after_metrics = _snapshot_metrics(data)
    # late deliveries — то, что только что отгрузилось из pending
    delivered_now = []
    if pending_for_new_cycle:
        delivered_now = [
            r for r in (data.get("feature_releases") or [])
            if int(r.get("delivered_at_week", -1)) == int(data["current_week"]) and r.get("slipped")
        ]
    recap = _build_weekly_recap(
        data, week_closed, before_metrics, after_metrics,
        {
            "event": _summarize_event_decision(last_event, last_decision),
            "decision": (last_decision or {}).get("option"),
            "decision_notes": (last_decision or {}).get("consequences"),
            "decision_notes_struct": (last_decision or {}).get("consequences_struct"),
            "released_features": (last_feature or {}).get("released"),
            "late_deliveries": delivered_now,
            "scrum_penalty": scrum_penalty,
            "quota_report": quota_report,
        },
    )
    _push_recap(data, recap)


def _summarize_event_decision(ev: Optional[Dict[str, Any]], decision_entry: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not ev and not decision_entry:
        return None
    if decision_entry and decision_entry.get("event"):
        return {
            "id": decision_entry["event"].get("id"),
            "title": decision_entry["event"].get("title"),
            "type": decision_entry["event"].get("type"),
        }
    if ev:
        return {"id": ev.get("id"), "title": ev.get("title"), "type": ev.get("type")}
    return None


def _push_recap(data: Dict[str, Any], recap: Dict[str, Any]) -> None:
    arr = data.setdefault("weekly_recaps", [])
    arr.append(recap)
    if len(arr) > _RECAP_KEEP:
        del arr[: len(arr) - _RECAP_KEEP]
    data["pending_recap_week"] = recap["week"]
    # Лог per-metric reasons держим только за последние _RECAP_KEEP недель,
    # чтобы JSON не пух бесконечно — recap уже содержит свою копию reasons.
    log = data.get("weekly_metric_log") or []
    cutoff = int(recap.get("week", 0)) - _RECAP_KEEP
    if log:
        data["weekly_metric_log"] = [r for r in log if int(r.get("week", 0) or 0) > cutoff]


# --------------------------- ai helper ---------------------------

_AI_SYSTEM_RU = (
    "Ты — продуктовый коуч для Product Owner. Объясняй последствия решений короткими "
    "понятными словами на русском в формате Markdown. Не выдумывай числа: говори про "
    "трэйд-оффы качественно. Не давай готовых ответов — задавай 1–2 уточняющих вопроса "
    "команде в конце."
)
_AI_SYSTEM_EN = (
    "You are a product coach for Product Owners. Explain consequences of decisions in "
    "concise English Markdown. Never invent numbers; talk about trade-offs qualitatively. "
    "Don’t give a ready answer — end with 1–2 clarifying questions for the team."
)


def _ai_reply(mode: str, user_input: str, ctx: Dict[str, Any], locale: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    fallback_ru = (
        "**Подумайте о цене решения.**\n\n"
        "У каждой опции есть быстрый эффект и долгий хвост: реклама — деньги сейчас и доверие потом, "
        "стабилизация — меньше боли позже, но без новых фич роста.\n\n"
        "1. Что важнее этой команде в ближайшие 4 недели — деньги, рост или доверие?\n"
        "2. Что вы готовы потерять, чтобы получить желаемое?"
    )
    fallback_en = (
        "**Think about the price of the choice.**\n\n"
        "Each option has a quick effect and a long tail: ads bring revenue now and trust hit later, "
        "stabilization reduces future pain but slows growth.\n\n"
        "1. What matters most to this team in the next 4 weeks — money, growth or trust?\n"
        "2. What are you willing to lose to get what you want?"
    )
    fallback = fallback_ru if locale != "en" else fallback_en
    if not api_key:
        return fallback
    try:
        import requests as _rq
        sys = _AI_SYSTEM_RU if locale != "en" else _AI_SYSTEM_EN
        ctx_lines = [
            f"Неделя: {ctx.get('week')}/{TOTAL_WEEKS}",
            f"Метрики: {ctx.get('metrics')}",
            f"Выручка: {ctx.get('revenue_total')} (в неделю {ctx.get('revenue_per_week', 0)})",
            f"Режим: {mode}",
        ]
        prompt = "\n".join(ctx_lines) + "\n\n" + (user_input or "(нет текста)")
        r = _rq.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "temperature": 0.4,
                "max_tokens": 350,
                "messages": [
                    {"role": "system", "content": sys},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=20,
        )
        if r.ok:
            js = r.json() or {}
            maybe = ((js.get("choices") or [{}])[0].get("message") or {}).get("content")
            if maybe and isinstance(maybe, str) and maybe.strip():
                return maybe.strip()
    except Exception:
        pass
    return fallback


# --------------------------- endpoints: participant ---------------------------


@bp_agile_pm_sim.get("/content")
def content_public():
    locale = _resolve_locale(request.args.get("locale"), None)
    return jsonify({
        "locale": locale,
        "total_weeks": TOTAL_WEEKS,
        "cycle_len": CYCLE_LEN,
        "starting_metrics": _initial_state()["metrics"],
        "starting_budget": START_BUDGET,
        "leaderboard_weeks": list(LEADERBOARD_WEEKS),
        "roles": list(ALLOWED_ROLES),
        "metric_keys": list(METRIC_KEYS) + ["users", "active_users"],
        "po_actions_per_week_limit": PO_ACTIONS_PER_WEEK_LIMIT,
        "quota_focuses": list(QUOTA_FOCUSES),
        "quota_defaults": dict(QUOTA_DEFAULTS),
        "quota_tolerance_pct": QUOTA_DEVIATION_TOLERANCE_PCT,
    })


@bp_agile_pm_sim.get("/g/<slug>/state")
def participant_state(slug: str):
    g, sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    locale = _resolve_locale(request.args.get("locale"), sess)
    token = (request.args.get("participant_token") or "").strip() or None
    row, data = _get_or_init_state(g)

    if data.get("phase") == PHASE_PLAYING:
        _ensure_event_for_week(data, g.id, locale)
        _ensure_feature_options(data, g.id, locale)

    changed = False
    if token:
        p = _require_participant(g, token)
        if p:
            _touch_participant(data, p)
            changed = True
    if changed:
        _save_state(row, data)

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "session": {
            "id": sess.id if sess else None,
            "title": sess.title if sess else "",
            "exercise_key": sess.exercise_key if sess else "pm_sim",
            "locale": sess.locale if sess else "ru",
        },
        "effective_locale": locale,
        "state": _serialize_state(row, data, locale, token),
    })


@bp_agile_pm_sim.post("/g/<slug>/join")
def participant_join(slug: str):
    """Выбрать роль в команде."""
    g, _sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    role = (body.get("role") or "").strip().lower()
    if not token:
        return jsonify({"error": "participant_token required"}), 400
    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404
    if role and role not in ALLOWED_ROLES:
        return jsonify({"error": "invalid role"}), 400

    row, data = _get_or_init_state(g)
    if role:
        # Если на роль PO уже кто-то есть — заменяем владельца роли (договорённость в команде)
        if role == ROLE_PO:
            roles = data.setdefault("roles", {})
            for tk in list(roles.keys()):
                if roles[tk] == ROLE_PO and tk != token:
                    roles[tk] = ROLE_ANALYST
        data.setdefault("roles", {})[token] = role
    _touch_participant(data, p)
    _save_state(row, data)
    return jsonify({"ok": True, "role": (data.get("roles", {}) or {}).get(token)})


@bp_agile_pm_sim.post("/g/<slug>/vote")
def participant_vote(slug: str):
    """Голос за вариант события или за фичу."""
    g, _sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    kind = (body.get("kind") or "").strip()
    choice = (body.get("choice") or "").strip()
    if kind not in {"event", "feature"} or not token:
        return jsonify({"error": "bad request"}), 400
    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404
    row, data = _get_or_init_state(g)

    by_token = data.setdefault("vote_by_token", {})
    by_token.setdefault(kind, {})
    counts = data.setdefault("votes", {}).setdefault(kind, {})

    prev = by_token[kind].get(token)
    if prev and counts.get(prev, 0) > 0:
        counts[prev] -= 1
        if counts[prev] <= 0:
            counts.pop(prev, None)
    if choice:
        by_token[kind][token] = choice
        counts[choice] = int(counts.get(choice, 0)) + 1
    else:
        by_token[kind].pop(token, None)

    _touch_participant(data, p)
    _save_state(row, data)
    return jsonify({"ok": True, "votes": counts, "my": by_token[kind].get(token)})


@bp_agile_pm_sim.post("/g/<slug>/event/decide")
def participant_event_decide(slug: str):
    """PO подтверждает решение по событию недели."""
    g, sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    locale = _resolve_locale(request.args.get("locale"), sess)
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    option_id = (body.get("option_id") or "").strip()
    if not token or not option_id:
        return jsonify({"error": "bad request"}), 400
    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404

    row, data = _get_or_init_state(g)
    if (data.get("roles", {}) or {}).get(token) != ROLE_PO:
        return jsonify({"error": "only PO can confirm"}), 403
    if data.get("phase") != PHASE_PLAYING or data.get("event_resolved", True):
        return jsonify({"error": "no active event"}), 400
    ev = data.get("current_event") or {}
    if not ev:
        return jsonify({"error": "no event"}), 400
    chosen, notes, struct = _resolve_event_decision(data, ev, option_id, locale)

    consequences = ", ".join(notes) if notes else ("без видимых изменений" if locale != "en" else "no visible changes")
    data["consequences_text"] = consequences
    data["consequences_struct"] = struct

    data.setdefault("history", []).append({
        "week": int(data["current_week"]),
        "kind": "event",
        "event": {"id": ev["id"], "title": ev["title"], "type": ev.get("type")},
        "option": {"id": chosen["id"], "title": chosen["title"]},
        "consequences": notes,
        "consequences_struct": struct,
        "votes": dict(data.get("votes", {}).get("event", {})),
        "ts": _now_iso(),
    })

    data["event_resolved"] = True
    data["last_event_id"] = ev.get("id")
    _touch_participant(data, p)

    # если это была неделя с открытым выбором фич, ждём фич; иначе — закрываем неделю
    if not data.get("feature_choice_open"):
        _close_week_and_advance(data, g.id, locale)
    _save_state(row, data)
    return jsonify({"ok": True, "state": _serialize_state(row, data, locale, token)})


@bp_agile_pm_sim.post("/g/<slug>/feature/release")
def participant_feature_release(slug: str):
    """PO подтверждает релиз фичи (или 'skip' = инвестиция в стабильность не выбрана)."""
    g, sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    locale = _resolve_locale(request.args.get("locale"), sess)
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    feature_keys = body.get("feature_keys") or []
    if not isinstance(feature_keys, list):
        feature_keys = []
    feature_keys = [str(k).strip() for k in feature_keys if str(k).strip()]
    if not token:
        return jsonify({"error": "bad request"}), 400
    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404

    row, data = _get_or_init_state(g)
    if (data.get("roles", {}) or {}).get(token) != ROLE_PO:
        return jsonify({"error": "only PO can confirm"}), 403
    if not data.get("feature_choice_open"):
        return jsonify({"error": "feature window closed"}), 400

    # Правило выбора фич — максимально простое:
    #   • суммарный cap выбранных фич не должен превышать текущий
    #     capacity_left (запас цикла);
    #   • «Стабилизация» — солирующее действие: смысл этого пункта
    #     «замораживаем продуктовые фичи в пользу качества», поэтому
    #     комбинировать его с релизом фич нельзя по самой постановке.
    # Раньше тут также было «не больше 2 фич» и «большая фича только в
    # одиночку», но это создавало ситуации «cap=50/100, есть бюджет — но
    # система не даёт выбрать ещё». Теперь решает только capacity.
    by_key = {f["key"]: f for f in _FEATURES_RU}
    chosen = [by_key[k] for k in feature_keys if k in by_key]
    if any(f.get("key") == "stabilize" for f in chosen) and len(chosen) > 1:
        return jsonify({"error": "stabilize_must_be_alone"}), 400
    total_cap = sum(int(f.get("capacity", 0)) for f in chosen)
    if total_cap > int(data.get("capacity_left", 0)):
        return jsonify({"error": "not_enough_capacity"}), 400

    rnd = _seeded_random(g.id, int(data["current_week"]), salt="release")
    released_records = []
    for f in chosen:
        rec = _release_feature(
            data,
            f["key"],
            int(data["current_week"]),
            locale,
            total_committed_cap=total_cap,
            rnd=rnd,
        )
        if rec:
            released_records.append(rec)

    data["feature_choice_open"] = False
    data["feature_options"] = []
    data.setdefault("history", []).append({
        "week": int(data["current_week"]),
        "kind": "feature",
        "released": released_records,
        "votes": dict(data.get("votes", {}).get("feature", {})),
        "ts": _now_iso(),
    })
    data["votes"]["feature"] = {}
    data.setdefault("vote_by_token", {})["feature"] = {}

    _touch_participant(data, p)
    _close_week_and_advance(data, g.id, locale)
    _save_state(row, data)
    return jsonify({"ok": True, "state": _serialize_state(row, data, locale, token)})


@bp_agile_pm_sim.post("/g/<slug>/quotas")
def participant_set_quotas(slug: str):
    """PO задаёт квоты на бизнес/тех. долг/архитектуру.

    Сумма должна быть 100. Каждое значение в [0, 100]. Эталон 50/30/20.
    Квоты сравниваются с фактической работой команды в конце цикла:
    серьёзный перекос — мягкий штраф, баланс — небольшой бонус.
    """
    g, sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    locale = _resolve_locale(request.args.get("locale"), sess)
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    raw = body.get("quotas") or {}
    if not token or not isinstance(raw, dict):
        return jsonify({"error": "bad request"}), 400
    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404

    row, data = _get_or_init_state(g)
    if (data.get("roles", {}) or {}).get(token) != ROLE_PO:
        return jsonify({"error": "only_po"}), 403

    parsed: Dict[str, int] = {}
    for f in QUOTA_FOCUSES:
        try:
            v = int(round(float(raw.get(f, 0))))
        except (TypeError, ValueError):
            return jsonify({"error": "invalid_quota"}), 400
        if v < 0 or v > 100:
            return jsonify({"error": "invalid_quota_range"}), 400
        parsed[f] = v
    if sum(parsed.values()) != 100:
        return jsonify({"error": "quotas_must_sum_to_100"}), 400

    data["quotas"] = parsed
    _touch_participant(data, p)
    _save_state(row, data)
    return jsonify({"ok": True, "quotas": parsed, "state": _serialize_state(row, data, locale, token)})


@bp_agile_pm_sim.post("/g/<slug>/premium-price")
def participant_set_premium_price(slug: str):
    """PO устанавливает цену Premium-подписки.

    Доступно только после релиза фичи `premium`. Изменять можно не чаще
    раза в `PREMIUM_PRICE_CHANGE_COOLDOWN` недель. Цена валидируется по
    диапазону `[PREMIUM_MIN_PRICE, PREMIUM_MAX_PRICE]`. Эффекты
    (новая база подписчиков, выручка, штраф за над-цену) применяются
    в обычном `_premium_tick` в конце недели.
    """
    g, sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    locale = _resolve_locale(request.args.get("locale"), sess)
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    raw_price = body.get("price")
    if not token or raw_price is None:
        return jsonify({"error": "bad request"}), 400
    try:
        price = int(round(float(raw_price)))
    except (TypeError, ValueError):
        return jsonify({"error": "invalid_price"}), 400
    if price < PREMIUM_MIN_PRICE or price > PREMIUM_MAX_PRICE:
        return jsonify({"error": "price_out_of_range",
                        "min": PREMIUM_MIN_PRICE, "max": PREMIUM_MAX_PRICE}), 400
    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404
    row, data = _get_or_init_state(g)
    if (data.get("roles", {}) or {}).get(token) != ROLE_PO:
        return jsonify({"error": "only_po"}), 403
    if data.get("phase") != PHASE_PLAYING:
        return jsonify({"error": "not_playing"}), 400
    if not data.get("premium_unlocked"):
        return jsonify({"error": "premium_locked"}), 400

    week = int(data.get("current_week", 0) or 0)
    last_changed = int(data.get("premium_last_changed_week", 0) or 0)
    if last_changed:
        cd_left = (last_changed + PREMIUM_PRICE_CHANGE_COOLDOWN) - week
        if cd_left > 0:
            return jsonify({"error": "cooldown",
                            "cooldown_left_weeks": int(cd_left)}), 400

    prev_price = int(data.get("premium_price") or PREMIUM_BASE_PRICE)
    if price == prev_price:
        # Молча возвращаем актуальный state — менять нечего.
        return jsonify({"ok": True, "state": _serialize_state(row, data, locale, token)})

    data["premium_price"] = price
    data["premium_last_changed_week"] = week
    history = data.setdefault("premium_price_history", [])
    history.append({"week": week, "price": price, "previous": prev_price})
    if len(history) > 12:
        del history[: len(history) - 12]
    _touch_participant(data, p)
    _save_state(row, data)
    return jsonify({"ok": True, "state": _serialize_state(row, data, locale, token)})


@bp_agile_pm_sim.post("/g/<slug>/po-action")
def participant_po_action(slug: str):
    """PO применяет действие из тулкита (discovery / growth / scrum-event / pivot)."""
    g, sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    locale = _resolve_locale(request.args.get("locale"), sess)
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    action_id = (body.get("action_id") or "").strip()
    if not token or not action_id:
        return jsonify({"error": "bad request"}), 400
    if action_id not in PO_ACTIONS:
        return jsonify({"error": "unknown_action"}), 400
    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404

    row, data = _get_or_init_state(g)
    if (data.get("roles", {}) or {}).get(token) != ROLE_PO:
        return jsonify({"error": "only_po"}), 403
    if data.get("phase") != PHASE_PLAYING:
        return jsonify({"error": "not_playing"}), 400

    action = PO_ACTIONS[action_id]
    status = _po_action_status(data, action_id, action)
    if not status["available"]:
        return jsonify({"error": "blocked", "reasons": status["blocked_reasons"]}), 400

    rec = _apply_po_action(data, action_id, locale)
    # Discovery/scrum-действия меняют размер пула фич (см. _feature_pool_caps).
    # Если окно выбора уже открыто — синхронизируем существующий пул прямо
    # сейчас, чтобы PO увидел новые опции, а не только новую цифру в подсказке.
    _ensure_feature_options(data, g.id, locale)
    _touch_participant(data, p)
    _save_state(row, data)
    return jsonify({"ok": True, "applied": rec, "state": _serialize_state(row, data, locale, token)})


@bp_agile_pm_sim.post("/g/<slug>/start")
def participant_start(slug: str):
    """PO стартует игру (если фасилитатор не нажал старт сам)."""
    g, sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    locale = _resolve_locale(request.args.get("locale"), sess)
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    if not token:
        return jsonify({"error": "bad request"}), 400
    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404

    row, data = _get_or_init_state(g)
    if (data.get("roles", {}) or {}).get(token) != ROLE_PO:
        return jsonify({"error": "only PO can start"}), 403
    if data.get("phase") not in {PHASE_LOBBY, PHASE_INTRO}:
        return jsonify({"error": "already started"}), 400
    data["phase"] = PHASE_PLAYING
    data["current_week"] = 1
    _start_new_cycle_if_needed(data)
    _ensure_event_for_week(data, g.id, locale)
    _ensure_feature_options(data, g.id, locale)
    _record_metrics_snapshot(data)
    _save_state(row, data)
    return jsonify({"ok": True, "state": _serialize_state(row, data, locale, token)})


@bp_agile_pm_sim.post("/g/<slug>/ai-assist")
def ai_assist(slug: str):
    g, sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    mode = (body.get("mode") or "tradeoff").strip().lower()
    user_input = _clamp_text(body.get("user_input"), AI_PROMPT_LIMIT_CHARS) or ""
    if not token:
        return jsonify({"error": "bad request"}), 400
    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404
    locale = _resolve_locale(body.get("locale"), sess)

    row, data = _get_or_init_state(g)
    calls = data.setdefault("ai_calls", {})
    n = int(calls.get(token, 0))
    if n >= AI_CALLS_LIMIT_PER_PARTICIPANT:
        return jsonify({"error": "ai_limit_exceeded"}), 429

    ctx = {
        "week": int(data.get("current_week", 0)),
        "metrics": data.get("metrics"),
        "revenue_total": int(data.get("revenue_total", 0)),
        "revenue_per_week": int(data.get("revenue_per_week", 0)),
    }
    reply = _ai_reply(mode, user_input, ctx, locale)
    calls[token] = n + 1
    _touch_participant(data, p)
    _save_state(row, data)
    return jsonify({"ok": True, "reply": reply, "ai_calls": calls[token],
                     "ai_calls_limit": AI_CALLS_LIMIT_PER_PARTICIPANT})


# --------------------------- endpoints: facilitator ---------------------------


def _check_owner(group_id: int) -> Tuple[Optional[AgileTrainingGroup], Optional[AgileTrainingSession], Optional[Tuple[Any, int]]]:
    g = AgileTrainingGroup.query.get(group_id)
    if not g:
        return None, None, (jsonify({"error": "Group not found"}), 404)
    sess = AgileTrainingSession.query.get(g.session_id)
    if not sess or sess.owner_user_id != _uid():
        return None, None, (jsonify({"error": "Forbidden"}), 403)
    return g, sess, None


@bp_agile_pm_sim.get("/sessions/<int:session_id>/overview")
@jwt_required()
def facilitator_session_overview(session_id: int):
    sess = AgileTrainingSession.query.get(session_id)
    if not sess or sess.owner_user_id != _uid():
        return jsonify({"error": "Forbidden"}), 403
    groups = AgileTrainingGroup.query.filter_by(session_id=session_id).all()
    out = []
    for g in groups:
        row, data = _get_or_init_state(g)
        m = data.get("metrics", {})
        out.append({
            "group": {"id": g.id, "name": g.name, "slug": g.slug},
            "phase": data.get("phase"),
            "current_week": int(data.get("current_week", 0)),
            "revenue_total": int(data.get("revenue_total", 0)),
            "revenue_per_week": int(data.get("revenue_per_week", 0)),
            "status": data.get("status", STATUS_ALIVE),
            "death_reason": data.get("death_reason"),
            "metrics": m,
            "participants_count": len(data.get("participants", {})),
            "version": int(data.get("version", 0)),
            "updated_at": data.get("updated_at"),
            "leaderboard_unlocked_weeks": data.get("leaderboard_unlocked_weeks", []),
        })
    out.sort(key=lambda r: (-int(r["revenue_total"]), -int(r["metrics"].get("users", 0))))
    return jsonify({"session": {"id": sess.id, "title": sess.title, "locale": sess.locale}, "groups": out})


@bp_agile_pm_sim.post("/sessions/<int:session_id>/leaderboard")
@jwt_required()
def facilitator_open_leaderboard(session_id: int):
    """Открыть лидерборд для всех команд этой сессии на конкретной неделе."""
    sess = AgileTrainingSession.query.get(session_id)
    if not sess or sess.owner_user_id != _uid():
        return jsonify({"error": "Forbidden"}), 403
    body = request.get_json(silent=True) or {}
    week = int(body.get("week", 0))
    if week not in LEADERBOARD_WEEKS:
        return jsonify({"error": "invalid week"}), 400
    groups = AgileTrainingGroup.query.filter_by(session_id=session_id).all()
    for g in groups:
        row, data = _get_or_init_state(g)
        weeks = list(data.get("leaderboard_unlocked_weeks") or [])
        if week not in weeks:
            weeks.append(week)
        data["leaderboard_unlocked_weeks"] = sorted(set(int(w) for w in weeks))
        _save_state(row, data)
    return jsonify({"ok": True, "week": week})


@bp_agile_pm_sim.get("/groups/<int:group_id>/state")
@jwt_required()
def facilitator_group_state(group_id: int):
    g, sess, err = _check_owner(group_id)
    if err:
        return err
    row, data = _get_or_init_state(g)
    locale = sess.locale or "ru"
    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "state": _serialize_state(row, data, locale, None, is_facilitator=True),
    })


@bp_agile_pm_sim.post("/groups/<int:group_id>/start")
@jwt_required()
def facilitator_start(group_id: int):
    g, sess, err = _check_owner(group_id)
    if err:
        return err
    locale = sess.locale or "ru"
    row, data = _get_or_init_state(g)
    if data.get("phase") not in {PHASE_LOBBY, PHASE_INTRO}:
        return jsonify({"error": "already started"}), 400
    data["phase"] = PHASE_PLAYING
    data["current_week"] = 1
    _start_new_cycle_if_needed(data)
    _ensure_event_for_week(data, g.id, locale)
    _ensure_feature_options(data, g.id, locale)
    _record_metrics_snapshot(data)
    _save_state(row, data)
    return jsonify({"ok": True})


@bp_agile_pm_sim.post("/groups/<int:group_id>/force-event")
@jwt_required()
def facilitator_force_event(group_id: int):
    """Фасилитатор вручную выбирает событие для текущей недели."""
    g, sess, err = _check_owner(group_id)
    if err:
        return err
    locale = sess.locale or "ru"
    body = request.get_json(silent=True) or {}
    event_id = (body.get("event_id") or "").strip()
    row, data = _get_or_init_state(g)
    if data.get("phase") != PHASE_PLAYING:
        return jsonify({"error": "not playing"}), 400
    ev_raw = next((e for e in _EVENTS_RU if e["id"] == event_id), None)
    if not ev_raw:
        return jsonify({"error": "unknown event"}), 400
    ev = _strip_callables(ev_raw)
    data["current_event"] = ev
    data["event_resolved"] = False
    data["votes"]["event"] = {}
    data.setdefault("vote_by_token", {})["event"] = {}
    _apply_event_appearance(data, ev)
    _save_state(row, data)
    return jsonify({"ok": True, "state": _serialize_state(row, data, locale, None, is_facilitator=True)})


@bp_agile_pm_sim.post("/groups/<int:group_id>/comment")
@jwt_required()
def facilitator_comment(group_id: int):
    g, sess, err = _check_owner(group_id)
    if err:
        return err
    body = request.get_json(silent=True) or {}
    text = _clamp_text(body.get("text"), 800) or ""
    if not text:
        return jsonify({"error": "empty"}), 400
    row, data = _get_or_init_state(g)
    data.setdefault("facilitator_comments", []).append({
        "week": int(data.get("current_week", 0)),
        "text": text,
        "ts": _now_iso(),
    })
    _save_state(row, data)
    return jsonify({"ok": True})


@bp_agile_pm_sim.post("/groups/<int:group_id>/pause")
@jwt_required()
def facilitator_pause(group_id: int):
    g, sess, err = _check_owner(group_id)
    if err:
        return err
    body = request.get_json(silent=True) or {}
    paused = bool(body.get("paused", True))
    row, data = _get_or_init_state(g)
    data["paused"] = paused
    _save_state(row, data)
    return jsonify({"ok": True, "paused": paused})


@bp_agile_pm_sim.post("/groups/<int:group_id>/reset")
@jwt_required()
def facilitator_reset(group_id: int):
    g, sess, err = _check_owner(group_id)
    if err:
        return err
    row = AgileTrainingPmSimState.query.filter_by(group_id=g.id).first()
    fresh = _initial_state()
    if row:
        row.data_json = json.dumps(fresh, ensure_ascii=False)
        row.phase = fresh["phase"]
        row.current_week = 0
        row.status = STATUS_ALIVE
        row.revenue_total = 0
        row.version = fresh["version"]
        row.paused = False
    else:
        db.session.add(AgileTrainingPmSimState(
            group_id=g.id, phase=fresh["phase"], current_week=0,
            status=STATUS_ALIVE, revenue_total=0, version=1, paused=False,
            data_json=json.dumps(fresh, ensure_ascii=False),
        ))
    db.session.commit()
    return jsonify({"ok": True})


@bp_agile_pm_sim.get("/events/catalog")
@jwt_required()
def facilitator_event_catalog():
    """Каталог событий для ручного выбора."""
    locale = _resolve_locale(request.args.get("locale"), None)
    out = []
    for ev in _EVENTS_RU:
        loc = _localize_event(ev, locale)
        out.append({
            "id": loc["id"], "type": loc["type"], "title": loc["title"],
            "description": loc["description"],
            "options": [{"id": o["id"], "title": o["title"]} for o in loc.get("options", [])],
        })
    return jsonify({"events": out})
