"""Backend тренинга «Kanban-система и системное мышление» (STATIK-ориентированный).

API под префиксом `/api/agile-training/kanban`.

Использует общие сущности обучающего каркаса:
  - AgileTrainingSession (exercise_key = "kanban_system")
  - AgileTrainingGroup
  - AgileTrainingParticipant

Ответы храним одной записью на участника (JSON в data_json). Тренинг — для
новичков, не обязательно из IT. Акцент — обучение через практику: анализ
запросов, поток, классы обслуживания, политики, каденции и, наконец,
визуальная Kanban-доска со swimlanes и WIP-лимитами. Бэкенд не оценивает,
только хранит артефакт, считает «последствия» по простым правилам и даёт
анонимного AI-помощника с лимитом.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from typing import Dict, List, Optional, Tuple

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database import db
from models import (
    AgileTrainingGroup,
    AgileTrainingKanbanAnswer,
    AgileTrainingParticipant,
    AgileTrainingSession,
)


bp_agile_kanban = Blueprint(
    "agile_kanban", __name__, url_prefix="/api/agile-training/kanban"
)


# --------------------------- constants / content ---------------------------


AI_CALLS_LIMIT_PER_PARTICIPANT = 15
AI_PROMPT_LIMIT_CHARS = 2000
MAX_DEMAND_ROWS = 20
MAX_WORKFLOW_STAGES = 10
MAX_CLASSES = 6
MAX_POLICIES = 12
MAX_SWIMLANES = 6
MAX_CARDS = 60

ALLOWED_STAGES = (
    "case_choice",
    "intro",
    "example",
    "dissatisfaction",
    "demand",
    "workflow",
    "classes",
    "policies",
    "cadences",
    "board",
    "consequences",
    "improve",
    "summary",
)
STAGE_SET = set(ALLOWED_STAGES)

ALLOWED_CASE_KEYS = {"realty", "helpdesk"}
ALLOWED_CADENCE_VALUES = {"daily", "weekly", "biweekly", "monthly", "on_demand"}


CONTENT = {
    "ru": {
        "cases": [
            {
                "key": "realty",
                "emoji": "🏢",
                "label": "Агентство недвижимости",
                "short": "Классический пример из задания. Подходит тем, кто работает не в IT.",
                "title": "Агентство аренды недвижимости, 50 сотрудников",
                "context": [
                    "50 сотрудников: менеджеры, юристы, фотографы, маркетологи",
                    "Разные клиенты: VIP, корпоративные контракты, частные арендаторы",
                    "Разные задачи: срочный показ, плановый договор, повторный клиент",
                    "Высокая вариативность: один день — 3 запроса, другой — 30",
                ],
                "pain": "Система работает нестабильно: задачи теряются, VIP ждут, у менеджеров выгорание.",
                "example_static": {
                    "dissatisfaction_internal": "Менеджеры жалуются, что не успевают и не понимают, что брать первым",
                    "dissatisfaction_client": "Клиенты ждут по 2 дня ответа и не понимают, кто ведёт их запрос",
                    "demand": [
                        {
                            "type": "Срочный показ VIP-клиенту",
                            "source": "Персональный менеджер VIP",
                            "frequency": "3–5 в неделю",
                            "expectations": "Ответ за 30 минут, показ в день обращения",
                        },
                        {
                            "type": "Подготовка договора аренды",
                            "source": "Менеджер после показа",
                            "frequency": "10–15 в неделю",
                            "expectations": "Договор готов за 2 дня",
                        },
                    ],
                },
                "suggested_workflow": [
                    "Запрос поступил",
                    "В работе",
                    "Согласование с юристом",
                    "Выполнение",
                    "Завершено",
                ],
                "suggested_classes": [
                    {"name": "VIP",           "color": "#7c3aed", "criteria": "VIP-клиенты и корпоративные договоры"},
                    {"name": "Срочные",       "color": "#ef4444", "criteria": "Пришли сегодня и нужно решить за 1 день"},
                    {"name": "Стандарт",      "color": "#0ea5e9", "criteria": "Обычный поток по очереди"},
                    {"name": "Фикс. дата",    "color": "#f59e0b", "criteria": "Есть конкретный дедлайн (например, дата показа)"},
                ],
                "suggested_swimlanes": [
                    {"name": "VIP"},
                    {"name": "Срочные"},
                    {"name": "Стандарт"},
                ],
                "suggested_wip": {"default": 3},
                "clues": {
                    "dissatisfaction": [
                        "Иван, менеджер аренды: «Утром приходят 3 VIP одновременно и 5 обычных — я теряюсь, за кого браться»",
                        "Марина, юрист: «Мне в 17:50 приносят срочный договор и ждут, что я уйду домой в 19:00. Так каждый второй день»",
                        "Фотограф Саша: «Меня записывают на показ через менеджера в чате. Половина запросов теряется»",
                        "Отзыв клиента в 2ГИС: «2 дня жду ответа по квартире — ушёл к конкурентам»",
                        "VIP-клиент Пётр С.: «Мне обещали перезвонить за 30 минут, а перезвонили на следующий день»",
                    ],
                    "demand": [
                        "Журнал обращений за прошлую неделю: 23 звонка от VIP, 47 писем от обычных клиентов, 12 лидов с сайта",
                        "VIP-менеджер: «В пиковые дни — до 6 срочных показов за смену»",
                        "Маркетинг: «На e-mail рассылки по корпоративным клиентам приходит 8–10 откликов в неделю»",
                        "Юридический отдел: «На согласование договора уходит 2 дня, если без спешки»",
                        "Руководитель отдела: «Возвращающиеся клиенты дают 30% выручки и не ждут долго»",
                    ],
                    "workflow": [
                        "Сегодня: клиент звонит → менеджер записывает запрос в личный блокнот → едет на показ → после показа диктует условия юристу → юрист готовит договор → подписываем",
                        "Ни одна задача не лежит на общей доске — всё в почте конкретного менеджера",
                        "Если менеджер заболел, его запросы никто не видит",
                    ],
                    "classes": [
                        "VIP и корпоративные — бьёмся за каждого, уходит — теряем контракт на 3 года",
                        "Срочные показы — бронируются в день обращения, клиент уже едет",
                        "Обычные аренды — готовы подождать 2–3 дня, главное не теряться",
                        "Фиксированные даты — заезд в квартиру в конкретный день, просрочить = штраф",
                    ],
                    "policies": [
                        "Сейчас правил нигде не записано — каждый менеджер решает сам",
                        "VIP обычно берут по звонку руководителя, а не по доске",
                        "Когда задача застряла, её не эскалируют — «сама разрулится»",
                        "Обеды и выходные стабильно у всех, кроме срочных показов",
                    ],
                    "cadences": [
                        "Планёрок нет — статус задач обсуждают в корп. чате хаотично",
                        "Новые запросы попадают в работу сразу, без обсуждения приоритетов",
                        "Раз в месяц — отчёт по сделкам, но про поток работ там ничего",
                    ],
                    "board": [
                        "Хотим, чтобы VIP были отдельно видны всей команде, а не только персональному менеджеру",
                        "Нужно, чтобы юристы заранее видели, какие договоры к ним идут",
                        "Желательно, чтобы руководитель мог сказать «стоп, у нас перегруз» не разбирая почту",
                    ],
                },
            },
            {
                "key": "helpdesk",
                "emoji": "🛎️",
                "label": "Служба поддержки клиентов",
                "short": "Удобный пример для IT и не-IT: обычный helpdesk с разными SLA.",
                "title": "Служба поддержки пользователей, 30 сотрудников",
                "context": [
                    "30 операторов и специалистов 2-й линии",
                    "Разные каналы: чат, почта, телефон",
                    "Есть договоры с разными SLA: обычные, корпоративные, premium",
                    "Поток неровный: вечером и в понедельник — пики",
                ],
                "pain": "Тикеты теряются между линиями, premium-клиенты жалуются, операторы перерабатывают.",
                "example_static": {
                    "dissatisfaction_internal": "Операторы не знают, что брать первым, 2-я линия завалена старыми тикетами",
                    "dissatisfaction_client": "Ответ приходит с задержкой, иногда один и тот же вопрос задают дважды",
                    "demand": [
                        {
                            "type": "Инцидент от premium-клиента",
                            "source": "Почта/телефон",
                            "frequency": "5–10 в день",
                            "expectations": "Первая реакция за 15 минут",
                        },
                        {
                            "type": "Обычный вопрос из чата",
                            "source": "Чат на сайте",
                            "frequency": "50–80 в день",
                            "expectations": "Ответ в течение дня",
                        },
                    ],
                },
                "suggested_workflow": [
                    "Новый тикет",
                    "1-я линия",
                    "Передан на 2-ю линию",
                    "Ждёт ответа клиента",
                    "Закрыт",
                ],
                "suggested_classes": [
                    {"name": "Premium",   "color": "#7c3aed", "criteria": "Premium-SLA, реакция за 15 минут"},
                    {"name": "Инцидент",  "color": "#ef4444", "criteria": "Что-то не работает прямо сейчас"},
                    {"name": "Стандарт",  "color": "#0ea5e9", "criteria": "Обычный вопрос"},
                    {"name": "Дата",      "color": "#f59e0b", "criteria": "Привязан к конкретной дате (релиз, отпуск)"},
                ],
                "suggested_swimlanes": [
                    {"name": "Premium"},
                    {"name": "Инциденты"},
                    {"name": "Стандарт"},
                ],
                "suggested_wip": {"default": 4},
                "clues": {
                    "dissatisfaction": [
                        "Оператор 1-й линии: «В 10 утра одновременно в чате 12 человек, в почте ещё 25 — за кого браться?»",
                        "2-я линия: «Нам передают тикеты без контекста, приходится заново собирать данные»",
                        "Premium-клиент в тикете: «Реакция за 4 часа при SLA 15 минут — верните деньги»",
                        "Старший оператор: «Один и тот же вопрос мы ответили дважды — клиент в бешенстве»",
                        "HR-отчёт: у 3-х операторов за полгода — увольнение по причине «переработки»",
                    ],
                    "demand": [
                        "Статистика за неделю: 350 чатов, 200 писем, 80 звонков",
                        "Понедельник 9:00–12:00 — пик: +60% обращений",
                        "Premium-клиенты: ~30 инцидентов в день, 15-мин. SLA",
                        "Корпоративные: ~40 запросов в день, SLA 1 час",
                        "Обычные клиенты: ~250 вопросов в день, SLA «в течение дня»",
                    ],
                    "workflow": [
                        "Сейчас: тикет → 1-я линия пытается ответить → если не может, тегает 2-ю линию в чате → 2-я линия берёт когда освободится → отвечает клиенту",
                        "Тикет от premium-клиента может стоять в «общей» очереди часами, если 1-я линия пропустила",
                        "Между линиями нет чёткой передачи — тикеты «зависают»",
                    ],
                    "classes": [
                        "Premium-клиенты — контракт 5–20 млн в год, потерять одного = −10% выручки",
                        "Инциденты — что-то не работает прямо сейчас, бизнес клиента стоит",
                        "Стандартные вопросы — важны, но потерпят до конца дня",
                        "Релизы и плановые работы — привязаны к конкретной дате",
                    ],
                    "policies": [
                        "Правила эскалации нигде не записаны — каждый оператор решает сам",
                        "Premium-клиентов по идее берут сразу, но фактически застревают в общей очереди",
                        "«Закончить начатое перед тем, как брать новое» — никто не соблюдает",
                        "Ночные смены и выходные обсуждаются в чате раз в неделю",
                    ],
                    "cadences": [
                        "Стендапов нет, 1-я и 2-я линии почти не общаются",
                        "Новые тикеты берут в работу по мере появления, без фильтра",
                        "Раз в месяц — разбор жалоб, но уже после того, как клиенты ушли",
                    ],
                    "board": [
                        "Premium и инциденты нужно показать отдельно — чтобы не тонули в общей очереди",
                        "2-я линия хочет видеть, что к ним идёт, не дожидаясь тега в чате",
                        "Руководитель хочет одним взглядом понимать, где затык",
                    ],
                },
            },
        ],
        "primer": {
            "kanban_title": "Что такое Kanban простыми словами?",
            "kanban_text": (
                "Kanban — это не инструмент и не программа, а способ увидеть и выровнять поток работы. "
                "Вы рисуете доску (столбцы — это этапы), кладёте задачи на стикеры и вводите правила: "
                "например, сколько задач одновременно может быть на каждом этапе (это называется WIP-лимит). "
                "Цель — чтобы работа двигалась спокойно, а не копилась в одном месте."
            ),
            "flow_title": "Что такое «поток работы»?",
            "flow_text": (
                "Поток — это путь, который проходит задача от появления до завершения. Для любой работы "
                "его можно нарисовать: «поступил запрос → кто-то взял → согласовал → сделал → закрыл». "
                "Когда поток видно, сразу видны и места, где задачи застревают."
            ),
            "class_title": "Что такое «классы обслуживания»?",
            "class_text": (
                "Классы обслуживания — это типы задач, которые мы обрабатываем по-разному: "
                "«VIP» идёт вне очереди, «Срочные» — в день обращения, «Стандарт» — по очереди, "
                "«Фиксированная дата» — к конкретному числу. Классы помогают договариваться, "
                "кому что нужно дать раньше, без хаоса."
            ),
            "wip_title": "Что такое WIP-лимиты?",
            "wip_text": (
                "WIP (work-in-progress) — это сколько задач одновременно может быть «в работе» на этапе. "
                "Лимит не позволяет команде набрать 30 задач сразу: лучше закончить 3 и взять следующие. "
                "Без лимитов доска быстро превращается в хаос."
            ),
            "swimlane_title": "Что такое swimlanes (дорожки)?",
            "swimlane_text": (
                "Swimlanes — это горизонтальные дорожки на доске. На каждой дорожке — свой класс задач. "
                "Например, верхняя дорожка «VIP», средняя «Срочные», нижняя «Стандарт». Так легко видно, "
                "что VIP-задачи не стоят в общей очереди с обычными."
            ),
            "urgent_pitfall": (
                "«Если всё срочное — ничего не срочное». Если все задачи помечены как VIP или Срочные, "
                "команда перестаёт отличать действительно важное."
            ),
        },
        "cadences": {
            "replenishment": {
                "title": "Как часто берём новые задачи в работу (пополнение)",
                "options": [
                    {"key": "daily",     "label": "Каждый день"},
                    {"key": "weekly",    "label": "Раз в неделю"},
                    {"key": "biweekly",  "label": "Раз в 2 недели"},
                    {"key": "on_demand", "label": "По мере освобождения"},
                ],
            },
            "review": {
                "title": "Как часто смотрим на доску и обсуждаем",
                "options": [
                    {"key": "daily",     "label": "Каждый день (stand-up)"},
                    {"key": "weekly",    "label": "Раз в неделю"},
                    {"key": "biweekly",  "label": "Раз в 2 недели"},
                    {"key": "monthly",   "label": "Раз в месяц"},
                ],
            },
        },
        "hints": {
            "dissatisfaction": ["задержки", "перегруз", "хаос в приоритетах", "потеря задач", "повторная работа", "конфликты"],
            "demand_types":    ["срочный инцидент", "плановая задача", "регулярный отчёт", "запрос клиента", "внутренний запрос"],
            "demand_sources":  ["чат", "почта", "телефон", "руководитель", "клиент", "отдел продаж"],
            "demand_freq":     ["несколько раз в день", "ежедневно", "несколько раз в неделю", "раз в неделю", "пиковая нагрузка в понедельник"],
            "policies":        ["VIP берём вне очереди", "после блокировки — эскалация", "закончить начатое, прежде чем брать новое", "дневной стендап 15 минут"],
        },
    },
    "en": {
        "cases": [
            {
                "key": "realty",
                "emoji": "🏢",
                "label": "Real-estate rental agency",
                "short": "A classic non-IT example from the brief.",
                "title": "Real-estate rental agency, 50 people",
                "context": [
                    "50 people: managers, lawyers, photographers, marketing",
                    "Different clients: VIP, corporate, private tenants",
                    "Different tasks: urgent viewing, scheduled contract, returning client",
                    "High variability: 3 requests one day, 30 another",
                ],
                "pain": "The system is unstable: tasks get lost, VIPs wait, managers burn out.",
                "example_static": {
                    "dissatisfaction_internal": "Managers complain they can't keep up and don't know what to pick first",
                    "dissatisfaction_client": "Clients wait two days for an answer and don't know who owns their request",
                    "demand": [
                        {
                            "type": "Urgent viewing for a VIP client",
                            "source": "Personal VIP manager",
                            "frequency": "3–5 a week",
                            "expectations": "Reply in 30 minutes, viewing the same day",
                        },
                        {
                            "type": "Rental contract preparation",
                            "source": "Manager after the viewing",
                            "frequency": "10–15 a week",
                            "expectations": "Contract ready in 2 days",
                        },
                    ],
                },
                "suggested_workflow": [
                    "Request received",
                    "In progress",
                    "Legal review",
                    "Execution",
                    "Done",
                ],
                "suggested_classes": [
                    {"name": "VIP",         "color": "#7c3aed", "criteria": "VIP and corporate contracts"},
                    {"name": "Urgent",      "color": "#ef4444", "criteria": "Arrived today, needs to be done in 1 day"},
                    {"name": "Standard",    "color": "#0ea5e9", "criteria": "Normal flow, FIFO"},
                    {"name": "Fixed date",  "color": "#f59e0b", "criteria": "Has a specific deadline (viewing date)"},
                ],
                "suggested_swimlanes": [
                    {"name": "VIP"},
                    {"name": "Urgent"},
                    {"name": "Standard"},
                ],
                "suggested_wip": {"default": 3},
                "clues": {
                    "dissatisfaction": [
                        "Ivan, rental manager: \"In the morning 3 VIPs ping me at once plus 5 regular ones — I don't know who to pick first\"",
                        "Marina, lawyer: \"They bring me an urgent contract at 5:50 PM and expect me to leave at 7. It happens every other day\"",
                        "Sasha, photographer: \"Managers book me for viewings via chat — half of the requests get lost\"",
                        "Customer review on Google: \"Waited 2 days for a reply about an apartment — went to a competitor\"",
                        "VIP client Peter S.: \"I was promised a call-back in 30 minutes, got one the next day\"",
                    ],
                    "demand": [
                        "Last week's request log: 23 VIP calls, 47 emails from regular clients, 12 website leads",
                        "VIP manager: \"On peak days — up to 6 urgent viewings per shift\"",
                        "Marketing: \"Our corporate email campaigns bring 8–10 replies per week\"",
                        "Legal: \"A contract takes 2 days to prepare if we're not rushed\"",
                        "Head of sales: \"Returning clients are 30% of revenue and won't wait long\"",
                    ],
                    "workflow": [
                        "Today: client calls → manager writes the request in a personal notebook → drives to the viewing → dictates terms to the lawyer → lawyer drafts the contract → signing",
                        "No task lives on a shared board — everything is in the personal manager's email",
                        "If a manager is sick, nobody sees their requests",
                    ],
                    "classes": [
                        "VIP and corporate — fight for every one, losing them = a 3-year contract gone",
                        "Urgent viewings — booked the same day, the client is already driving",
                        "Regular rentals — willing to wait 2–3 days as long as we don't lose them",
                        "Fixed-date — move-in on a specific day, missing it means a fine",
                    ],
                    "policies": [
                        "Today there are no written rules — every manager decides for themselves",
                        "VIPs are usually picked up on a head's phone call, not via the board",
                        "When a task gets stuck, nobody escalates — \"it'll sort itself out\"",
                        "Lunches and days off are respected by everyone, except for urgent viewings",
                    ],
                    "cadences": [
                        "No stand-ups — task status is discussed ad-hoc in a corporate chat",
                        "New requests enter work immediately, without any priority discussion",
                        "A monthly deal report — but nothing about the flow of work",
                    ],
                    "board": [
                        "We want VIPs visible to the whole team, not only to the personal manager",
                        "Lawyers need to see which contracts are coming their way in advance",
                        "The head wants to call 'stop, we're overloaded' without digging through emails",
                    ],
                },
            },
            {
                "key": "helpdesk",
                "emoji": "🛎️",
                "label": "Customer support team",
                "short": "Friendly for IT and non-IT: a helpdesk with different SLAs.",
                "title": "Customer support team, 30 people",
                "context": [
                    "30 agents and a 2nd-line team",
                    "Channels: chat, email, phone",
                    "Different SLAs: basic, corporate, premium",
                    "Uneven flow: evening and Monday are peaks",
                ],
                "pain": "Tickets get lost between lines, premium clients complain, agents overwork.",
                "example_static": {
                    "dissatisfaction_internal": "Agents don't know what to pick first, 2nd line is buried in old tickets",
                    "dissatisfaction_client": "Replies arrive late, the same question is sometimes answered twice",
                    "demand": [
                        {
                            "type": "Premium-client incident",
                            "source": "Email/phone",
                            "frequency": "5–10 a day",
                            "expectations": "First response in 15 minutes",
                        },
                        {
                            "type": "Regular chat question",
                            "source": "Website chat",
                            "frequency": "50–80 a day",
                            "expectations": "Reply within the day",
                        },
                    ],
                },
                "suggested_workflow": [
                    "New ticket",
                    "1st line",
                    "Passed to 2nd line",
                    "Waiting for the client",
                    "Closed",
                ],
                "suggested_classes": [
                    {"name": "Premium",   "color": "#7c3aed", "criteria": "Premium SLA, 15-minute reaction"},
                    {"name": "Incident",  "color": "#ef4444", "criteria": "Something is broken right now"},
                    {"name": "Standard",  "color": "#0ea5e9", "criteria": "Regular question"},
                    {"name": "Date",      "color": "#f59e0b", "criteria": "Tied to a specific date (release, holiday)"},
                ],
                "suggested_swimlanes": [
                    {"name": "Premium"},
                    {"name": "Incidents"},
                    {"name": "Standard"},
                ],
                "suggested_wip": {"default": 4},
                "clues": {
                    "dissatisfaction": [
                        "1st-line agent: \"At 10 AM there are 12 people in the chat and 25 in email — who do I pick?\"",
                        "2nd-line: \"They hand us tickets without context, we have to re-collect the data\"",
                        "Premium client in a ticket: \"4-hour reaction when the SLA is 15 min — I want a refund\"",
                        "Senior agent: \"We answered the same question twice — the client is furious\"",
                        "HR report: 3 agents left in half a year, all quoting 'overwork'\",",
                    ],
                    "demand": [
                        "Weekly stats: 350 chats, 200 emails, 80 calls",
                        "Monday 9–12 AM is a peak: +60% of contacts",
                        "Premium clients: ~30 incidents per day, 15-min SLA",
                        "Corporate: ~40 requests per day, 1-hour SLA",
                        "Regular clients: ~250 questions per day, SLA 'within the day'",
                    ],
                    "workflow": [
                        "Today: ticket → 1st line tries to answer → if not, tags 2nd line in chat → 2nd line takes it when free → replies",
                        "A premium-client ticket can sit in the common queue for hours if 1st line misses it",
                        "No formal hand-off between lines — tickets 'hang'",
                    ],
                    "classes": [
                        "Premium clients — contracts of $50k–$200k a year; losing one ≈ −10% revenue",
                        "Incidents — something is broken right now, the client's business is stalled",
                        "Standard — important but can wait until end of day",
                        "Releases and planned work — tied to specific dates",
                    ],
                    "policies": [
                        "Escalation rules aren't written anywhere — each agent guesses",
                        "In theory premiums go first, in reality they stick in the common queue",
                        "'Finish what's started before picking new work' — nobody follows it",
                        "Night shifts and weekends are discussed ad-hoc in chat once a week",
                    ],
                    "cadences": [
                        "No stand-ups — 1st and 2nd line barely communicate",
                        "New tickets enter work immediately with no filter",
                        "A monthly complaint review — but only after clients have already left",
                    ],
                    "board": [
                        "Premiums and incidents must be visible separately — so they don't drown in the common queue",
                        "2nd line wants to see what's coming before being tagged in chat",
                        "The head wants a one-glance view of where things are stuck",
                    ],
                },
            },
        ],
        "primer": {
            "kanban_title": "What is Kanban in simple words?",
            "kanban_text": (
                "Kanban is not a tool or software — it's a way to see and shape the flow of your work. "
                "You draw a board (columns are stages), put tasks on stickers and add rules: "
                "for example, how many tasks can be «in progress» on a stage at the same time (a WIP limit). "
                "The goal is for work to flow calmly instead of piling up in one place."
            ),
            "flow_title": "What is «flow of work»?",
            "flow_text": (
                "The flow is the path a task takes from appearing to being done. Any work has one: "
                "«request arrived → someone took it → reviewed → done → closed». Once the flow is visible, "
                "the places where tasks get stuck become obvious."
            ),
            "class_title": "What are «classes of service»?",
            "class_text": (
                "Classes of service are task types we handle differently: «VIP» jumps the queue, "
                "«Urgent» is done the same day, «Standard» is FIFO, «Fixed date» ends on a specific date. "
                "Classes help the team agree who gets what first, without chaos."
            ),
            "wip_title": "What are WIP limits?",
            "wip_text": (
                "WIP (work-in-progress) is how many tasks can be «in progress» at a stage at the same time. "
                "A limit prevents the team from starting 30 things at once — it's better to finish 3 and pick "
                "the next. Without limits the board quickly turns into chaos."
            ),
            "swimlane_title": "What are swimlanes?",
            "swimlane_text": (
                "Swimlanes are horizontal rows on the board. Each row is a class of task. "
                "For example: top row «VIP», middle «Urgent», bottom «Standard». This way VIP tasks "
                "don't sit in the same queue as regular ones."
            ),
            "urgent_pitfall": (
                "«If everything is urgent — nothing is urgent». If all tasks are marked VIP or Urgent, "
                "the team stops telling what really matters."
            ),
        },
        "cadences": {
            "replenishment": {
                "title": "How often do we pull new work in (replenishment)",
                "options": [
                    {"key": "daily",     "label": "Every day"},
                    {"key": "weekly",    "label": "Once a week"},
                    {"key": "biweekly",  "label": "Every 2 weeks"},
                    {"key": "on_demand", "label": "As capacity frees up"},
                ],
            },
            "review": {
                "title": "How often do we look at the board and talk about it",
                "options": [
                    {"key": "daily",    "label": "Every day (stand-up)"},
                    {"key": "weekly",   "label": "Once a week"},
                    {"key": "biweekly", "label": "Every 2 weeks"},
                    {"key": "monthly",  "label": "Once a month"},
                ],
            },
        },
        "hints": {
            "dissatisfaction": ["delays", "overload", "chaotic priorities", "lost tasks", "rework", "internal conflicts"],
            "demand_types":    ["urgent incident", "scheduled task", "recurring report", "client request", "internal request"],
            "demand_sources":  ["chat", "email", "phone", "manager", "client", "sales"],
            "demand_freq":     ["several times a day", "daily", "a few times a week", "once a week", "Monday peak"],
            "policies":        ["VIP jump the queue", "after being blocked — escalate", "finish before starting new", "15-min daily stand-up"],
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


def _safe_json_load(raw: Optional[str]) -> Dict:
    if not raw:
        return {}
    try:
        v = json.loads(raw)
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def _clamp_text(value, limit: int = 1200) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    return s[:limit]


def _clean_color(value) -> str:
    s = str(value or "").strip()
    if len(s) == 7 and s.startswith("#") and all(c in "0123456789abcdefABCDEF" for c in s[1:]):
        return s
    return "#0ea5e9"


def _clean_demand(raw) -> List[Dict]:
    out: List[Dict] = []
    if not isinstance(raw, list):
        return out
    for idx, item in enumerate(raw[:MAX_DEMAND_ROWS]):
        if not isinstance(item, dict):
            continue
        row = {
            "id": str(item.get("id") or f"d{idx+1}")[:16],
            "type": _clamp_text(item.get("type"), 180) or "",
            "source": _clamp_text(item.get("source"), 180) or "",
            "frequency": _clamp_text(item.get("frequency"), 120) or "",
            "expectations": _clamp_text(item.get("expectations"), 240) or "",
        }
        if not (row["type"] or row["source"] or row["frequency"] or row["expectations"]):
            continue
        out.append(row)
    return out


def _clean_workflow(raw) -> List[Dict]:
    out: List[Dict] = []
    if not isinstance(raw, list):
        return out
    for idx, item in enumerate(raw[:MAX_WORKFLOW_STAGES]):
        if isinstance(item, str):
            name = item
        elif isinstance(item, dict):
            name = str(item.get("name") or "")
        else:
            continue
        name = name.strip()[:80]
        if not name:
            continue
        sid = str((item or {}).get("id") if isinstance(item, dict) else "") or f"s{idx+1}"
        out.append({"id": sid[:16], "name": name})
    return out


def _clean_classes(raw) -> List[Dict]:
    out: List[Dict] = []
    if not isinstance(raw, list):
        return out
    for idx, item in enumerate(raw[:MAX_CLASSES]):
        if not isinstance(item, dict):
            continue
        name = _clamp_text(item.get("name"), 60) or ""
        if not name:
            continue
        out.append({
            "id": str(item.get("id") or f"c{idx+1}")[:16],
            "name": name,
            "color": _clean_color(item.get("color")),
            "criteria": _clamp_text(item.get("criteria"), 300) or "",
        })
    return out


def _clean_policies(raw) -> List[Dict]:
    out: List[Dict] = []
    if not isinstance(raw, list):
        return out
    for idx, item in enumerate(raw[:MAX_POLICIES]):
        if isinstance(item, str):
            text = item
        elif isinstance(item, dict):
            text = str(item.get("text") or "")
        else:
            continue
        text = text.strip()[:240]
        if not text:
            continue
        out.append({"id": f"p{idx+1}", "text": text})
    return out


def _clean_swimlanes(raw) -> List[Dict]:
    out: List[Dict] = []
    if not isinstance(raw, list):
        return out
    for idx, item in enumerate(raw[:MAX_SWIMLANES]):
        if isinstance(item, str):
            name = item
        elif isinstance(item, dict):
            name = str(item.get("name") or "")
        else:
            continue
        name = name.strip()[:60]
        if not name:
            continue
        lid = (item or {}).get("id") if isinstance(item, dict) else None
        out.append({"id": str(lid or f"l{idx+1}")[:16], "name": name})
    return out


def _clean_cards(raw, column_ids: set, lane_ids: set, class_ids: set) -> List[Dict]:
    out: List[Dict] = []
    if not isinstance(raw, list):
        return out
    for idx, item in enumerate(raw[:MAX_CARDS]):
        if not isinstance(item, dict):
            continue
        title = _clamp_text(item.get("title"), 160)
        if not title:
            continue
        col_id = str(item.get("column_id") or "")
        lane_id = str(item.get("lane_id") or "")
        class_id = str(item.get("class_id") or "")
        out.append({
            "id": str(item.get("id") or f"k{idx+1}")[:20],
            "title": title,
            "column_id": col_id if col_id in column_ids else "",
            "lane_id": lane_id if lane_id in lane_ids else "",
            "class_id": class_id if class_id in class_ids else "",
            "note": _clamp_text(item.get("note"), 240),
        })
    return out


def _clean_column_limits(raw, column_ids: set) -> Dict[str, int]:
    out: Dict[str, int] = {}
    if not isinstance(raw, dict):
        return out
    for k, v in raw.items():
        key = str(k)
        if key not in column_ids:
            continue
        try:
            iv = int(v)
        except (TypeError, ValueError):
            continue
        if iv <= 0 or iv > 99:
            continue
        out[key] = iv
    return out


def _clean_cadences(raw) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not isinstance(raw, dict):
        return out
    for key in ("replenishment", "review"):
        val = str(raw.get(key) or "").strip().lower()
        if val in ALLOWED_CADENCE_VALUES:
            out[key] = val
    return out


def _clean_board_payload(data: Dict) -> Dict:
    workflow = _clean_workflow(data.get("workflow"))
    classes = _clean_classes(data.get("classes"))
    swimlanes = _clean_swimlanes(data.get("swimlanes"))
    column_ids = {s["id"] for s in workflow}
    lane_ids = {l["id"] for l in swimlanes}
    class_ids = {c["id"] for c in classes}
    cards = _clean_cards(data.get("cards"), column_ids, lane_ids, class_ids)
    column_limits = _clean_column_limits(data.get("column_limits"), column_ids)
    return {
        "workflow": workflow,
        "classes": classes,
        "swimlanes": swimlanes,
        "cards": cards,
        "column_limits": column_limits,
    }


def _compute_consequences(data: Dict, locale: str) -> List[Dict]:
    """Простая «система последствий». Возвращает список сообщений."""
    msgs: List[Dict] = []
    ru = (locale != "en")

    workflow = data.get("workflow") or []
    classes = data.get("classes") or []
    swimlanes = data.get("swimlanes") or []
    cards = data.get("cards") or []
    column_limits = data.get("column_limits") or {}

    def add(severity: str, title_ru: str, title_en: str, hint_ru: str, hint_en: str):
        msgs.append({
            "severity": severity,
            "title": title_ru if ru else title_en,
            "hint": hint_ru if ru else hint_en,
        })

    # Отсутствие потока
    if len(workflow) < 3:
        add(
            "warn",
            "Поток слишком короткий",
            "The flow is too short",
            "Трудно увидеть, где задачи застревают, если всего 1–2 этапа. Добавьте хотя бы 3–4.",
            "With only 1–2 stages it's hard to spot where tasks get stuck. Add at least 3–4.",
        )

    # WIP-лимиты
    middle_stages = workflow[1:-1] if len(workflow) >= 3 else workflow
    no_limit_stages = [s for s in middle_stages if str(s.get("id")) not in column_limits]
    if no_limit_stages:
        names = ", ".join(s.get("name", "") for s in no_limit_stages[:4])
        add(
            "warn",
            "Без WIP-лимитов — ожидайте перегруза",
            "No WIP limits — expect overload",
            f"Этапы без ограничений: {names}. Без лимитов команда набирает слишком много и всё застревает.",
            f"Stages without limits: {names}. Without limits the team takes too much on and everything gets stuck.",
        )
    elif column_limits:
        # есть какие-то лимиты — это хорошо
        add(
            "ok",
            "WIP-лимиты установлены",
            "WIP limits are set",
            "Отлично — ограничения не дадут команде набрать сразу всё.",
            "Good — limits will prevent the team from grabbing everything at once.",
        )

    # Превышение лимитов
    over = []
    for col_id, limit in column_limits.items():
        count = sum(1 for c in cards if c.get("column_id") == col_id)
        if count > limit:
            col = next((w for w in workflow if w.get("id") == col_id), None)
            if col:
                over.append((col.get("name"), count, limit))
    if over:
        text_parts = [f"«{n}» — {c}/{l}" for n, c, l in over]
        add(
            "danger",
            "Превышен WIP-лимит",
            "WIP limit exceeded",
            "Задач больше, чем разрешено: " + "; ".join(text_parts) + ". Закончите начатое перед тем, как брать новое.",
            "More tasks than allowed: " + "; ".join(text_parts) + ". Finish before starting new ones.",
        )

    # «Всё срочное»
    if classes and cards:
        urgent_ids = set()
        for cl in classes:
            name = (cl.get("name") or "").lower()
            if any(w in name for w in ("vip", "срочн", "urgent", "premium", "инцидент", "incident")):
                urgent_ids.add(cl.get("id"))
        if urgent_ids:
            urgent_cards = sum(1 for c in cards if c.get("class_id") in urgent_ids)
            if len(cards) >= 3 and urgent_cards / len(cards) > 0.6:
                add(
                    "danger",
                    "«Если всё срочное — ничего не срочное»",
                    "«If everything is urgent — nothing is urgent»",
                    f"Более 60% задач помечены как VIP/срочные ({urgent_cards} из {len(cards)}). Команда перестанет различать настоящие приоритеты.",
                    f"Over 60% of tasks are marked VIP/urgent ({urgent_cards} of {len(cards)}). The team will lose real priorities.",
                )

    # Нет swimlanes
    if not swimlanes:
        add(
            "info",
            "Нет дорожек (swimlanes)",
            "No swimlanes",
            "Можно добавить 2–3 дорожки (например, VIP / Срочные / Стандарт) — так разные типы задач не будут толкаться в одной очереди.",
            "You could add 2–3 swimlanes (e.g. VIP / Urgent / Standard) — different task types won't fight for the same queue.",
        )

    # Нет классов
    if not classes:
        add(
            "info",
            "Не определены классы обслуживания",
            "No classes of service",
            "Когда все задачи «одинаковые», нельзя быстро договориться, кому в первую очередь. 3–4 класса обычно достаточно.",
            "When all tasks are «the same», it's impossible to agree who goes first. 3–4 classes are usually enough.",
        )

    # Пустые колонки
    if workflow and cards:
        empty_cols = [w for w in workflow if not any(c.get("column_id") == w.get("id") for c in cards)]
        if len(empty_cols) >= max(2, len(workflow) // 2):
            add(
                "info",
                "На доске много пустых колонок",
                "The board has many empty columns",
                "Попробуйте положить хотя бы одну карточку в каждый этап — станет виднее, где работа действительно идёт.",
                "Try placing at least one card in each stage — it will make visible where work actually flows.",
            )

    if not msgs:
        add(
            "ok",
            "Базовая система собрана",
            "A baseline system is in place",
            "Хороший старт. На реальной команде проверяйте её каждые 1–2 недели и настраивайте.",
            "A good start. On a real team, review it every 1–2 weeks and tune.",
        )

    return msgs


# --------------------------- model helpers ---------------------------


def _get_or_create_answer(group_id: int, participant_id: int) -> AgileTrainingKanbanAnswer:
    a = (
        AgileTrainingKanbanAnswer.query
        .filter_by(participant_id=participant_id)
        .first()
    )
    if a:
        return a
    a = AgileTrainingKanbanAnswer(
        group_id=group_id,
        participant_id=participant_id,
        data_json=json.dumps({}, ensure_ascii=False),
    )
    db.session.add(a)
    return a


def _serialize_answer(a: AgileTrainingKanbanAnswer) -> Dict:
    data = _safe_json_load(a.data_json)
    case_key = a.case_key or data.get("case_key")
    if case_key not in ALLOWED_CASE_KEYS:
        case_key = None
    return {
        "stage": a.stage,
        "case_key": case_key,
        "dissatisfaction": data.get("dissatisfaction") or {},
        "demand": data.get("demand") or [],
        "workflow": data.get("workflow") or [],
        "classes": data.get("classes") or [],
        "policies": data.get("policies") or [],
        "cadences": data.get("cadences") or {},
        "swimlanes": data.get("swimlanes") or [],
        "column_limits": data.get("column_limits") or {},
        "cards": data.get("cards") or [],
        "improved_board": data.get("improved_board") or None,
        "notes": data.get("notes") or {},
        "ai_history": data.get("ai_history") or [],
        "ai_calls": int(a.ai_calls or 0),
        "ai_calls_remaining": max(0, AI_CALLS_LIMIT_PER_PARTICIPANT - int(a.ai_calls or 0)),
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


# --------------------------- public (participant) ---------------------------


@bp_agile_kanban.get("/content")
def content_public():
    locale = _resolve_locale(request.args.get("locale"), None)
    return jsonify({"locale": locale, **CONTENT.get(locale, CONTENT["ru"])})


@bp_agile_kanban.get("/g/<slug>/state")
def participant_state(slug: str):
    g, sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404

    locale = _resolve_locale(request.args.get("locale"), sess)
    token = (request.args.get("participant_token") or "").strip()
    answer_payload: Optional[Dict] = None
    if token:
        p = _require_participant(g, token)
        if p:
            a = (
                AgileTrainingKanbanAnswer.query
                .filter_by(participant_id=p.id)
                .first()
            )
            if a:
                answer_payload = _serialize_answer(a)

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "session": {
            "id": sess.id if sess else None,
            "title": sess.title if sess else "",
            "exercise_key": sess.exercise_key if sess else "kanban_system",
            "locale": sess.locale if sess else "ru",
        },
        "effective_locale": locale,
        "content": CONTENT.get(locale, CONTENT["ru"]),
        "ai_calls_limit": AI_CALLS_LIMIT_PER_PARTICIPANT,
        "answer": answer_payload,
    })


@bp_agile_kanban.post("/g/<slug>/answer")
def participant_answer(slug: str):
    """Upsert всего артефакта участника.

    В body можно передавать любые поля из: case_key, stage, dissatisfaction{},
    demand[], workflow[], classes[], policies[], cadences{}, swimlanes[],
    column_limits{}, cards[], improved_board{}, notes{}, clear_ai_history.
    """
    g, _sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404

    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()

    if not token:
        return jsonify({"error": "participant_token required"}), 400

    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404

    a = _get_or_create_answer(g.id, p.id)
    data = _safe_json_load(a.data_json)

    if "stage" in body:
        stg = (body.get("stage") or "").strip().lower()
        if stg in STAGE_SET:
            a.stage = stg

    if "case_key" in body:
        ck = body.get("case_key")
        if ck is None or ck == "":
            a.case_key = None
            data.pop("case_key", None)
        else:
            ck = str(ck).strip().lower()
            if ck in ALLOWED_CASE_KEYS:
                a.case_key = ck
                data["case_key"] = ck

    if "dissatisfaction" in body and isinstance(body.get("dissatisfaction"), dict):
        d_in = body["dissatisfaction"]
        data["dissatisfaction"] = {
            "internal": _clamp_text(d_in.get("internal"), 1500) or "",
            "client":   _clamp_text(d_in.get("client"), 1500) or "",
        }

    if "demand" in body:
        data["demand"] = _clean_demand(body.get("demand"))

    if "workflow" in body:
        data["workflow"] = _clean_workflow(body.get("workflow"))

    if "classes" in body:
        data["classes"] = _clean_classes(body.get("classes"))

    if "policies" in body:
        data["policies"] = _clean_policies(body.get("policies"))

    if "cadences" in body:
        data["cadences"] = _clean_cadences(body.get("cadences"))

    if "swimlanes" in body:
        data["swimlanes"] = _clean_swimlanes(body.get("swimlanes"))

    # Для карточек и лимитов нам нужны текущие id колонок/дорожек/классов
    workflow = data.get("workflow") or []
    classes = data.get("classes") or []
    swimlanes = data.get("swimlanes") or []
    column_ids = {s["id"] for s in workflow if isinstance(s, dict) and s.get("id")}
    lane_ids = {l["id"] for l in swimlanes if isinstance(l, dict) and l.get("id")}
    class_ids = {c["id"] for c in classes if isinstance(c, dict) and c.get("id")}

    if "cards" in body:
        data["cards"] = _clean_cards(body.get("cards"), column_ids, lane_ids, class_ids)
    if "column_limits" in body:
        data["column_limits"] = _clean_column_limits(body.get("column_limits"), column_ids)

    if "improved_board" in body and isinstance(body.get("improved_board"), dict):
        data["improved_board"] = _clean_board_payload(body.get("improved_board"))

    if "notes" in body and isinstance(body.get("notes"), dict):
        notes_in = body.get("notes") or {}
        notes_current = data.get("notes") or {}
        if not isinstance(notes_current, dict):
            notes_current = {}
        for k, v in notes_in.items():
            if not isinstance(k, str):
                continue
            key = k.strip()[:32]
            if not key:
                continue
            txt = _clamp_text(v, 2000)
            if txt is None:
                notes_current.pop(key, None)
            else:
                notes_current[key] = txt
        data["notes"] = notes_current

    if body.get("clear_ai_history"):
        data["ai_history"] = []

    # Считаем агрегаты для удобства фасилитатора
    a.cards_count = len(data.get("cards") or [])
    a.columns_count = len(data.get("workflow") or [])
    a.swimlanes_count = len(data.get("swimlanes") or [])

    a.data_json = json.dumps(data, ensure_ascii=False)
    db.session.commit()

    return jsonify({"saved": True, "answer": _serialize_answer(a)})


@bp_agile_kanban.get("/g/<slug>/consequences")
def participant_consequences(slug: str):
    g, sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    locale = _resolve_locale(request.args.get("locale"), sess)
    token = (request.args.get("participant_token") or "").strip()
    if not token:
        return jsonify({"error": "participant_token required"}), 400
    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404
    a = (
        AgileTrainingKanbanAnswer.query
        .filter_by(participant_id=p.id)
        .first()
    )
    data = _safe_json_load(a.data_json) if a else {}
    return jsonify({"consequences": _compute_consequences(data, locale)})


# --------------------------- AI helper ---------------------------


def _openai_client():
    try:
        from openai import OpenAI  # type: ignore
    except Exception:
        return None
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    try:
        return OpenAI(api_key=key)
    except Exception:
        return None


_SYSTEM_PROMPTS = {
    "ru": (
        "Ты — доброжелательный фасилитатор тренинга по Kanban и системному мышлению. "
        "Ученики — новички и не обязательно из IT. Никогда не говори «правильно/неправильно» "
        "и не выставляй оценок. Вместо этого задавай 1–3 коротких уточняющих вопроса, "
        "предложи вариант формулировки и коротко объясни, что можно улучшить. "
        "Пиши кратко, дружелюбно, по-русски, без жаргона. Отвечай в Markdown: "
        "короткие абзацы, списки, **жирный** для акцентов. Не придумывай факты о кейсе."
    ),
    "en": (
        "You are a friendly facilitator for a Kanban / systems-thinking training. "
        "Learners are beginners, not necessarily from IT. Never say «correct/incorrect» and "
        "never grade. Ask 1–3 short clarifying questions, suggest a wording and briefly "
        "explain what could be improved. Keep it short and friendly, in English, no jargon. "
        "Reply in Markdown: short paragraphs, lists, **bold** for emphasis. Do not invent facts."
    ),
}


def _ai_mode_instruction(mode: str, locale: str) -> str:
    mode = (mode or "").strip().lower()
    if locale == "en":
        table = {
            "dissatisfaction": "The learner describes sources of dissatisfaction (internal and client). Ask what makes the pain worst, suggest a crisp phrasing and note what might be a symptom vs. a cause.",
            "demand":         "The learner lists types of incoming work. Help them separate type / source / frequency / expectations, and point out if something looks too generic.",
            "workflow":       "The learner draws a flow. Ask about handoffs, returns, waiting stages; suggest a tighter sequence.",
            "classes":        "The learner defines classes of service. Suggest 3–4 with clear criteria and remind that «all urgent = nothing urgent».",
            "policies":       "The learner writes policies. Suggest 3–5 crisp rules (priorities, WIP, blockers) that a team can actually follow.",
            "board":          "The learner designs a Kanban board with swimlanes and WIP limits. Suggest reasonable WIP limits and whether swimlanes match the classes.",
            "improve":        "The learner improves the board after seeing consequences. Suggest specific adjustments and remind about slowing intake before speeding up work.",
            "generic":        "Help the learner move on. Ask 1–2 clarifying questions and suggest a next step.",
        }
    else:
        table = {
            "dissatisfaction": "Участник описывает источники неудовлетворённости (внутренние и клиентские). Спроси, что беспокоит сильнее всего, предложи чёткую формулировку и подскажи, где симптом, а где причина.",
            "demand":         "Участник описывает типы входящей работы. Помоги разделить: тип / источник / частота / ожидания — и укажи, если что-то слишком общее.",
            "workflow":       "Участник рисует поток. Спроси про передачи между людьми, возвраты и этапы ожидания; предложи более чёткую последовательность.",
            "classes":        "Участник придумывает классы обслуживания. Предложи 3–4 с понятными критериями и напомни: «если всё срочное — ничего не срочное».",
            "policies":       "Участник пишет политики. Предложи 3–5 конкретных правил (приоритеты, WIP, блокировки), которые команда реально сможет выполнять.",
            "board":          "Участник проектирует Kanban-доску со swimlanes и WIP-лимитами. Предложи разумные лимиты и подскажи, совпадают ли swimlanes с классами обслуживания.",
            "improve":        "Участник улучшает доску после просмотра последствий. Предложи конкретные правки и напомни: сначала замедляйте вход, а уже потом ускоряйте работу.",
            "generic":        "Помоги ученику двигаться дальше. Задай 1–2 уточняющих вопроса и предложи следующий шаг.",
        }
    return table.get(mode, table["generic"])


def _scripted_assist(mode: str, locale: str, user_input: str) -> str:
    if locale == "en":
        bank = {
            "dissatisfaction": (
                "**Questions to think about**\n\n"
                "- What bothers the team most right now?\n"
                "- What does the client feel when something goes wrong?\n"
                "- Which of these are symptoms, and which are real causes?"
            ),
            "demand": (
                "**Per type of work answer**\n\n"
                "- What exactly is the task?\n"
                "- Where does it come from?\n"
                "- How often does it arrive?\n"
                "- What does the client expect in timing and quality?"
            ),
            "workflow": (
                "**Draw the path a task takes**\n\n"
                "- Who receives it first?\n"
                "- Where does it wait?\n"
                "- Is there a review or handoff?\n"
                "- When is it «done» for the client?"
            ),
            "classes": (
                "**Ideas for classes of service**\n\n"
                "- VIP — jumps the queue (use sparingly).\n"
                "- Urgent — same day.\n"
                "- Standard — FIFO.\n"
                "- Fixed date — to a specific deadline."
            ),
            "policies": (
                "**Examples of crisp policies**\n\n"
                "- Finish what you started before pulling new work.\n"
                "- WIP per person: max 2.\n"
                "- Blocked > 1 day → escalate.\n"
                "- 15-minute daily stand-up at the board."
            ),
            "board": (
                "**Designing the board**\n\n"
                "- Put all the workflow stages as columns.\n"
                "- Add 2–3 swimlanes matching your main classes.\n"
                "- Set WIP limits on «in progress» and review stages.\n"
                "- Place cards and check if anything immediately overflows."
            ),
            "improve": (
                "**Tuning ideas**\n\n"
                "- If a stage overflows — lower its WIP limit or split the stage.\n"
                "- If everything is urgent — tighten the urgent criteria.\n"
                "- If a column is always empty — maybe it's not a real stage."
            ),
            "generic": "Take a breath. What is the very next thing the team would need to actually start using this system?",
        }
    else:
        bank = {
            "dissatisfaction": (
                "**Подумайте над вопросами**\n\n"
                "- Что сейчас раздражает команду сильнее всего?\n"
                "- Что чувствует клиент, когда что-то идёт не так?\n"
                "- Что из этого — симптомы, а что — настоящие причины?"
            ),
            "demand": (
                "**По каждому типу работы ответьте**\n\n"
                "- Что именно это за задача?\n"
                "- Откуда она приходит?\n"
                "- Как часто?\n"
                "- Что клиент ждёт по сроку и качеству?"
            ),
            "workflow": (
                "**Нарисуйте путь задачи**\n\n"
                "- Кто получает её первым?\n"
                "- Где она ждёт?\n"
                "- Где есть передача или проверка?\n"
                "- Когда она «готова» для клиента?"
            ),
            "classes": (
                "**Идеи для классов обслуживания**\n\n"
                "- VIP — вне очереди (используйте редко).\n"
                "- Срочные — в день обращения.\n"
                "- Стандарт — по очереди.\n"
                "- Фиксированная дата — к конкретной дате."
            ),
            "policies": (
                "**Примеры чётких правил**\n\n"
                "- Закончить начатое перед тем, как брать новое.\n"
                "- WIP на человека: максимум 2.\n"
                "- Задача заблокирована >1 дня → эскалация.\n"
                "- Ежедневный стендап у доски 15 минут."
            ),
            "board": (
                "**Проектируем доску**\n\n"
                "- Сделайте колонки из этапов потока.\n"
                "- Добавьте 2–3 дорожки (swimlanes) под основные классы.\n"
                "- Поставьте WIP-лимиты на «в работе» и проверке.\n"
                "- Разложите карточки и посмотрите, где сразу переполнение."
            ),
            "improve": (
                "**Идеи для доработки**\n\n"
                "- Этап переполняется → уменьшите его WIP или разделите.\n"
                "- Всё срочное → сузьте критерии «срочного».\n"
                "- Колонка всегда пустая → может, это не отдельный этап."
            ),
            "generic": "Сделайте паузу. Что нужно сделать команде самым первым, чтобы реально начать пользоваться этой системой?",
        }
    return bank.get(mode, bank["generic"])


@bp_agile_kanban.post("/g/<slug>/ai-assist")
def participant_ai_assist(slug: str):
    g, sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404

    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    mode = (body.get("mode") or "generic").strip().lower()
    locale = _resolve_locale(body.get("locale"), sess)
    user_input = _clamp_text(body.get("user_input"), AI_PROMPT_LIMIT_CHARS) or ""

    if not token:
        return jsonify({"error": "participant_token required"}), 400

    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404

    a = _get_or_create_answer(g.id, p.id)
    if int(a.ai_calls or 0) >= AI_CALLS_LIMIT_PER_PARTICIPANT:
        return jsonify({
            "error": "ai_limit_exceeded",
            "limit": AI_CALLS_LIMIT_PER_PARTICIPANT,
            "ai_calls": int(a.ai_calls or 0),
        }), 429

    client = _openai_client()
    stored = _safe_json_load(a.data_json)
    case_key = a.case_key or stored.get("case_key")
    locale_content = CONTENT.get(locale, CONTENT["ru"])
    case = None
    if case_key:
        case = next((c for c in (locale_content.get("cases") or []) if c.get("key") == case_key), None)
    if case is None and locale_content.get("cases"):
        case = locale_content["cases"][0]

    reply_text = ""
    model_used = None
    if client:
        system = _SYSTEM_PROMPTS.get(locale, _SYSTEM_PROMPTS["ru"])
        instruction = _ai_mode_instruction(mode, locale)
        if case:
            case_summary = f"{case.get('title','')}. {' '.join(case.get('context') or [])} {case.get('pain','')}".strip()
        else:
            case_summary = ""
        user_msg = (
            f"{instruction}\n\nКонтекст кейса: {case_summary}\n\n"
            f"Что написал участник:\n{user_input or '(пусто)'}"
        )
        try:
            resp = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.5,
                max_tokens=600,
            )
            choice = resp.choices[0] if resp.choices else None
            if choice and getattr(choice, "message", None):
                reply_text = (choice.message.content or "").strip()
            model_used = getattr(resp, "model", None)
        except Exception as exc:
            reply_text = ""
            model_used = f"error:{type(exc).__name__}"

    if not reply_text:
        reply_text = _scripted_assist(mode, locale, user_input)
        model_used = model_used or "scripted"

    a.ai_calls = int(a.ai_calls or 0) + 1
    data = _safe_json_load(a.data_json)
    history = data.get("ai_history") or []
    if not isinstance(history, list):
        history = []
    history.append({
        "mode": mode,
        "input": user_input,
        "reply": reply_text,
        "model": model_used,
    })
    data["ai_history"] = history[-20:]
    a.data_json = json.dumps(data, ensure_ascii=False)
    db.session.commit()

    return jsonify({
        "reply": reply_text,
        "model": model_used,
        "ai_calls": int(a.ai_calls or 0),
        "ai_calls_remaining": max(0, AI_CALLS_LIMIT_PER_PARTICIPANT - int(a.ai_calls or 0)),
    })


# --------------------------- facilitator ---------------------------


@bp_agile_kanban.get("/groups/<int:group_id>/participants")
@jwt_required()
def group_participants(group_id: int):
    uid = _uid()
    g = (
        AgileTrainingGroup.query
        .join(AgileTrainingSession, AgileTrainingSession.id == AgileTrainingGroup.session_id)
        .filter(AgileTrainingGroup.id == group_id, AgileTrainingSession.owner_user_id == uid)
        .first()
    )
    if not g:
        return jsonify({"error": "Not found"}), 404

    participants = (
        AgileTrainingParticipant.query
        .filter_by(group_id=g.id)
        .order_by(AgileTrainingParticipant.id.asc())
        .all()
    )
    rows: List[Dict] = []
    for idx, p in enumerate(participants, start=1):
        a = (
            AgileTrainingKanbanAnswer.query
            .filter_by(participant_id=p.id)
            .first()
        )
        if not a:
            rows.append({
                "id": p.id,
                "display_name": p.display_name or f"#{idx}",
                "anonymous_label": f"#{idx}",
                "joined_at": p.created_at.isoformat() if p.created_at else None,
                "has_answer": False,
            })
            continue
        data = _safe_json_load(a.data_json)
        rows.append({
            "id": p.id,
            "display_name": p.display_name or f"#{idx}",
            "anonymous_label": f"#{idx}",
            "joined_at": p.created_at.isoformat() if p.created_at else None,
            "has_answer": True,
            "stage": a.stage,
            "case_key": a.case_key or data.get("case_key"),
            "cards_count": int(a.cards_count or len(data.get("cards") or [])),
            "columns_count": int(a.columns_count or len(data.get("workflow") or [])),
            "swimlanes_count": int(a.swimlanes_count or len(data.get("swimlanes") or [])),
            "dissatisfaction": data.get("dissatisfaction") or {},
            "demand": data.get("demand") or [],
            "workflow": data.get("workflow") or [],
            "classes": data.get("classes") or [],
            "policies": data.get("policies") or [],
            "cadences": data.get("cadences") or {},
            "swimlanes": data.get("swimlanes") or [],
            "column_limits": data.get("column_limits") or {},
            "cards": data.get("cards") or [],
            "improved_board": data.get("improved_board") or None,
            "notes": data.get("notes") or {},
            "ai_calls": int(a.ai_calls or 0),
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        })

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants": rows,
    })


@bp_agile_kanban.get("/groups/<int:group_id>/results")
@jwt_required()
def group_results(group_id: int):
    uid = _uid()
    g = (
        AgileTrainingGroup.query
        .join(AgileTrainingSession, AgileTrainingSession.id == AgileTrainingGroup.session_id)
        .filter(AgileTrainingGroup.id == group_id, AgileTrainingSession.owner_user_id == uid)
        .first()
    )
    if not g:
        return jsonify({"error": "Not found"}), 404

    rows = AgileTrainingKanbanAnswer.query.filter_by(group_id=g.id).all()
    stage_counter: Counter = Counter()
    case_counter: Counter = Counter()
    total_cards = 0
    total_columns = 0
    total_swimlanes = 0
    with_board = 0
    for r in rows:
        if r.stage:
            stage_counter[r.stage] += 1
        if r.case_key:
            case_counter[r.case_key] += 1
        total_cards += int(r.cards_count or 0)
        total_columns += int(r.columns_count or 0)
        total_swimlanes += int(r.swimlanes_count or 0)
        if (r.cards_count or 0) > 0 and (r.columns_count or 0) > 0:
            with_board += 1
    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants_count": g.participants.count(),
        "answers_count": len(rows),
        "with_board_count": with_board,
        "avg_cards": round(total_cards / len(rows), 1) if rows else 0.0,
        "avg_columns": round(total_columns / len(rows), 1) if rows else 0.0,
        "avg_swimlanes": round(total_swimlanes / len(rows), 1) if rows else 0.0,
        "stages": dict(stage_counter),
        "cases": dict(case_counter),
    })


@bp_agile_kanban.get("/sessions/<int:session_id>/results")
@jwt_required()
def sessions_results(session_id: int):
    uid = _uid()
    sess = (
        AgileTrainingSession.query
        .filter_by(id=session_id, owner_user_id=uid)
        .first()
    )
    if not sess:
        return jsonify({"error": "Not found"}), 404

    groups = sess.groups.order_by(AgileTrainingGroup.id.asc()).all()
    groups_view: List[Dict] = []
    totals = {"groups": 0, "participants": 0, "answers": 0, "with_board": 0}
    for g in groups:
        rows = AgileTrainingKanbanAnswer.query.filter_by(group_id=g.id).all()
        participants_count = g.participants.count()
        totals["groups"] += 1
        totals["participants"] += participants_count
        totals["answers"] += len(rows)
        with_board = sum(1 for r in rows if (r.cards_count or 0) > 0 and (r.columns_count or 0) > 0)
        totals["with_board"] += with_board
        groups_view.append({
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            "participants_count": participants_count,
            "answers_count": len(rows),
            "with_board_count": with_board,
        })
    return jsonify({
        "session": {"id": sess.id, "title": sess.title, "locale": sess.locale},
        "totals": totals,
        "groups": groups_view,
    })


@bp_agile_kanban.post("/groups/<int:group_id>/reset")
@jwt_required()
def group_reset(group_id: int):
    uid = _uid()
    g = (
        AgileTrainingGroup.query
        .join(AgileTrainingSession, AgileTrainingSession.id == AgileTrainingGroup.session_id)
        .filter(AgileTrainingGroup.id == group_id, AgileTrainingSession.owner_user_id == uid)
        .first()
    )
    if not g:
        return jsonify({"error": "Not found"}), 404
    AgileTrainingKanbanAnswer.query.filter_by(group_id=g.id).delete()
    db.session.commit()
    return jsonify({"reset": True})
