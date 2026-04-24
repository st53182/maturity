"""Backend симулятора Scrum-команды.

API под префиксом `/api/agile-training/scrum-sim`.

Основная идея — командный мультиплеер поверх общего артефакта:
одна запись `AgileTrainingScrumSimState` на группу (uniq по group_id),
все действия участников её изменяют, клиенты поллят `/state`.

Контекст — ремонт квартиры под сдачу (не-IT), 10 рабочих дней.
Каждый день: событие → обновление доски → daily → решение → обновление → конец дня.
"""

from __future__ import annotations

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
    AgileTrainingScrumSimState,
    AgileTrainingSession,
)


bp_agile_scrum_sim = Blueprint(
    "agile_scrum_sim", __name__, url_prefix="/api/agile-training/scrum-sim"
)


# --------------------------- constants ---------------------------

AI_CALLS_LIMIT_PER_PARTICIPANT = 10
AI_PROMPT_LIMIT_CHARS = 1800
SPRINT_DAYS = 10
BASE_DAILY_CAPACITY = 6
MAX_ALLOCATION_TASKS = 6

PHASE_LOBBY = "lobby"
PHASE_PLANNING = "planning"
PHASE_REVIEW = "review"
PHASE_RETRO = "retro"
PHASE_SUMMARY = "summary"

ALLOWED_PHASES = {
    PHASE_LOBBY, PHASE_PLANNING, PHASE_REVIEW, PHASE_RETRO, PHASE_SUMMARY,
    *{f"day_{i}" for i in range(1, SPRINT_DAYS + 1)},
}

ALLOWED_ROLES = {"product_owner", "scrum_master", "developer"}

TASK_COL_BACKLOG = "backlog"     # ещё в Sprint backlog, не тронут
TASK_COL_IN_PROGRESS = "in_progress"
TASK_COL_REVIEW = "review"
TASK_COL_DONE = "done"
TASK_COL_PRODUCT = "product"      # не затянут в спринт (Product Backlog)

ALLOWED_TASK_COLUMNS = {
    TASK_COL_PRODUCT, TASK_COL_BACKLOG, TASK_COL_IN_PROGRESS,
    TASK_COL_REVIEW, TASK_COL_DONE,
}

DECISION_KEYS = {
    "continue",        # действовать как запланировали
    "swarm",           # сфокусировать всю команду на одной задаче (+50% к её прогрессу)
    "split_task",      # разбить большую задачу на две меньшие
    "descope",         # убрать задачу из спринта (в Product Backlog)
    "buffer_quality",  # потратить 1 капасити на квалити (снижает вероятность rework)
    "escalate",        # привлечь внешний ресурс: разблокировать заблокированную задачу ценой -1 капасити завтра
}


# --------------------------- content (RU/EN) ---------------------------


def _tasks_ru() -> List[Dict[str, Any]]:
    """Пресет backlog для ремонта квартиры. Ключи стабильные, чтобы ссылаться в событиях.

    Задачи подобраны так, чтобы каждая занимала несколько дней работы команды
    (complexity 3–12 пунктов при 6 капасити/день × 10 дней = 60). Суммарно core
    задач больше мощности — команде придётся договариваться про descope.
    """
    return [
        {"key": "demo_tiles",      "title": "Демонтаж старой плитки",           "desc": "Снять плитку в ванной, коридоре, вывезти мусор",     "complexity": 4,  "core": True,  "deps": []},
        {"key": "strobe_walls",    "title": "Штробление стен под проводку",     "desc": "Подготовить каналы под кабели во всей квартире",     "complexity": 6,  "core": True,  "deps": []},
        {"key": "electrical",      "title": "Прокладка электрики",              "desc": "Кабели, подрозетники, щит, розетки и выключатели",   "complexity": 10, "core": True,  "deps": ["strobe_walls"]},
        {"key": "plumbing_rough",  "title": "Черновая сантехника",              "desc": "Трубы, слив, стяжка пола в мокрых зонах",            "complexity": 6,  "core": True,  "deps": ["demo_tiles"]},
        {"key": "tiles_bathroom",  "title": "Укладка плитки в ванной",          "desc": "Пол и стены в санузле, подрезка, затирка",           "complexity": 12, "core": True,  "deps": ["plumbing_rough", "electrical"]},
        {"key": "drywall",         "title": "Шпаклёвка стен",                   "desc": "Выравнивание стен и потолка под покраску",           "complexity": 9,  "core": True,  "deps": ["strobe_walls"]},
        {"key": "paint",           "title": "Покраска стен",                    "desc": "Финишное покрытие — два слоя",                        "complexity": 7,  "core": True,  "deps": ["drywall"]},
        {"key": "ceiling_stretch", "title": "Натяжные потолки",                 "desc": "Монтаж полотна и светильников",                       "complexity": 5,  "core": True,  "deps": ["electrical"]},
        {"key": "laminate",        "title": "Укладка ламината",                 "desc": "Пол во всех жилых комнатах + плинтус",               "complexity": 8,  "core": True,  "deps": ["drywall", "ceiling_stretch"]},
        {"key": "plumbing_finish", "title": "Чистовая сантехника",              "desc": "Смесители, унитаз, раковина, душевая стойка",        "complexity": 5,  "core": True,  "deps": ["tiles_bathroom"]},
        {"key": "kitchen_install", "title": "Сборка кухни",                     "desc": "Монтаж гарнитура, подключение техники и мойки",      "complexity": 12, "core": True,  "deps": ["electrical", "laminate"]},
        {"key": "cleaning",        "title": "Финальная уборка",                 "desc": "Очистить квартиру от строй-пыли, вывезти отходы",    "complexity": 3,  "core": True,  "deps": ["paint", "laminate", "plumbing_finish"]},
        {"key": "curtains",        "title": "Карнизы и шторы",                  "desc": "Закрыть окна, придать уют, повесить шторы",          "complexity": 2,  "core": False, "deps": ["paint"]},
        {"key": "photo_shoot",     "title": "Фотосессия для объявления",        "desc": "Снять квартиру для публикации объявления",           "complexity": 3,  "core": False, "deps": ["cleaning"]},
        {"key": "smart_home",      "title": "Умный дом (базовый набор)",        "desc": "Умные розетки и датчик протечки — бонус для жильцов", "complexity": 5,  "core": False, "deps": ["electrical"]},
        {"key": "balcony_glazing", "title": "Остекление балкона",               "desc": "Тёплое остекление и отделка балкона",                "complexity": 6,  "core": False, "deps": []},
    ]


def _tasks_en() -> List[Dict[str, Any]]:
    base = _tasks_ru()
    t_en = {
        "demo_tiles":      ("Demolish old tiles",           "Remove tiles in bathroom and hallway, haul away debris"),
        "strobe_walls":    ("Chase walls for wiring",       "Prepare channels for cables across the flat"),
        "electrical":      ("Electrical wiring",            "Cables, outlets, distribution box, sockets and switches"),
        "plumbing_rough":  ("Rough plumbing",               "Pipes, drain and floor screed in wet zones"),
        "tiles_bathroom":  ("Bathroom tiling",              "Floor and walls in the bathroom, cuts, grouting"),
        "drywall":         ("Plastering walls",             "Level walls and ceiling for painting"),
        "paint":           ("Painting walls",               "Final coat — two layers"),
        "ceiling_stretch": ("Stretch ceiling install",      "Mount the canvas and lights"),
        "laminate":        ("Laminate flooring",            "Floor in all rooms + skirting"),
        "plumbing_finish": ("Finish plumbing",              "Faucets, toilet, sink, shower column"),
        "kitchen_install": ("Kitchen installation",         "Assemble the kitchen, hook up appliances and sink"),
        "cleaning":        ("Final cleanup",                "Clean the flat of construction dust and waste"),
        "curtains":        ("Cornices and curtains",        "Close windows, add coziness, hang curtains"),
        "photo_shoot":     ("Photo shoot for the listing",  "Photograph the flat for the listing"),
        "smart_home":      ("Smart home (starter kit)",     "Smart sockets and a leak sensor — a tenant bonus"),
        "balcony_glazing": ("Balcony glazing",              "Warm glazing and balcony finish"),
    }
    out: List[Dict[str, Any]] = []
    for t in base:
        tr = t_en.get(t["key"], (t["title"], t["desc"]))
        out.append({**t, "title": tr[0], "desc": tr[1]})
    return out


def _events_ru() -> List[Dict[str, Any]]:
    """8 событий на 10 дней (дни 3 и 8 — спокойные).

    Формат: {key, day, title, description, effects[]}. Эффекты — см. `_apply_event_effects`.
    """
    return [
        {
            "key": "material_delay",
            "day": 1,
            "title": "Поставка плитки задерживается",
            "description": "Поставщик сообщил: плитка приедет позже обещанного. Задачи, связанные с плиткой, замораживаются до разблокировки.",
            "effects": [
                {"type": "block", "task": "tiles_bathroom", "reason": "Нет плитки на складе"}
            ],
        },
        {
            "key": "weather_rain",
            "day": 2,
            "title": "Ливень, квартира промокла",
            "description": "Дождь зашёл через вентиляцию — пол мокрый, маляры не могут работать. Сегодня мощность команды ниже.",
            "effects": [
                {"type": "capacity_delta", "delta": -2, "day_only": True}
            ],
        },
        {
            "key": "worker_sick",
            "day": 4,
            "title": "Один из мастеров заболел",
            "description": "Команда сегодня меньше. Дневная мощность снижена на 2 пункта.",
            "effects": [
                {"type": "capacity_delta", "delta": -2, "day_only": True}
            ],
        },
        {
            "key": "hidden_defect",
            "day": 5,
            "title": "Скрытый дефект стены",
            "description": "За шпаклёвкой обнаружены трещины. Задачу «Шпаклёвка стен» нужно переделать частично — появился дополнительный объём работы.",
            "effects": [
                {"type": "rework", "task": "drywall", "extra": 3}
            ],
        },
        {
            "key": "supplier_ahead",
            "day": 6,
            "title": "Поставщик нагоняет срыв",
            "description": "Плитка приехала раньше, чем обещали, а бригада на соседнем объекте закончила пораньше и готова помочь. Мощность сегодня выше, и блок по плитке снят.",
            "effects": [
                {"type": "unblock", "task": "tiles_bathroom"},
                {"type": "capacity_delta", "delta": 2, "day_only": True},
            ],
        },
        {
            "key": "inspector_visit",
            "day": 7,
            "title": "Визит инспектора",
            "description": "Инспектор нашёл недочёты в монтажной схеме кухни. Задачу по сборке кухни нужно будет частично переделать — объём работ вырос.",
            "effects": [
                {"type": "rework", "task": "kitchen_install", "extra": 2}
            ],
        },
        {
            "key": "subcontractor_noshow",
            "day": 9,
            "title": "Субподрядчик не вышел",
            "description": "Сантехники-чистовики не приехали — у них форс-мажор на другом объекте. «Чистовая сантехника» заблокирована, пока SM не решит вопрос через эскалацию.",
            "effects": [
                {"type": "block", "task": "plumbing_finish", "reason": "Субподрядчик не вышел"},
            ],
        },
        {
            "key": "urgent_change",
            "day": 10,
            "title": "Срочный запрос от заказчика",
            "description": "Заказчик хочет добавить тёплый пол в ванную. Появилась новая задача — PO должен решить, брать её в спринт или отказаться.",
            "effects": [
                {"type": "add_task", "task": {
                    "key": "warm_floor",
                    "title": "Тёплый пол в ванной",
                    "desc": "Монтаж плёночного тёплого пола и терморегулятора",
                    "complexity": 4, "core": False, "deps": ["electrical"],
                    "origin": "stakeholder"
                }},
            ],
        },
    ]


def _events_en() -> List[Dict[str, Any]]:
    base = _events_ru()
    tr = {
        "material_delay":       ("Tile delivery delayed",            "The supplier said tiles will arrive late. Tile-related tasks are frozen until unblocked."),
        "weather_rain":         ("Heavy rain — flat is wet",         "Rain came through the vent — the floor is wet, painters can't work. Capacity is lower today."),
        "worker_sick":          ("One of the workers is sick",       "The team is smaller today. Daily capacity is reduced by 2 points."),
        "hidden_defect":        ("Hidden wall defect",               "Behind the plaster there are cracks. Plastering has to be partly redone — extra work has appeared."),
        "supplier_ahead":       ("Supplier recovers the delay",      "Tiles arrived earlier than promised and a crew from a neighbouring site is free to help. Capacity is up today, and the tile block is lifted."),
        "inspector_visit":      ("Inspector visit",                  "The inspector found issues in the kitchen installation. The kitchen task has extra work now."),
        "subcontractor_noshow": ("Subcontractor didn't show up",     "The finish-plumbing crew didn't arrive — emergency on another site. \"Finish plumbing\" is blocked until the SM escalates it."),
        "urgent_change":        ("Urgent change request",            "The client wants underfloor heating in the bathroom. A new task appeared — the PO must decide whether to take it on."),
    }
    out: List[Dict[str, Any]] = []
    for e in base:
        t = tr.get(e["key"], (e["title"], e["description"]))
        ev_copy = dict(e)
        ev_copy["title"] = t[0]
        ev_copy["description"] = t[1]
        if e["key"] == "urgent_change":
            ev_copy["effects"] = [
                {"type": "add_task", "task": {
                    "key": "warm_floor",
                    "title": "Underfloor heating in bathroom",
                    "desc": "Install heating film and thermostat",
                    "complexity": 4, "core": False, "deps": ["electrical"],
                    "origin": "stakeholder"
                }},
            ]
        out.append(ev_copy)
    return out


def _decisions_ru() -> List[Dict[str, Any]]:
    """Решения дня. `allowed_roles` определяет, кто из команды вправе его утвердить.

    Если в команде никто не взял ни одну из `allowed_roles`, решение разрешается
    любому участнику (graceful fallback, чтобы команда без выбранных ролей не застряла).
    """
    return [
        {"key": "continue",        "title": "Работаем как договорились",
         "desc": "Не меняем план на сегодня — просто распределим капасити по выбранным задачам.",
         "allowed_roles": ["developer", "scrum_master", "product_owner"]},
        {"key": "swarm",           "title": "Сварм (все на одну задачу)",
         "desc": "Сегодня вся команда фокусируется на одной задаче — её прогресс +50%. Другие задачи сегодня не двигаются.",
         "needs_task": True,
         "allowed_roles": ["scrum_master"]},
        {"key": "split_task",      "title": "Разбить большую задачу",
         "desc": "Большую задачу делим на две меньшие — легче вмешиваться и выкатывать кусками.",
         "needs_task": True,
         "allowed_roles": ["developer"]},
        {"key": "descope",         "title": "Убрать задачу из спринта",
         "desc": "Если не успеваем — возвращаем задачу в Product Backlog. Честнее, чем тянуть до последнего.",
         "needs_task": True,
         "allowed_roles": ["product_owner"]},
        {"key": "buffer_quality",  "title": "Вложиться в качество",
         "desc": "Сегодня тратим 1 капасити на контроль качества. Снижает вероятность «скрытых дефектов» в следующие дни.",
         "allowed_roles": ["developer"]},
        {"key": "escalate",        "title": "Эскалация / внешний ресурс",
         "desc": "Привлекаем снаружи (PO идёт к заказчику / SM пробивает поставщика). Разблокируем одну заблокированную задачу ценой −1 капасити завтра.",
         "needs_task": True,
         "allowed_roles": ["scrum_master"]},
    ]


def _decisions_en() -> List[Dict[str, Any]]:
    tr = {
        "continue":       ("Carry on as planned",       "Don't change today's plan — just distribute capacity across the chosen tasks."),
        "swarm":          ("Swarm (all on one task)",   "The whole team focuses on one task — its progress today gets +50%. Other tasks don't move today."),
        "split_task":     ("Split the big task",        "Break a big task into two smaller ones — easier to intervene and ship in pieces."),
        "descope":        ("Descope from sprint",       "If we can't fit it — move the task back to Product Backlog. Fairer than dragging it until the last day."),
        "buffer_quality": ("Invest in quality",         "Spend 1 capacity on quality control today. Reduces the chance of hidden defects later."),
        "escalate":       ("Escalate / external help",  "Pull in someone external (PO to the stakeholder / SM to the supplier). Unblock one blocked task at the cost of −1 capacity tomorrow."),
    }
    out: List[Dict[str, Any]] = []
    for d in _decisions_ru():
        t = tr.get(d["key"], (d["title"], d["desc"]))
        c = dict(d)
        c["title"] = t[0]
        c["desc"] = t[1]
        out.append(c)
    return out


def _improvements_ru() -> List[Dict[str, Any]]:
    return [
        {"key": "refinement",       "title": "Регулярный refinement",       "desc": "Разобрать задачи заранее — меньше «скрытых дефектов» в спринте."},
        {"key": "small_stories",    "title": "Меньшие задачи",              "desc": "Делим работу на куски по ≤3 пункта — поток быстрее, блокировки короче."},
        {"key": "pairing",          "title": "Парная работа",               "desc": "Работаем парами — легче переживаем болезнь/замены."},
        {"key": "dod_tight",        "title": "Уточнить Definition of Done", "desc": "Жёстче критерии готовности — меньше возвратов из Review."},
        {"key": "supplier_buffer",  "title": "Договориться с поставщиками", "desc": "Буферные материалы на складе — меньше блокировок по поставкам."},
        {"key": "product_goal",     "title": "Общая цель продукта",         "desc": "У команды видна Product Goal — проще решать, что резать."},
    ]


def _improvements_en() -> List[Dict[str, Any]]:
    tr = {
        "refinement":      ("Regular refinement",           "Break tasks down in advance — fewer hidden defects in the sprint."),
        "small_stories":   ("Smaller tasks",                "Split work into chunks of ≤3 points — faster flow, shorter blocks."),
        "pairing":         ("Pair work",                    "Work in pairs — better able to survive sickness / handovers."),
        "dod_tight":       ("Tighten Definition of Done",   "Stricter completion criteria — fewer returns from Review."),
        "supplier_buffer": ("Supplier agreements",          "Buffer stock — fewer blocks from deliveries."),
        "product_goal":    ("Shared Product Goal",          "The team sees the Product Goal — easier to decide what to cut."),
    }
    out: List[Dict[str, Any]] = []
    for i in _improvements_ru():
        t = tr.get(i["key"], (i["title"], i["desc"]))
        c = dict(i)
        c["title"] = t[0]
        c["desc"] = t[1]
        out.append(c)
    return out


CONTENT = {
    "ru": {
        "context": {
            "title": "Ремонт квартиры под сдачу, 10 дней",
            "story": [
                "Вы — команда, которая взялась сделать ремонт в квартире за 10 рабочих дней (2 календарные недели). Квартиру потом будут сдавать в аренду.",
                "В команде несколько мастеров, PO (общается с заказчиком) и SM (убирает препятствия). Задачи зависят друг от друга: нельзя класть плитку, пока не сделана черновая сантехника.",
                "Каждый день может случиться что-то неожиданное — болезни, задержки поставок, запросы заказчика. Вам нужно адаптироваться, не теряя цель спринта.",
                "Распределение ролей важно: только PO может убрать задачу из спринта, только SM — сделать сварм или эскалировать блок, разработчики сами разбивают задачи и решают, заложить ли буфер на качество.",
            ],
            "sprint_goal_hint": "Сформулируйте короткую цель спринта: что заказчик должен увидеть через 2 недели, чтобы сказать «отлично»?",
            "columns": [
                {"key": "product",     "label": "Product Backlog"},
                {"key": "backlog",     "label": "Sprint Backlog"},
                {"key": "in_progress", "label": "В работе"},
                {"key": "review",      "label": "На проверке"},
                {"key": "done",        "label": "Завершено"},
            ],
            "states": [
                {"key": "ok",      "label": "В порядке",     "emoji": "🟡"},
                {"key": "blocked", "label": "Заблокирована", "emoji": "🔴"},
                {"key": "rework",  "label": "Переделка",     "emoji": "⚠️"},
                {"key": "risk",    "label": "Риск качества", "emoji": "⚠️"},
                {"key": "done",    "label": "Готово",        "emoji": "🟢"},
            ],
        },
        "roles": [
            {"key": "product_owner", "title": "Product Owner",
             "desc": "Представляет заказчика. Вправе менять приоритеты, принимать готовую работу, добавлять/снимать задачи."},
            {"key": "scrum_master",  "title": "Scrum Master",
             "desc": "Убирает препятствия, помогает команде договариваться, следит за фреймворком. Может эскалировать блоки."},
            {"key": "developer",     "title": "Разработчик (мастер)",
             "desc": "Делает работу. Может разбивать задачи, предлагать сварм, замечать технический долг."},
        ],
        "tasks": _tasks_ru(),
        "events": _events_ru(),
        "decisions": _decisions_ru(),
        "improvements": _improvements_ru(),
        "labels": {
            "sprint_goal":       "Цель спринта",
            "team":              "Команда",
            "day":               "День",
            "capacity":          "Мощность команды",
            "points":            "пунктов",
            "not_planning":      "Ещё не планировали",
            "start_planning":    "Начать планирование",
            "confirm_planning":  "Зафиксировать план → день 1",
            "open_today_event":  "Показать событие дня",
            "choose_allocation": "Выбрать, что делаем сегодня",
            "choose_decision":   "Решение команды",
            "finish_day":        "Завершить день",
            "open_review":       "Перейти к Sprint Review",
            "open_retro":        "Перейти к ретро",
            "open_summary":      "Финальный экран",
            "reset":             "Сбросить симуляцию",
        },
    },
    "en": {
        "context": {
            "title": "Renovating a flat for rent, 10 days",
            "story": [
                "You are a team taking on the renovation of a flat in 10 working days (two calendar weeks). After that, the flat will be rented out.",
                "The team has several craftspeople, a PO (talks to the client) and an SM (removes obstacles). Tasks depend on each other: you can't tile until rough plumbing is done.",
                "Every day something unexpected can happen — sick days, delivery delays, client requests. You have to adapt without losing the sprint goal.",
                "Roles matter: only the PO can drop a task from the sprint, only the SM can swarm or escalate a block, developers split tasks and decide whether to buffer quality.",
            ],
            "sprint_goal_hint": "Write a short Sprint Goal: what should the client see in 2 weeks to say \"great\"?",
            "columns": [
                {"key": "product",     "label": "Product Backlog"},
                {"key": "backlog",     "label": "Sprint Backlog"},
                {"key": "in_progress", "label": "In progress"},
                {"key": "review",      "label": "In review"},
                {"key": "done",        "label": "Done"},
            ],
            "states": [
                {"key": "ok",      "label": "OK",              "emoji": "🟡"},
                {"key": "blocked", "label": "Blocked",         "emoji": "🔴"},
                {"key": "rework",  "label": "Rework",          "emoji": "⚠️"},
                {"key": "risk",    "label": "Quality risk",    "emoji": "⚠️"},
                {"key": "done",    "label": "Done",            "emoji": "🟢"},
            ],
        },
        "roles": [
            {"key": "product_owner", "title": "Product Owner",
             "desc": "Represents the client. Can change priorities, accept finished work, add/remove tasks."},
            {"key": "scrum_master",  "title": "Scrum Master",
             "desc": "Removes obstacles, helps the team agree, watches over the framework. Can escalate blocks."},
            {"key": "developer",     "title": "Developer (craftsperson)",
             "desc": "Does the work. Can split tasks, suggest swarms, flag technical debt."},
        ],
        "tasks": _tasks_en(),
        "events": _events_en(),
        "decisions": _decisions_en(),
        "improvements": _improvements_en(),
        "labels": {
            "sprint_goal":       "Sprint Goal",
            "team":              "Team",
            "day":               "Day",
            "capacity":          "Team capacity",
            "points":            "points",
            "not_planning":      "Not planned yet",
            "start_planning":    "Start planning",
            "confirm_planning":  "Lock plan → day 1",
            "open_today_event":  "Reveal today's event",
            "choose_allocation": "Choose what we do today",
            "choose_decision":   "Team decision",
            "finish_day":        "Finish the day",
            "open_review":       "Go to Sprint Review",
            "open_retro":        "Go to Retrospective",
            "open_summary":      "Final screen",
            "reset":             "Reset the simulation",
        },
    },
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


def _clamp_text(value, limit: int = 1200) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    return s[:limit]


def _initial_state(locale: str = "ru") -> Dict[str, Any]:
    tasks = _tasks_ru() if locale != "en" else _tasks_en()
    task_map = {}
    for t in tasks:
        task_map[t["key"]] = {
            "key": t["key"],
            "title": t["title"],
            "desc": t["desc"],
            "complexity": int(t["complexity"]),
            "core": bool(t.get("core", True)),
            "deps": list(t.get("deps", [])),
            "column": TASK_COL_PRODUCT,
            "progress": 0,
            "extra": 0,
            "state": "ok",
            "state_reason": "",
            "origin": t.get("origin", "initial"),
        }
    return {
        "version": 1,
        "phase": PHASE_LOBBY,
        "current_day": 0,
        "sprint_goal": "",
        "team_capacity_per_day": BASE_DAILY_CAPACITY,
        "next_day_capacity_mod": 0,   # модификатор на следующий день (например, от escalate)
        "tasks": task_map,
        "roles": {},                  # token -> role
        "participants": {},           # token -> {name, role, joined_at, last_seen}
        "days": [],                   # история: [{day, event, allocation, decision, notes, snapshot}]
        "pending_day": {              # текущий «открытый» день
            "day": 0,
            "event_applied": False,
            "allocation": {},         # task_key -> pts
            "decision": None,         # {"key": ..., "task": ...}
            "swarm_task": None,
            "buffer_used": False,
        },
        "retro_picks": [],
        "review_metrics": None,
        "ai_calls": {},               # token -> int
        "notes": {},                  # freeform per-phase notes
        "paused": False,
        "updated_at": _now_iso(),
    }


def _get_or_init_state(group: AgileTrainingGroup) -> Tuple[AgileTrainingScrumSimState, Dict[str, Any]]:
    row = (
        AgileTrainingScrumSimState.query
        .filter_by(group_id=group.id)
        .first()
    )
    if row is None:
        data = _initial_state("ru")
        row = AgileTrainingScrumSimState(
            group_id=group.id,
            phase=data["phase"],
            current_day=0,
            version=1,
            paused=False,
            data_json=json.dumps(data, ensure_ascii=False),
        )
        db.session.add(row)
        db.session.commit()
        return row, data
    data = _safe_json_load(row.data_json)
    if not data:
        data = _initial_state("ru")
    return row, data


def _save_state(row: AgileTrainingScrumSimState, data: Dict[str, Any]) -> None:
    data["version"] = int(data.get("version", 1)) + 1
    data["updated_at"] = _now_iso()
    row.version = data["version"]
    row.phase = data.get("phase") or PHASE_LOBBY
    row.current_day = int(data.get("current_day", 0))
    row.paused = bool(data.get("paused", False))
    row.data_json = json.dumps(data, ensure_ascii=False)
    db.session.commit()


def _touch_participant(data: Dict[str, Any], p: AgileTrainingParticipant) -> None:
    token = p.participant_token
    plist = data.setdefault("participants", {})
    entry = plist.get(token) or {}
    entry["name"] = p.display_name or entry.get("name") or "…"
    entry["role"] = data.get("roles", {}).get(token) or entry.get("role")
    entry["last_seen"] = _now_iso()
    entry.setdefault("joined_at", _now_iso())
    plist[token] = entry


# --------------------------- game engine ---------------------------


def _tasks_deps_done(tasks: Dict[str, Dict[str, Any]], t: Dict[str, Any]) -> bool:
    for dep in t.get("deps", []) or []:
        dep_task = tasks.get(dep)
        if not dep_task:
            continue
        if dep_task.get("column") != TASK_COL_DONE:
            return False
    return True


def _is_workable(tasks: Dict[str, Dict[str, Any]], t: Dict[str, Any]) -> bool:
    """Можно ли сегодня выделить капасити на эту задачу."""
    if t.get("column") in (TASK_COL_DONE, TASK_COL_REVIEW, TASK_COL_PRODUCT):
        return False
    if t.get("state") == "blocked":
        return False
    if not _tasks_deps_done(tasks, t):
        return False
    return True


def _recompute_blocks_from_deps(tasks: Dict[str, Dict[str, Any]]) -> None:
    """Если блок снят и deps готовы — задача становится ok. Иначе ok-задачи не трогаем."""
    pass  # блок снимается/ставится событиями явно


def _apply_event_effects(data: Dict[str, Any], event: Dict[str, Any]) -> List[str]:
    tasks = data["tasks"]
    notes: List[str] = []
    for eff in event.get("effects", []) or []:
        etype = eff.get("type")
        if etype == "block":
            key = eff.get("task")
            t = tasks.get(key)
            if t and t.get("column") not in (TASK_COL_DONE,):
                t["state"] = "blocked"
                t["state_reason"] = eff.get("reason") or ""
                notes.append(f"Заблокирована: {t['title']}")
        elif etype == "unblock":
            key = eff.get("task")
            t = tasks.get(key)
            if t and t.get("state") == "blocked":
                t["state"] = "ok"
                t["state_reason"] = ""
                notes.append(f"Разблокирована: {t['title']}")
        elif etype == "rework":
            key = eff.get("task")
            extra = int(eff.get("extra", 2))
            t = tasks.get(key)
            if t:
                t["extra"] = int(t.get("extra", 0)) + extra
                t["state"] = "rework"
                t["state_reason"] = "Требуется переделать часть работы"
                if t.get("column") in (TASK_COL_REVIEW, TASK_COL_DONE):
                    t["column"] = TASK_COL_IN_PROGRESS
                    t.pop("_new_in_review", None)
                notes.append(f"Переделка: {t['title']} +{extra}п.")
        elif etype == "capacity_delta":
            delta = int(eff.get("delta", 0))
            day_only = bool(eff.get("day_only", True))
            if day_only:
                data.setdefault("pending_day", {})["capacity_mod_today"] = delta
            else:
                data["team_capacity_per_day"] = max(1, data.get("team_capacity_per_day", BASE_DAILY_CAPACITY) + delta)
            notes.append(f"Мощность {'сегодня' if day_only else 'спринта'}: {delta:+d}")
        elif etype == "add_task":
            nt = eff.get("task") or {}
            key = nt.get("key")
            if key and key not in tasks:
                tasks[key] = {
                    "key": key,
                    "title": nt.get("title", key),
                    "desc": nt.get("desc", ""),
                    "complexity": int(nt.get("complexity", 3)),
                    "core": bool(nt.get("core", False)),
                    "deps": list(nt.get("deps", [])),
                    "column": TASK_COL_BACKLOG,
                    "progress": 0,
                    "extra": 0,
                    "state": "risk",
                    "state_reason": "Добавлена заказчиком в процессе спринта",
                    "origin": nt.get("origin", "stakeholder"),
                }
                notes.append(f"Новая задача: {tasks[key]['title']}")
    return notes


def _effective_capacity_today(data: Dict[str, Any]) -> int:
    base = int(data.get("team_capacity_per_day", BASE_DAILY_CAPACITY))
    mod = int(data.get("pending_day", {}).get("capacity_mod_today", 0))
    carry = int(data.get("next_day_capacity_mod", 0))
    return max(1, base + mod + carry)


def _snapshot_board(data: Dict[str, Any]) -> Dict[str, Any]:
    """Короткий срез состояния доски — для истории дней."""
    cols: Dict[str, List[str]] = {c: [] for c in [
        TASK_COL_PRODUCT, TASK_COL_BACKLOG, TASK_COL_IN_PROGRESS, TASK_COL_REVIEW, TASK_COL_DONE
    ]}
    for k, t in data.get("tasks", {}).items():
        cols.setdefault(t.get("column", TASK_COL_BACKLOG), []).append(k)
    return {
        "columns": cols,
        "sprint_goal": data.get("sprint_goal", ""),
        "capacity": data.get("team_capacity_per_day", BASE_DAILY_CAPACITY),
    }


def _compute_review(data: Dict[str, Any]) -> Dict[str, Any]:
    tasks = data.get("tasks", {})
    total_core = sum(1 for t in tasks.values() if t.get("core"))
    done_core = sum(1 for t in tasks.values() if t.get("core") and t.get("column") == TASK_COL_DONE)
    total_sprint = sum(
        1 for t in tasks.values()
        if t.get("column") in (TASK_COL_BACKLOG, TASK_COL_IN_PROGRESS, TASK_COL_REVIEW, TASK_COL_DONE)
    )
    done_any = sum(1 for t in tasks.values() if t.get("column") == TASK_COL_DONE)
    blocked = sum(1 for t in tasks.values() if t.get("state") == "blocked" and t.get("column") != TASK_COL_DONE)
    rework = sum(
        1 for t in tasks.values()
        if t.get("state") == "rework" and t.get("column") != TASK_COL_DONE
    )

    ratio = (done_core / max(1, total_core))
    if ratio >= 0.85:
        outcome = "great"
    elif ratio >= 0.6:
        outcome = "ok"
    elif ratio >= 0.3:
        outcome = "rough"
    else:
        outcome = "fail"

    return {
        "done_total":    done_any,
        "in_sprint":     total_sprint,
        "done_core":     done_core,
        "total_core":    total_core,
        "blocked":       blocked,
        "rework":        rework,
        "core_ratio":    round(ratio, 2),
        "outcome":       outcome,
    }


def _task_need(t: Dict[str, Any]) -> int:
    """Сколько всего пунктов нужно для задачи (complexity + extra от reworks)."""
    return max(0, int(t.get("complexity", 0)) + int(t.get("extra", 0)))


def _add_progress_capped(t: Dict[str, Any], delta: int) -> int:
    """Добавить прогресс задаче с кэпом по `need`. Возвращает фактически добавленный дельта.

    Это решает визуальный баг «need = −2»: прогресс никогда не превышает `need`.
    Лишние пункты капасити считаются потерянными (переходят в notes вызывающим кодом).
    """
    if delta <= 0:
        return 0
    need = _task_need(t)
    cur = int(t.get("progress", 0))
    nxt = min(need, cur + int(delta))
    t["progress"] = nxt
    return max(0, nxt - cur)


def _apply_allocation_and_decision(data: Dict[str, Any]) -> List[str]:
    """Применить сегодняшние allocation + decision к задачам. Вернуть заметки.

    Важные инварианты:
      * прогресс задачи никогда не превышает `need` (complexity + extra);
      * задача, переехавшая в Review сегодня, помечается `_new_in_review=True`
        и сдвигается в Done только на СЛЕДУЮЩЕМ вызове (т.е. через 1 день);
      * при swarm допускается исчерпание капасити + 50% бонус, но также кэпируется
        по потребности задачи.
    """
    notes: List[str] = []
    tasks = data["tasks"]
    pending = data.get("pending_day", {}) or {}
    allocation: Dict[str, int] = pending.get("allocation", {}) or {}
    decision: Dict[str, Any] = pending.get("decision") or {"key": "continue"}
    cap_today = _effective_capacity_today(data)

    used = 0
    for k, pts in list(allocation.items()):
        t = tasks.get(k)
        if not t:
            allocation.pop(k, None)
            continue
        try:
            p = max(0, int(pts))
        except Exception:
            p = 0
        if not _is_workable(tasks, t):
            p = 0
        allocation[k] = p
        used += p

    if used > cap_today:
        factor = cap_today / max(1, used)
        for k in list(allocation.keys()):
            allocation[k] = int(allocation[k] * factor)

    dkey = decision.get("key")
    if dkey == "swarm":
        sk = decision.get("task") or pending.get("swarm_task")
        t = tasks.get(sk) if sk else None
        if t and _is_workable(tasks, t):
            swarm_delta = int(cap_today * 1.5)
            actually = _add_progress_capped(t, swarm_delta)
            allocation = {sk: min(cap_today, actually)}
            if t.get("column") == TASK_COL_BACKLOG:
                t["column"] = TASK_COL_IN_PROGRESS
            notes.append(f"Сварм: {t['title']} (+{actually}п.)")
            used = cap_today
        else:
            dkey = "continue"
    elif dkey == "split_task":
        sk = decision.get("task")
        t = tasks.get(sk) if sk else None
        if t and t.get("column") in (TASK_COL_BACKLOG, TASK_COL_IN_PROGRESS) and int(t.get("complexity", 0)) >= 4:
            old_complex = int(t["complexity"])
            half1 = old_complex // 2
            half2 = old_complex - half1
            t["complexity"] = half1
            new_key = sk + "__b"
            suffix = 2
            while new_key in tasks:
                new_key = f"{sk}__b{suffix}"
                suffix += 1
            tasks[new_key] = {
                "key": new_key,
                "title": t["title"] + " (часть 2)",
                "desc": t.get("desc", "") + " — вторая половина после разбиения",
                "complexity": half2,
                "core": bool(t.get("core", True)),
                "deps": list(t.get("deps", [])),
                "column": TASK_COL_BACKLOG,
                "progress": 0, "extra": 0, "state": "ok", "state_reason": "",
                "origin": "split",
            }
            notes.append(f"Разбили: {t['title']} → 2×")
    elif dkey == "descope":
        sk = decision.get("task")
        t = tasks.get(sk) if sk else None
        if t and t.get("column") != TASK_COL_DONE:
            t["column"] = TASK_COL_PRODUCT
            t["progress"] = 0
            t["state"] = "ok"
            t["state_reason"] = "Убрана из спринта решением команды"
            notes.append(f"Descope: {t['title']}")
    elif dkey == "buffer_quality":
        used = min(cap_today, used + 1)
        data["quality_buffer"] = int(data.get("quality_buffer", 0)) + 1
        for t in tasks.values():
            if t.get("state") == "risk":
                t["state"] = "ok"
                t["state_reason"] = ""
        notes.append("Вложились в качество (+1 буфер)")
    elif dkey == "escalate":
        sk = decision.get("task")
        t = tasks.get(sk) if sk else None
        if t and t.get("state") == "blocked":
            t["state"] = "ok"
            t["state_reason"] = ""
            data["next_day_capacity_mod"] = int(data.get("next_day_capacity_mod", 0)) - 1
            notes.append(f"Эскалация: разблокировали {t['title']} (−1 капасити завтра)")

    if dkey != "swarm":
        for k, pts in allocation.items():
            t = tasks.get(k)
            if not t or pts <= 0:
                continue
            if not _is_workable(tasks, t):
                continue
            _add_progress_capped(t, int(pts))
            if t.get("column") == TASK_COL_BACKLOG:
                t["column"] = TASK_COL_IN_PROGRESS

    for t in tasks.values():
        if t.get("column") == TASK_COL_REVIEW and t.get("_new_in_review"):
            t["column"] = TASK_COL_DONE
            t["state"] = "done"
            t.pop("_new_in_review", None)

    for t in tasks.values():
        if t.get("column") == TASK_COL_IN_PROGRESS and t.get("state") != "blocked":
            if int(t.get("progress", 0)) >= _task_need(t):
                t["column"] = TASK_COL_REVIEW
                t["state"] = "ok"
                t["_new_in_review"] = True

    return notes


# --------------------------- serialization ---------------------------


def _serialize_state(row: AgileTrainingScrumSimState, data: Dict[str, Any], locale: str, participant_token: Optional[str]) -> Dict[str, Any]:
    return {
        "version": int(data.get("version", 0)),
        "phase": data.get("phase", PHASE_LOBBY),
        "current_day": int(data.get("current_day", 0)),
        "sprint_days": SPRINT_DAYS,
        "paused": bool(data.get("paused", False)),
        "sprint_goal": data.get("sprint_goal", ""),
        "team_capacity_per_day": int(data.get("team_capacity_per_day", BASE_DAILY_CAPACITY)),
        "next_day_capacity_mod": int(data.get("next_day_capacity_mod", 0)),
        "capacity_today": _effective_capacity_today(data),
        "tasks": list(data.get("tasks", {}).values()),
        "participants": data.get("participants", {}),
        "roles": data.get("roles", {}),
        "days": data.get("days", []),
        "pending_day": data.get("pending_day", {}),
        "priority_order": data.get("priority_order", []),
        "retro_picks": data.get("retro_picks", []),
        "review_metrics": data.get("review_metrics"),
        "notes": data.get("notes", {}),
        "my": {
            "token": participant_token or None,
            "role": data.get("roles", {}).get(participant_token or ""),
            "ai_calls": int(data.get("ai_calls", {}).get(participant_token or "", 0)),
            "ai_calls_limit": AI_CALLS_LIMIT_PER_PARTICIPANT,
        },
        "updated_at": data.get("updated_at"),
    }


# --------------------------- endpoints: public content ---------------------------


@bp_agile_scrum_sim.get("/content")
def content_public():
    locale = _resolve_locale(request.args.get("locale"), None)
    return jsonify({"locale": locale, **CONTENT.get(locale, CONTENT["ru"])})


# --------------------------- endpoints: participant-facing ---------------------------


@bp_agile_scrum_sim.get("/g/<slug>/state")
def participant_state(slug: str):
    g, sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404

    locale = _resolve_locale(request.args.get("locale"), sess)
    token = (request.args.get("participant_token") or "").strip() or None

    row, data = _get_or_init_state(g)
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
            "exercise_key": sess.exercise_key if sess else "scrum_simulator",
            "locale": sess.locale if sess else "ru",
        },
        "effective_locale": locale,
        "content": CONTENT.get(locale, CONTENT["ru"]),
        "state": _serialize_state(row, data, locale, token),
    })


@bp_agile_scrum_sim.post("/g/<slug>/join")
def participant_join(slug: str):
    """Выбрать/обновить свою роль в команде."""
    g, _ = _group_and_session(slug)
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
        data.setdefault("roles", {})[token] = role
    _touch_participant(data, p)
    _save_state(row, data)
    return jsonify({"ok": True, "role": data["roles"].get(token)})


@bp_agile_scrum_sim.post("/g/<slug>/planning")
def participant_planning(slug: str):
    """Действия планирования: pull/push задач между Product Backlog и Sprint Backlog,
    установка Sprint Goal."""
    g, _ = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    if not token:
        return jsonify({"error": "participant_token required"}), 400
    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404

    row, data = _get_or_init_state(g)
    if data.get("phase") not in (PHASE_LOBBY, PHASE_PLANNING):
        return jsonify({"error": "planning closed"}), 400

    data["phase"] = PHASE_PLANNING

    if "sprint_goal" in body:
        data["sprint_goal"] = _clamp_text(body.get("sprint_goal"), 240) or ""

    action = (body.get("action") or "").strip()
    task_key = (body.get("task_key") or "").strip()
    if action == "pull" and task_key:
        t = data.get("tasks", {}).get(task_key)
        if t and t.get("column") == TASK_COL_PRODUCT:
            t["column"] = TASK_COL_BACKLOG
    elif action == "push" and task_key:
        t = data.get("tasks", {}).get(task_key)
        if t and t.get("column") == TASK_COL_BACKLOG:
            t["column"] = TASK_COL_PRODUCT
    elif action == "reset":
        for t in data.get("tasks", {}).values():
            t["column"] = TASK_COL_PRODUCT

    _touch_participant(data, p)
    _save_state(row, data)
    return jsonify({"ok": True, "state": _serialize_state(row, data, "ru", token)})


@bp_agile_scrum_sim.post("/g/<slug>/planning/confirm")
def planning_confirm(slug: str):
    g, _ = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    p = _require_participant(g, token) if token else None

    row, data = _get_or_init_state(g)
    if data.get("phase") not in (PHASE_PLANNING, PHASE_LOBBY):
        return jsonify({"error": "planning already closed"}), 400

    sprint_tasks = [t for t in data.get("tasks", {}).values() if t.get("column") == TASK_COL_BACKLOG]
    if not sprint_tasks:
        return jsonify({"error": "pull at least one task into Sprint Backlog"}), 400

    data["phase"] = "day_1"
    data["current_day"] = 1
    data["pending_day"] = {
        "day": 1, "event_applied": False, "allocation": {},
        "decision": None, "swarm_task": None, "buffer_used": False,
    }
    if p:
        _touch_participant(data, p)
    _save_state(row, data)
    return jsonify({"ok": True, "state": _serialize_state(row, data, "ru", token)})


@bp_agile_scrum_sim.post("/g/<slug>/day/advance")
def day_reveal_event(slug: str):
    """Открыть сегодняшнее событие: применить эффекты к задачам."""
    g, _ = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    p = _require_participant(g, token) if token else None

    row, data = _get_or_init_state(g)
    phase = data.get("phase", "")
    if not phase.startswith("day_"):
        return jsonify({"error": "not in day phase"}), 400

    pending = data.setdefault("pending_day", {})
    if pending.get("event_applied"):
        return jsonify({"ok": True, "state": _serialize_state(row, data, "ru", token)})

    day = int(data.get("current_day", 1))
    events = _events_ru()
    today_event = next((e for e in events if int(e.get("day", 0)) == day), None)

    notes: List[str] = []
    if today_event:
        notes = _apply_event_effects(data, today_event)
        pending["event"] = {
            "key": today_event.get("key"),
            "title": today_event.get("title"),
            "description": today_event.get("description"),
            "notes": notes,
        }
    else:
        pending["event"] = {"key": "no_event", "title": "Обычный день", "description": "Сегодня без сюрпризов — работаем как запланировали.", "notes": []}
    pending["event_applied"] = True
    pending.setdefault("allocation", {})
    if p:
        _touch_participant(data, p)
    _save_state(row, data)
    return jsonify({"ok": True, "state": _serialize_state(row, data, "ru", token)})


@bp_agile_scrum_sim.post("/g/<slug>/day/allocate")
def day_allocate(slug: str):
    g, _ = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    p = _require_participant(g, token) if token else None

    row, data = _get_or_init_state(g)
    phase = data.get("phase", "")
    if not phase.startswith("day_"):
        return jsonify({"error": "not in day phase"}), 400
    pending = data.setdefault("pending_day", {})
    if not pending.get("event_applied"):
        return jsonify({"error": "reveal event first"}), 400

    allocation_raw = body.get("allocation") or {}
    if not isinstance(allocation_raw, dict):
        return jsonify({"error": "allocation must be object {task_key: pts}"}), 400
    cap = _effective_capacity_today(data)
    clean: Dict[str, int] = {}
    total = 0
    tasks = data.get("tasks", {})
    for k, v in list(allocation_raw.items())[:MAX_ALLOCATION_TASKS]:
        t = tasks.get(k)
        if not t:
            continue
        try:
            p_ = max(0, min(cap, int(v)))
        except Exception:
            p_ = 0
        if not _is_workable(tasks, t):
            p_ = 0
        need_left = max(0, _task_need(t) - int(t.get("progress", 0)))
        if p_ > need_left:
            p_ = need_left
        if p_ > 0:
            clean[k] = p_
            total += p_
    if total > cap:
        factor = cap / max(1, total)
        for k in list(clean.keys()):
            clean[k] = int(clean[k] * factor)
    pending["allocation"] = clean

    priority_raw = body.get("priority_order")
    if isinstance(priority_raw, list):
        cleaned_order = [k for k in priority_raw if isinstance(k, str) and k in tasks]
        seen = set()
        dedup: List[str] = []
        for k in cleaned_order:
            if k in seen:
                continue
            seen.add(k)
            dedup.append(k)
        data["priority_order"] = dedup

    if p:
        _touch_participant(data, p)
    _save_state(row, data)
    return jsonify({"ok": True, "state": _serialize_state(row, data, "ru", token)})


def _decision_allowed_roles(dkey: str) -> List[str]:
    """Достать allowed_roles из определения решения (на русском, т.к. ключи общие)."""
    for d in _decisions_ru():
        if d.get("key") == dkey:
            return list(d.get("allowed_roles") or [])
    return []


def _check_role_for_decision(data: Dict[str, Any], token: str, dkey: str) -> Tuple[bool, List[str]]:
    """Проверить, может ли токен утвердить решение `dkey`.

    Возвращает (ok, required_roles). Правила:
      * если у решения нет `allowed_roles` или оно не указано — ok=True
      * если у участника роль входит в allowed_roles — ok=True
      * если НИКТО в команде не взял ни одну из allowed_roles — ok=True (fallback)
      * иначе — ok=False и список required_roles
    """
    required = _decision_allowed_roles(dkey)
    if not required:
        return True, []
    my_role = (data.get("roles", {}) or {}).get(token or "")
    if my_role and my_role in required:
        return True, required
    team_roles = set((data.get("roles", {}) or {}).values())
    if not (team_roles & set(required)):
        return True, required
    return False, required


@bp_agile_scrum_sim.post("/g/<slug>/day/decision")
def day_decision(slug: str):
    g, _ = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    p = _require_participant(g, token) if token else None

    row, data = _get_or_init_state(g)
    phase = data.get("phase", "")
    if not phase.startswith("day_"):
        return jsonify({"error": "not in day phase"}), 400

    dkey = (body.get("decision_key") or "").strip().lower()
    if dkey and dkey not in DECISION_KEYS:
        return jsonify({"error": "invalid decision_key"}), 400
    task_key = (body.get("task_key") or "").strip() or None

    effective_key = dkey or "continue"
    ok, required = _check_role_for_decision(data, token, effective_key)
    if not ok:
        return jsonify({
            "error": "role_required",
            "message": "decision_requires_role",
            "required_roles": required,
        }), 403

    pending = data.setdefault("pending_day", {})
    pending["decision"] = {"key": effective_key, "task": task_key}
    if p:
        _touch_participant(data, p)
    _save_state(row, data)
    return jsonify({"ok": True, "state": _serialize_state(row, data, "ru", token)})


@bp_agile_scrum_sim.post("/g/<slug>/day/end")
def day_end(slug: str):
    g, _ = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    p = _require_participant(g, token) if token else None

    row, data = _get_or_init_state(g)
    phase = data.get("phase", "")
    if not phase.startswith("day_"):
        return jsonify({"error": "not in day phase"}), 400

    pending = data.setdefault("pending_day", {})
    if not pending.get("event_applied"):
        return jsonify({"error": "reveal event first"}), 400

    apply_notes = _apply_allocation_and_decision(data)

    day = int(data.get("current_day", 1))
    history_entry = {
        "day": day,
        "event": pending.get("event"),
        "allocation": pending.get("allocation", {}),
        "decision": pending.get("decision") or {"key": "continue"},
        "capacity_today": _effective_capacity_today(data),
        "apply_notes": apply_notes,
        "snapshot": _snapshot_board(data),
        "finished_at": _now_iso(),
    }
    data.setdefault("days", []).append(history_entry)

    carry = data.get("next_day_capacity_mod", 0)
    data["next_day_capacity_mod"] = 0

    if day >= SPRINT_DAYS:
        data["phase"] = PHASE_REVIEW
        data["review_metrics"] = _compute_review(data)
    else:
        next_day = day + 1
        data["current_day"] = next_day
        data["phase"] = f"day_{next_day}"
        data["pending_day"] = {
            "day": next_day, "event_applied": False, "allocation": {},
            "decision": None, "swarm_task": None, "buffer_used": False,
            "capacity_mod_today": carry,
        }

    if p:
        _touch_participant(data, p)
    _save_state(row, data)
    return jsonify({"ok": True, "state": _serialize_state(row, data, "ru", token)})


@bp_agile_scrum_sim.post("/g/<slug>/review/confirm")
def review_confirm(slug: str):
    g, _ = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    p = _require_participant(g, token) if token else None

    row, data = _get_or_init_state(g)
    if data.get("phase") != PHASE_REVIEW:
        return jsonify({"error": "not in review"}), 400
    data["phase"] = PHASE_RETRO
    if p:
        _touch_participant(data, p)
    _save_state(row, data)
    return jsonify({"ok": True, "state": _serialize_state(row, data, "ru", token)})


@bp_agile_scrum_sim.post("/g/<slug>/retro")
def retro_update(slug: str):
    g, _ = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    p = _require_participant(g, token) if token else None

    row, data = _get_or_init_state(g)
    if data.get("phase") not in (PHASE_RETRO, PHASE_REVIEW):
        return jsonify({"error": "not in retro"}), 400

    data["phase"] = PHASE_RETRO

    picks = body.get("picks") or []
    if isinstance(picks, list):
        valid = {i["key"] for i in _improvements_ru()}
        picks = [k for k in picks if isinstance(k, str) and k in valid][:4]
        data["retro_picks"] = picks

    if body.get("confirm"):
        data["phase"] = PHASE_SUMMARY

    if p:
        _touch_participant(data, p)
    _save_state(row, data)
    return jsonify({"ok": True, "state": _serialize_state(row, data, "ru", token)})


@bp_agile_scrum_sim.post("/g/<slug>/reset")
def participant_reset(slug: str):
    g, _ = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    p = _require_participant(g, token) if token else None

    row = (
        AgileTrainingScrumSimState.query
        .filter_by(group_id=g.id)
        .first()
    )
    fresh = _initial_state("ru")
    if row is None:
        row = AgileTrainingScrumSimState(
            group_id=g.id, phase=fresh["phase"], current_day=0,
            version=1, paused=False, data_json=json.dumps(fresh, ensure_ascii=False),
        )
        db.session.add(row)
    else:
        old_participants = {}
        old_roles = {}
        try:
            prev = _safe_json_load(row.data_json)
            old_participants = prev.get("participants", {}) or {}
            old_roles = prev.get("roles", {}) or {}
        except Exception:
            pass
        fresh["participants"] = old_participants
        fresh["roles"] = old_roles
        row.data_json = json.dumps(fresh, ensure_ascii=False)
        row.phase = fresh["phase"]
        row.current_day = 0
        row.version = fresh["version"]
        row.paused = False
    if p:
        _touch_participant(fresh, p)
    db.session.commit()
    return jsonify({"ok": True, "state": _serialize_state(row, fresh, "ru", token)})


# --------------------------- AI helper ---------------------------


def _scripted_ai_reply(mode: str, user_input: str, phase: str) -> str:
    hints = {
        "planning": "Подумайте: что именно в пятницу должен увидеть заказчик? Задачи без видимого результата часто можно отрезать.",
        "daily":    "В daily обсуждайте НЕ статусы, а препятствия. Что нас тормозит сегодня? Кто может помочь?",
        "decision": "Классический трейд-офф: сделать быстро vs. сделать правильно. Посчитайте, что дороже при проседании в качестве.",
        "review":   "На review не только показывайте что сделано, но и честно говорите, что не вошло и почему.",
        "retro":    "Хорошая ретро-цель — маленькая и измеримая: «в следующем спринте проводить refinement во вторник 30 минут».",
    }
    return hints.get(mode, hints.get(phase, "Подумайте, что сейчас является самым важным ограничением команды — и что вы можете сделать с ним сегодня."))


@bp_agile_scrum_sim.post("/g/<slug>/ai-assist")
def ai_assist(slug: str):
    g, sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    if not token:
        return jsonify({"error": "participant_token required"}), 400
    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404

    mode = (body.get("mode") or "generic").strip().lower()
    user_input = _clamp_text(body.get("user_input"), AI_PROMPT_LIMIT_CHARS) or ""

    row, data = _get_or_init_state(g)
    calls = data.setdefault("ai_calls", {})
    n = int(calls.get(token, 0))
    if n >= AI_CALLS_LIMIT_PER_PARTICIPANT:
        return jsonify({
            "error": "limit",
            "message": f"Лимит AI-помощи исчерпан ({AI_CALLS_LIMIT_PER_PARTICIPANT}/тренинг)"
        }), 429

    phase = data.get("phase", PHASE_LOBBY)
    reply = _scripted_ai_reply(mode, user_input, phase)

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            import requests as _rq
            ctx = f"Фаза: {phase}. Режим: {mode}. Команда играет в симулятор Scrum (ремонт квартиры за 5 дней)."
            sys = (
                "Ты — продвинутый Scrum-коуч. Даёшь короткие, практичные подсказки. "
                "Не давай готовых ответов — задавай 1–2 уточняющих вопроса и предлагай вариант."
            )
            r = _rq.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    "temperature": 0.4,
                    "max_tokens": 350,
                    "messages": [
                        {"role": "system", "content": sys},
                        {"role": "user", "content": f"{ctx}\n\nВопрос команды: {user_input or '(нет текста)'}"},
                    ],
                },
                timeout=20,
            )
            if r.ok:
                js = r.json() or {}
                maybe = ((js.get("choices") or [{}])[0].get("message") or {}).get("content")
                if maybe and isinstance(maybe, str) and maybe.strip():
                    reply = maybe.strip()
        except Exception:
            pass

    calls[token] = n + 1
    _touch_participant(data, p)
    _save_state(row, data)

    return jsonify({
        "ok": True,
        "reply": reply,
        "calls": calls[token],
        "limit": AI_CALLS_LIMIT_PER_PARTICIPANT,
    })


# --------------------------- facilitator endpoints ---------------------------


@bp_agile_scrum_sim.get("/groups/<int:group_id>/state")
@jwt_required()
def facilitator_group_state(group_id: int):
    g = AgileTrainingGroup.query.get(group_id)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    sess = AgileTrainingSession.query.get(g.session_id)
    if not sess or sess.owner_user_id != _uid():
        return jsonify({"error": "Forbidden"}), 403
    row, data = _get_or_init_state(g)
    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "state": _serialize_state(row, data, sess.locale, None),
    })


@bp_agile_scrum_sim.get("/sessions/<int:session_id>/overview")
@jwt_required()
def facilitator_session_overview(session_id: int):
    sess = AgileTrainingSession.query.get(session_id)
    if not sess or sess.owner_user_id != _uid():
        return jsonify({"error": "Forbidden"}), 403
    groups = AgileTrainingGroup.query.filter_by(session_id=session_id).all()
    out = []
    for g in groups:
        row, data = _get_or_init_state(g)
        metrics = data.get("review_metrics") or _compute_review(data)
        out.append({
            "group":        {"id": g.id, "name": g.name, "slug": g.slug},
            "phase":        data.get("phase"),
            "current_day":  data.get("current_day"),
            "version":      int(data.get("version", 0)),
            "updated_at":   data.get("updated_at"),
            "participants_count": len(data.get("participants", {})),
            "metrics":      metrics,
            "sprint_goal":  data.get("sprint_goal", ""),
        })
    return jsonify({"session": {"id": sess.id, "title": sess.title, "locale": sess.locale}, "groups": out})


@bp_agile_scrum_sim.post("/groups/<int:group_id>/pause")
@jwt_required()
def facilitator_group_pause(group_id: int):
    g = AgileTrainingGroup.query.get(group_id)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    sess = AgileTrainingSession.query.get(g.session_id)
    if not sess or sess.owner_user_id != _uid():
        return jsonify({"error": "Forbidden"}), 403
    body = request.get_json(silent=True) or {}
    paused = bool(body.get("paused", True))
    row, data = _get_or_init_state(g)
    data["paused"] = paused
    _save_state(row, data)
    return jsonify({"ok": True, "paused": paused})


@bp_agile_scrum_sim.post("/groups/<int:group_id>/reset")
@jwt_required()
def facilitator_group_reset(group_id: int):
    g = AgileTrainingGroup.query.get(group_id)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    sess = AgileTrainingSession.query.get(g.session_id)
    if not sess or sess.owner_user_id != _uid():
        return jsonify({"error": "Forbidden"}), 403
    row = (
        AgileTrainingScrumSimState.query
        .filter_by(group_id=g.id)
        .first()
    )
    fresh = _initial_state("ru")
    if row:
        row.data_json = json.dumps(fresh, ensure_ascii=False)
        row.phase = fresh["phase"]
        row.current_day = 0
        row.version = fresh["version"]
        row.paused = False
    else:
        db.session.add(AgileTrainingScrumSimState(
            group_id=g.id, phase=fresh["phase"], current_day=0,
            version=1, paused=False, data_json=json.dumps(fresh, ensure_ascii=False),
        ))
    db.session.commit()
    return jsonify({"ok": True})
