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
]


# --------------------------- catalog: features ---------------------------

_FEATURES_RU: List[Dict[str, Any]] = [
    {"key": "reactions", "title": "Реакции на сообщения",
     "description": "Простой способ ответить эмоцией без сообщения.",
     "capacity": 20, "budget": 0,
     "effects": {"users_pct": 3, "satisfaction": 5, "tech_debt": 3}},
    {"key": "voice", "title": "Голосовые сообщения",
     "description": "Самая ожидаемая просьба пользователей.",
     "capacity": 35, "budget": 0,
     "effects": {"active_users_pct": 6, "satisfaction": 4, "stability": -3, "tech_debt": 5}},
    {"key": "channels", "title": "Каналы для сообществ",
     "description": "Большая фича — авторы получают подписчиков.",
     "capacity": 50, "budget": 0,
     "effects": {"users_pct": 12, "tech_debt": 10, "stability": -5, "revenue_potential": 8000}},
    {"key": "premium", "title": "Подписка Premium",
     "description": "Платный пакет: облачное хранение, темы, эмодзи.",
     "capacity": 40, "budget": 0,
     "effects": {"satisfaction": -2, "monetization_on": True, "revenue_per_week": 4000},
     "requires": {"satisfaction": 60}},
    {"key": "ads", "title": "Реклама в каналах",
     "description": "Быстрый источник денег.",
     "capacity": 20, "budget": 0,
     "effects": {"satisfaction": -10, "trust": -5, "monetization_on": True,
                  "revenue_per_week": 5000, "ad_strength": 1}},
    {"key": "e2ee", "title": "Сквозное шифрование",
     "description": "Доверие вырастет, но фича дорогая.",
     "capacity": 45, "budget": 0,
     "effects": {"trust": 18, "satisfaction": 4, "tech_debt": 8}},
    {"key": "stabilize", "title": "Стабилизация платформы",
     "description": "Не фича, а вложение в качество.",
     "capacity": 35, "budget": 0,
     "effects": {"stability": 15, "tech_debt": -10}},
    {"key": "redesign", "title": "Редизайн интерфейса",
     "description": "Свежий вид и переосмысление навигации.",
     "capacity": 30, "budget": 0,
     "effects": {"satisfaction": 8, "active_users_pct": 3, "first_week_satisfaction_dip": 3}},
    {"key": "stickers", "title": "Маркетплейс стикеров",
     "description": "Контент-фича + чуть денег от продаж.",
     "capacity": 25, "budget": 0,
     "effects": {"satisfaction": 4, "users_pct": 2, "revenue_per_week": 1200, "monetization_on": True}},
    {"key": "analytics", "title": "Аналитика для авторов",
     "description": "Поддерживает каналы — авторы остаются дольше.",
     "capacity": 30, "budget": 0,
     "effects": {"satisfaction": 2, "active_users_pct": 4, "tech_debt": 4},
     "requires": {"feature": "channels"}},
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
    # --- Discovery ---
    "problem_interview": {
        "title_ru": "Провести проблемное интервью",
        "title_en": "Run problem interviews",
        "description_ru": "Поговорить с 5 пользователями. Уточняешь настоящую боль — следующая фича попадёт точнее.",
        "description_en": "Talk to 5 users. Sharpen real pain — next feature lands closer to value.",
        "category": "discovery",
        "icon": "🎤",
        "cap_cost": 8,
        "budget_cost": 0,
        "cooldown_weeks": 2,
        "max_per_game": None,
        "effects": {"satisfaction": 2, "trust": 2, "tech_debt": -2},
    },
    "solution_interview": {
        "title_ru": "Провести solution-интервью",
        "title_en": "Run solution interviews",
        "description_ru": "Показать прототип — проверить, решит ли он проблему. Снижает риск опоздать со следующим релизом.",
        "description_en": "Show a prototype — check that it actually solves the problem. Lowers slip risk on the next release.",
        "category": "discovery",
        "icon": "🧪",
        "cap_cost": 6,
        "budget_cost": 0,
        "cooldown_weeks": 2,
        "effects": {"satisfaction": 1, "stability": 2, "tech_debt": -1},
        "side_effects": {"next_release_risk_buff": 12},  # custom hook (см. _apply_po_action)
    },
    "ab_test": {
        "title_ru": "Запустить A/B тест",
        "title_en": "Run an A/B test",
        "description_ru": "Маленький эксперимент вместо большой ставки. Низкий риск, но и эффект скромнее.",
        "description_en": "A small experiment instead of a big bet. Low risk, modest reward.",
        "category": "discovery",
        "icon": "🆎",
        "cap_cost": 10,
        "budget_cost": 0,
        "cooldown_weeks": 2,
        "effects": {"satisfaction": 2, "trust": 1, "active_users_pct": 2, "tech_debt": 2},
    },
    # --- Growth ---
    "traffic_invest": {
        "title_ru": "Вложиться в трафик",
        "title_en": "Invest in paid traffic",
        "description_ru": "Платный трафик: пользователей быстро прибавится, но без удержания они уйдут с разочарованием.",
        "description_en": "Paid traffic: quick user spike. Without retention they churn back disappointed.",
        "category": "growth",
        "icon": "💸",
        "cap_cost": 5,
        "budget_cost": 15000,
        "cooldown_weeks": 3,
        "effects": {"users_pct": 8, "satisfaction": -3, "trust": -1, "ad_strength": 1},
        "requires": {"satisfaction": 50},
    },
    "pivot": {
        "title_ru": "Сделать пивот",
        "title_en": "Pivot",
        "description_ru": "Большая ставка на переосмысление продукта. Дорого, требует фокуса, но восстанавливает доверие и снимает долг.",
        "description_en": "A big bet on rethinking the product. Costly and disruptive, but restores trust and pays off debt.",
        "category": "pivot",
        "icon": "🔄",
        "cap_cost": 40,
        "budget_cost": 10000,
        "cooldown_weeks": 0,
        "max_per_game": 1,
        "requires": {"week_min": 5},
        "effects": {"satisfaction": 6, "trust": 8, "tech_debt": -12, "stability": 4, "users_pct": -5},
    },
    # --- Scrum events ---
    "daily": {
        "title_ru": "Сходить на Daily Stand-up",
        "title_en": "Attend Daily Stand-up",
        "description_ru": "Раз в неделю команда синкается. Если PO не приходит — растёт долг и теряется capacity (в реальной жизни тоже).",
        "description_en": "The team syncs once a week. If the PO skips — tech debt grows and capacity drops (just like in real life).",
        "category": "scrum",
        "icon": "🧍",
        "cap_cost": 0,
        "budget_cost": 0,
        "cooldown_weeks": 1,
        "effects": {"capacity_delta": 2},
        "side_effects": {"mark_daily": True},
    },
    "refinement": {
        "title_ru": "Провести Backlog Refinement",
        "title_en": "Run Backlog Refinement",
        "description_ru": "Уточняешь беклог с командой. Следующий цикл получит немного больше capacity — оценки точнее.",
        "description_en": "Refine the backlog with the team. The next cycle gets a small capacity bump — estimates get sharper.",
        "category": "scrum",
        "icon": "📋",
        "cap_cost": 3,
        "budget_cost": 0,
        "cooldown_weeks": 1,
        "effects": {"capacity_delta": 5, "tech_debt": -1},
    },
    "sprint_review": {
        "title_ru": "Провести Sprint Review",
        "title_en": "Run Sprint Review",
        "description_ru": "Демонстрируешь стейкхолдерам результаты. Доверие растёт, обратная связь — вход в следующий цикл.",
        "description_en": "Demo to stakeholders. Trust grows; feedback feeds into the next cycle.",
        "category": "scrum",
        "icon": "🔍",
        "cap_cost": 0,
        "budget_cost": 0,
        "cooldown_weeks": 2,
        "requires": {"cycle_end_week": True},  # только на чётной неделе цикла (w2,4,6,…)
        "effects": {"trust": 4, "satisfaction": 2, "stability": 1},
    },
    "retro": {
        "title_ru": "Провести Retrospective",
        "title_en": "Run Retrospective",
        "description_ru": "Команда чинит процесс. Долг уменьшается, стабильность растёт.",
        "description_en": "The team fixes its process. Tech debt drops, stability rises.",
        "category": "scrum",
        "icon": "🔧",
        "cap_cost": 2,
        "budget_cost": 0,
        "cooldown_weeks": 2,
        "requires": {"cycle_end_week": True},
        "effects": {"tech_debt": -5, "stability": 3, "satisfaction": 1},
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
        "icon": action.get("icon"),
        "cap_cost": int(action.get("cap_cost", 0)),
        "budget_cost": int(action.get("budget_cost", 0)),
        "cooldown_weeks": int(action.get("cooldown_weeks", 0)),
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
            "satisfaction": 70,
            "stability": 80,
            "tech_debt": 20,
            "trust": 75,
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
        "next_release_risk_buff_pct": 0.0,  # бафф от solution_interview
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
        "updated_at": _now_iso(),
    }


def _seeded_random(group_id: int, week: int, salt: str = "") -> random.Random:
    raw = f"{group_id}:{week}:{salt}".encode("utf-8")
    seed = int(hashlib.sha256(raw).hexdigest()[:12], 16)
    return random.Random(seed)


def _apply_metric_delta(data: Dict[str, Any], delta: Dict[str, Any]) -> List[str]:
    """Применяет числовой эффект варианта/фичи к data, возвращает человеческие лейблы изменений."""
    m = data["metrics"]
    notes: List[str] = []

    def bump(name: str, value: float, lo=0, hi=100, fmt="±{v}"):
        cur = m[name]
        new = _clamp(cur + value, lo, hi)
        if abs(new - cur) >= 0.01:
            m[name] = round(new, 1) if isinstance(new, float) else int(new)
            notes.append(f"{name} {fmt.format(v=int(round(value)))}")

    for k in METRIC_KEYS:
        if k in delta:
            bump(k, float(delta[k]))

    if "users_pct" in delta:
        cur = m["users"]
        diff = int(round(cur * float(delta["users_pct"]) / 100.0))
        m["users"] = max(0, cur + diff)
        # active users пересчитаем через формулу позже, но добавим прирост пропорционально
        m["active_users"] = max(0, m["active_users"] + int(diff * 0.4))
        notes.append(f"users {'+' if diff >= 0 else ''}{diff}")

    if "active_users_pct" in delta:
        cur = m["active_users"]
        diff = int(round(cur * float(delta["active_users_pct"]) / 100.0))
        m["active_users"] = max(0, cur + diff)
        notes.append(f"active_users {'+' if diff >= 0 else ''}{diff}")

    if "churn_bump" in delta:
        # моментальный отток в процентах от users
        pct = float(delta["churn_bump"])
        cur = m["users"]
        lost = int(round(cur * pct / 100.0))
        m["users"] = max(0, cur - lost)
        m["active_users"] = max(0, m["active_users"] - int(lost * 0.5))
        notes.append(f"churn -{lost}")

    if "growth_pct" in delta:
        # отложенный рост в течение цикла
        data["pending_growth_pct"] = float(data.get("pending_growth_pct", 0)) + float(delta["growth_pct"])

    if "capacity_delta" in delta:
        data["capacity_left"] = max(0, int(data.get("capacity_left", CAPACITY_PER_CYCLE)) + int(delta["capacity_delta"]))
        notes.append(f"capacity {int(delta['capacity_delta']):+d}")

    if "budget_delta" in delta:
        data["budget"] = int(data.get("budget", 0)) + int(delta["budget_delta"])
        notes.append(f"budget {int(delta['budget_delta']):+d}")

    if "revenue_per_week" in delta:
        data["revenue_per_week"] = max(0, int(data.get("revenue_per_week", 0)) + int(delta["revenue_per_week"]))
        notes.append(f"revenue/week → {data['revenue_per_week']}")

    if "monetization_on" in delta and delta["monetization_on"]:
        data["monetization_on"] = True

    if "ad_strength" in delta:
        data["ad_strength"] = max(0, int(data.get("ad_strength", 0)) + int(delta["ad_strength"]))

    if "investor_pressure_delta" in delta:
        data["investor_pressure"] = int(data.get("investor_pressure", 0)) + int(delta["investor_pressure_delta"])

    if "tech_debt_delta" in delta:
        bump("tech_debt", float(delta["tech_debt_delta"]))

    return notes


def _apply_passive_week(data: Dict[str, Any]) -> None:
    """Пассивный шаг недели: рост/отток, выручка, давление техдолга."""
    m = data["metrics"]
    # active ratio тяготеет к функции от satisfaction & stability
    target_ratio = 0.30 + 0.30 * (m["satisfaction"] / 100.0) + 0.10 * (m["stability"] / 100.0)
    target_ratio = _clamp(target_ratio, 0.15, 0.85)
    target_active = int(m["users"] * target_ratio)
    m["active_users"] = int(round(0.6 * m["active_users"] + 0.4 * target_active))

    # органический рост от satisfaction/trust
    base_growth = (m["satisfaction"] - 55) * 0.0015 + (m["trust"] - 60) * 0.0010
    base_growth += float(data.get("pending_growth_pct", 0)) / 100.0
    data["pending_growth_pct"] = float(data.get("pending_growth_pct", 0)) * 0.5  # затухает
    # отток от низкой удовлетворенности и доверия
    churn = max(0.0, (55 - m["satisfaction"]) * 0.0035) + max(0.0, (55 - m["trust"]) * 0.0020)
    churn += max(0.0, (data.get("ad_strength", 0)) * 0.003)

    delta_users = int(round(m["users"] * (base_growth - churn)))
    m["users"] = max(0, m["users"] + delta_users)
    m["active_users"] = min(m["active_users"], m["users"])

    # техдолг медленно растёт сам по себе
    m["tech_debt"] = int(_clamp(m["tech_debt"] + 0.5, 0, 100))

    # стабильность зависит от техдолга
    if m["tech_debt"] > 70 and m["stability"] > 30:
        m["stability"] = int(_clamp(m["stability"] - 1, 0, 100))

    # выручка
    rev = int(data.get("revenue_per_week", 0))
    # реклама даёт надбавку, пропорциональную active_users
    rev += int((data.get("ad_strength", 0)) * (m["active_users"] / 1000) * 30)
    if data.get("monetization_on") and rev <= 0:
        data["weeks_without_revenue_after_monetization"] = int(data.get("weeks_without_revenue_after_monetization", 0)) + 1
    elif rev > 0:
        data["weeks_without_revenue_after_monetization"] = 0
    data["revenue_total"] = int(data.get("revenue_total", 0)) + rev
    data["revenue_this_week"] = rev


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
    used_ids = {h.get("event", {}).get("id") for h in data.get("history", []) if h.get("event")}
    out = []
    for ev in _EVENTS_RU:
        if ev.get("once") and ev["id"] in used_ids:
            continue
        if ev["id"] in used_ids and not ev.get("repeats", False):
            # допустим повторы только для investor_money, ads_backlash
            if ev["id"] not in {"investor_money", "ads_backlash", "outage", "support_overload"}:
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
    rnd = _seeded_random(group_id, week, salt="event")
    candidates = _eligible_events(data, week)
    last_id = data.get("last_event_id")
    # Антиповтор: если есть альтернативы, не повторяем событие сразу же.
    if last_id and len(candidates) > 1:
        filtered = [c for c in candidates if c["id"] != last_id]
        if filtered:
            candidates = filtered
    if not candidates:
        # fallback — берём первое событие, которое не повторяет прошлую неделю.
        pool = [e for e in _EVENTS_RU if e["id"] != last_id]
        chosen = pool[0] if pool else _EVENTS_RU[0]
    else:
        weights = [int(c.get("weight", 5)) for c in candidates]
        chosen = rnd.choices(candidates, weights=weights, k=1)[0]
    return _strip_callables(chosen)


def _apply_event_appearance(data: Dict[str, Any], ev: Dict[str, Any]) -> None:
    """Эффекты, которые применяются в момент появления события (до решения)."""
    if "applied_on_appear" in ev:
        _apply_metric_delta(data, ev["applied_on_appear"])


def _resolve_event_decision(
    data: Dict[str, Any],
    ev: Dict[str, Any],
    option_id: str,
    locale: str,
) -> Tuple[Dict[str, Any], List[str]]:
    chosen = next((o for o in ev["options"] if o["id"] == option_id), None)
    if not chosen:
        chosen = ev["options"][0]
    notes = _apply_metric_delta(data, chosen.get("effects", {}))

    if chosen.get("unlocks"):
        data.setdefault("unlocked_feature_keys", []).append(chosen["unlocks"])
    return chosen, notes


def _eligible_features(data: Dict[str, Any], locale: str) -> List[Dict[str, Any]]:
    """Список фич, доступных в текущем состоянии."""
    released = {f["key"] for f in data.get("feature_releases", [])}
    sat = data["metrics"]["satisfaction"]
    out = []
    for f in _FEATURES_RU:
        if f["key"] in released:
            continue
        req = f.get("requires") or {}
        if "satisfaction" in req and sat < float(req["satisfaction"]):
            continue
        if "feature" in req and req["feature"] not in released:
            continue
        out.append(_localize_feature(f, locale))
    # ограничим до 5 случайных по seed (но stabilize всегда показываем)
    return out


def _select_feature_options(data: Dict[str, Any], group_id: int, week: int, locale: str) -> List[Dict[str, Any]]:
    rnd = _seeded_random(group_id, week, salt="features")
    pool = _eligible_features(data, locale)
    must = [f for f in pool if f["key"] in {"stabilize"}]
    rest = [f for f in pool if f["key"] not in {"stabilize"}]
    rnd.shuffle(rest)
    return (must + rest)[:5]


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

    risk_pct = _delivery_risk_pct(data, total_committed_cap or cap)
    risk_buff = float(data.get("next_release_risk_buff_pct", 0) or 0)
    if risk_buff > 0:
        risk_pct = max(0.0, risk_pct - risk_buff)
    slipped = False
    if risk_pct > 0 and rnd is not None:
        slipped = (rnd.random() * 100.0) < risk_pct
    # бафф «израсходован» одним релизом, дальше — обычный риск
    data["next_release_risk_buff_pct"] = 0.0

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
    }

    if slipped:
        # Фича уехала в следующий цикл: эффектов пока нет, висит в pending.
        base_rec["slipped"] = True
        base_rec["delivery_cycle"] = cur_cycle + 1
        data.setdefault("pending_releases", []).append(base_rec)
        return base_rec

    notes = _apply_metric_delta(data, f.get("effects", {}))
    _bump_recent_feature_count(data, fkey)
    rec = dict(base_rec)
    rec["week"] = week
    rec["cycle"] = cur_cycle
    rec["delivered_at_week"] = week
    rec["notes"] = notes
    data.setdefault("feature_releases", []).append(rec)
    return rec


def _process_due_pending_releases(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """В начале нового цикла — отгрузить фичи, которые опоздали в прошлый.

    Эффекты применяются только сейчас, а в `feature_releases` появляется
    запись с пометкой «доехало с опозданием».
    """
    cur_cycle = int(data.get("cycle_index", 1))
    cur_week = int(data.get("current_week", 0))
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
        notes = _apply_metric_delta(data, f.get("effects", {}))
        _bump_recent_feature_count(data, rec.get("key", ""))
        out = dict(rec)
        out["week"] = cur_week
        out["cycle"] = cur_cycle
        out["delivered_at_week"] = cur_week
        out["notes"] = notes
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
        "next_release_risk_buff_pct": float(data.get("next_release_risk_buff_pct", 0)),
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
        reasons.append("not_enough_capacity")
    budget = int(data.get("budget", 0) or 0)
    bcost = int(action.get("budget_cost", 0) or 0)
    if bcost > 0 and budget < bcost:
        reasons.append("not_enough_budget")
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

    notes = _apply_metric_delta(data, action.get("effects") or {})

    side = action.get("side_effects") or {}
    if side.get("mark_daily"):
        data["did_daily_this_week"] = True
        data["skipped_daily_last_week"] = False
    if "next_release_risk_buff" in side:
        data["next_release_risk_buff_pct"] = float(data.get("next_release_risk_buff_pct", 0)) + float(side["next_release_risk_buff"])

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
        "icon": action.get("icon"),
        "consequences": notes,
        "cap_cost": cap_cost,
        "budget_cost": bcost,
        "ts": _now_iso(),
    }
    data.setdefault("po_action_log", []).append(rec)
    data.setdefault("history", []).append({
        "week": week,
        "kind": "po_action",
        "action": {"id": action_id, "title": title, "category": action.get("category"), "icon": action.get("icon")},
        "consequences": notes,
        "cap_cost": cap_cost,
        "budget_cost": bcost,
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
    if not data.get("feature_choice_open"):
        return
    if data.get("feature_options"):
        return
    data["feature_options"] = _select_feature_options(data, group_id, int(data["current_week"]), locale)
    data.setdefault("votes", {})["feature"] = {}
    data.setdefault("vote_by_token", {})["feature"] = {}


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
    return {
        "week": week,
        "next_week": next_week,
        "before": before,
        "after": after,
        "deltas": diffs,
        "event": extras.get("event"),
        "decision": extras.get("decision"),
        "decision_notes": extras.get("decision_notes") or [],
        "released_features": extras.get("released_features") or [],
        "late_deliveries": extras.get("late_deliveries") or [],
        "scrum_penalty": extras.get("scrum_penalty") or [],
        "focus": _focus_for_next_week(data, next_week),
        "ts": _now_iso(),
    }


def _apply_scrum_penalty_if_needed(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Проверка scrum-дисциплины при тике недели.

    Если за прошлую неделю PO не сходил на Daily Stand-up — команда теряет
    capacity на следующую неделю (как в реальной жизни: коммуникация
    провисает, появляются дубли работы).
    """
    notes: List[str] = []
    if not data.get("did_daily_this_week"):
        # На неделе НЕ был на Daily — penalty
        m = data.get("metrics") or {}
        m["tech_debt"] = int(_clamp(m.get("tech_debt", 0) + 2, 0, 100))
        data["metrics"] = m
        data["capacity_left"] = max(0, int(data.get("capacity_left", 0)) - 3)
        data["skipped_daily_last_week"] = True
        notes.append({"reason": "no_daily", "tech_debt": 2, "capacity_delta": -3})
    else:
        data["skipped_daily_last_week"] = False
    data["did_daily_this_week"] = False  # сбрасываем флажок на новую неделю
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
    scrum_penalty = _apply_scrum_penalty_if_needed(data)
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
                "released_features": (last_feature or {}).get("released"),
                "scrum_penalty": scrum_penalty,
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
                "released_features": (last_feature or {}).get("released"),
                "scrum_penalty": scrum_penalty,
            },
        )
        _push_recap(data, recap)
        return
    data["current_week"] = int(data["current_week"]) + 1
    data["current_event"] = None
    data["event_resolved"] = True
    # Запоминаем какие фичи поедут «с опозданием» именно сейчас (до старта цикла)
    pending_for_new_cycle = [
        dict(r) for r in (data.get("pending_releases") or [])
        if int(r.get("delivery_cycle", 0)) == int(data.get("cycle_index", 1)) + 1
    ]
    _start_new_cycle_if_needed(data)
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
            "released_features": (last_feature or {}).get("released"),
            "late_deliveries": delivered_now,
            "scrum_penalty": scrum_penalty,
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
    chosen, notes = _resolve_event_decision(data, ev, option_id, locale)

    consequences = ", ".join(notes) if notes else ("без видимых изменений" if locale != "en" else "no visible changes")
    data["consequences_text"] = consequences

    data.setdefault("history", []).append({
        "week": int(data["current_week"]),
        "kind": "event",
        "event": {"id": ev["id"], "title": ev["title"], "type": ev.get("type")},
        "option": {"id": chosen["id"], "title": chosen["title"]},
        "consequences": notes,
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

    # capacity / pick rule guard:
    #   - максимум 2 фичи в цикле
    #   - если есть «большая» (>=40 cap) — она должна быть единственной
    #   - если выбрана «Стабилизация» — она тоже должна быть единственной
    #   - суммарный cap не больше текущего capacity_left
    # Структурные правила проверяем РАНЬШЕ capacity, чтобы пользователь видел
    # «настоящую» ошибку выбора, а не просто «не хватает capacity».
    by_key = {f["key"]: f for f in _FEATURES_RU}
    chosen = [by_key[k] for k in feature_keys if k in by_key]
    if len(chosen) > 2:
        return jsonify({"error": "max_two_features"}), 400
    big_count = sum(1 for f in chosen if int(f.get("capacity", 0)) >= 40)
    if big_count > 1:
        return jsonify({"error": "max_one_big"}), 400
    if big_count == 1 and len(chosen) > 1:
        return jsonify({"error": "big_must_be_alone"}), 400
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
