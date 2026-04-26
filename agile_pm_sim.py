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
    },
    "competitor_channels": {
        "rush": {"title": "Rush channels out", "description": "Big growth, big risk."},
        "research": {"title": "Research the need", "description": "Understand first, build better."},
        "focus": {"title": "Double down on current users", "description": "Don't chase the competitor."},
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
        "unlocked_feature_keys": [],
        "current_event": None,
        "event_resolved": True,
        "votes": {"event": {}, "feature": {}},
        "vote_by_token": {"event": {}, "feature": {}},
        "history": [],
        "metrics_history": [],
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
    if not candidates:
        # fallback — generic user event
        chosen = _EVENTS_RU[0]
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


def _release_feature(data: Dict[str, Any], fkey: str, week: int, locale: str) -> Optional[Dict[str, Any]]:
    f = next((x for x in _FEATURES_RU if x["key"] == fkey), None)
    if not f:
        return None
    cap = int(f.get("capacity", 0))
    if data.get("capacity_left", 0) < cap:
        return None
    data["capacity_left"] = int(data["capacity_left"]) - cap
    notes = _apply_metric_delta(data, f.get("effects", {}))
    # учёт частоты фичи без стабилизации (для team_burnout триггера)
    if fkey != "stabilize":
        data["recent_feature_count"] = int(data.get("recent_feature_count", 0)) + 1
    else:
        data["recent_feature_count"] = max(0, int(data.get("recent_feature_count", 0)) - 1)
    rec = {
        "key": fkey,
        "title": _localize_feature(f, locale)["title"],
        "week": week,
        "cycle": int(data.get("cycle_index", 1)),
        "notes": notes,
    }
    data.setdefault("feature_releases", []).append(rec)
    return rec


def _start_new_cycle_if_needed(data: Dict[str, Any]) -> None:
    """В начале цикла (нечётная неделя) — открываем выбор фичи и пополняем capacity."""
    w = int(data.get("current_week", 0))
    if w == 0 or w > TOTAL_WEEKS:
        return
    if w % CYCLE_LEN == 1:  # неделя 1, 3, 5, ... — старт цикла
        data["capacity_left"] = CAPACITY_PER_CYCLE
        data["cycle_index"] = (w + 1) // CYCLE_LEN  # 1..10
        data["feature_choice_open"] = True
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
    if data.get("current_event") and not data.get("event_resolved", True):
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


def _close_week_and_advance(data: Dict[str, Any], group_id: int, locale: str) -> None:
    """Заканчиваем текущую неделю: пассивные эффекты, статус, переход на следующую."""
    _apply_passive_week(data)
    status, reason = _evaluate_status(data)
    data["status"] = status
    if status == STATUS_DEAD:
        data["death_reason"] = reason
        data["phase"] = PHASE_FINISHED
        _record_metrics_snapshot(data)
        return
    _record_metrics_snapshot(data)
    if int(data["current_week"]) >= TOTAL_WEEKS:
        data["phase"] = PHASE_FINISHED
        return
    data["current_week"] = int(data["current_week"]) + 1
    data["current_event"] = None
    data["event_resolved"] = True
    _start_new_cycle_if_needed(data)
    _ensure_event_for_week(data, group_id, locale)
    _ensure_feature_options(data, group_id, locale)


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

    # capacity guard: 1 большая (>=40) или 2 маленькие или 1 stabilize
    by_key = {f["key"]: f for f in _FEATURES_RU}
    chosen = [by_key[k] for k in feature_keys if k in by_key]
    total_cap = sum(int(f.get("capacity", 0)) for f in chosen)
    if total_cap > int(data.get("capacity_left", 0)):
        return jsonify({"error": "not_enough_capacity"}), 400
    big_count = sum(1 for f in chosen if int(f.get("capacity", 0)) >= 40)
    if big_count > 1 or len(chosen) > 2:
        return jsonify({"error": "max 1 big or 2 small"}), 400

    released_records = []
    for f in chosen:
        rec = _release_feature(data, f["key"], int(data["current_week"]), locale)
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
    ev = next((e for e in _EVENTS_RU if e["id"] == event_id), None)
    if not ev:
        return jsonify({"error": "unknown event"}), 400
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
