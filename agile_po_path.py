"""Backend тренинга «Путь Product Owner»: JTBD → Value Proposition → Market Fit → Lean Canvas.

Пошаговый воркшоп с фасилитатором. Использует существующий каркас
AgileTrainingSession / Group / Participant, ответ хранится одной записью
(`AgileTrainingPoPathAnswer`) с целиком JSON-стейтом из 4 этапов и их
статусов. Каждый этап проходит цикл draft → submitted → approved (или
needs_revision). Пока этап не approved, следующий заблокирован.

API под префиксом `/api/agile-training/po-path`:
- public / participant:
    GET  /content?locale=ru|en
    GET  /g/<slug>/state?participant_token=...
    POST /g/<slug>/answer        (autosave per-stage data, confidence)
    POST /g/<slug>/submit        (stage → submitted)
    POST /g/<slug>/return        (вернуть участника к более раннему этапу — этот и все после сбрасываются в draft)
    POST /g/<slug>/ai-assist     (improve / formulate / generic helper)
    POST /g/<slug>/ai-uncomfortable (3-5 «неудобных» вопросов для market fit)
- facilitator (JWT, владелец сессии):
    GET  /groups/<group_id>/participants
    GET  /groups/<group_id>/participants/<participant_id>
    POST /groups/<group_id>/participants/<participant_id>/review
    POST /groups/<group_id>/participants/<participant_id>/comment
    POST /groups/<group_id>/reset
    GET  /groups/<group_id>/results
"""

from __future__ import annotations

import json
import os
import secrets
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database import db
from models import (
    AgileTrainingGroup,
    AgileTrainingParticipant,
    AgileTrainingPoPathAnswer,
    AgileTrainingSession,
)


bp_agile_po_path = Blueprint(
    "agile_po_path", __name__, url_prefix="/api/agile-training/po-path"
)


# --------------------------- constants ---------------------------

STAGES: Tuple[str, ...] = ("jtbd", "value", "fit", "canvas")
STAGE_SET = set(STAGES)
NEXT_STAGE: Dict[str, str] = {"jtbd": "value", "value": "fit", "fit": "canvas", "canvas": "done"}

STATUS_DRAFT = "draft"
STATUS_SUBMITTED = "submitted"
STATUS_IN_REVIEW = "in_review"
STATUS_APPROVED = "approved"
STATUS_NEEDS_REVISION = "needs_revision"
ALL_STATUSES = {
    STATUS_DRAFT,
    STATUS_SUBMITTED,
    STATUS_IN_REVIEW,
    STATUS_APPROVED,
    STATUS_NEEDS_REVISION,
}

AI_CALLS_LIMIT_PER_PARTICIPANT = 30
AI_PROMPT_LIMIT_CHARS = 2000
FIELD_TEXT_LIMIT = 3000
COMMENT_LIMIT = 2000


# --------------------------- content (mostly UI-only; stage definitions) ---------------------------


# Структура полей по этапам — используется и в API (валидация), и
# отдаётся клиенту, чтобы не дублировать список полей в Vue. Длины
# ограничиваются на уровне API (FIELD_TEXT_LIMIT).
STAGE_FIELDS: Dict[str, List[str]] = {
    "jtbd": [
        "job_statement",
        "trigger",
        "context",
        "frequency",
        "motivation",
        "outcomes",
        "current_solution",
        "barriers",
        "fears",
        "success_criteria",
    ],
    # На value-этапе pains и gains — списки объектов (см. _clean_value_data).
    # Здесь они перечислены в "field-список", но фронт рендерит их особым UI.
    "value": [
        "product",
        "pains",
        "gains",
    ],
    "fit": [
        "customer",
        "why_choose",
        "alternatives",
        "usage_context",
    ],
    "canvas": [
        "problem",
        "segments",
        "value_prop",
        "solution",
        "channels",
        "revenue",
        "costs",
        "metrics",
        "unfair_advantage",
        "early_adopters",
    ],
}


# Layout канваса по этапам: row,col,colspan,rowspan для CSS grid.
# Используется фронтом, чтобы рендерить форму как «канвас», а не стек.
# Сетка для всех этапов — 6 колонок (адаптивно сжимается на мобилках).
STAGE_LAYOUT: Dict[str, Dict[str, Dict[str, int]]] = {
    "jtbd": {
        "job_statement":    {"row": 1, "col": 1, "colspan": 4, "rowspan": 1, "accent": "primary"},
        "trigger":          {"row": 1, "col": 5, "colspan": 2, "rowspan": 1},
        "context":          {"row": 2, "col": 1, "colspan": 3, "rowspan": 1},
        "frequency":        {"row": 2, "col": 4, "colspan": 3, "rowspan": 1},
        "motivation":       {"row": 3, "col": 1, "colspan": 2, "rowspan": 1, "accent": "warm"},
        "outcomes":         {"row": 3, "col": 3, "colspan": 2, "rowspan": 1, "accent": "ok"},
        "current_solution": {"row": 3, "col": 5, "colspan": 2, "rowspan": 1},
        "barriers":         {"row": 4, "col": 1, "colspan": 2, "rowspan": 1, "accent": "danger"},
        "fears":            {"row": 4, "col": 3, "colspan": 2, "rowspan": 1, "accent": "danger"},
        "success_criteria": {"row": 4, "col": 5, "colspan": 2, "rowspan": 1, "accent": "ok"},
    },
    # Layout для value не используется (фронт рендерит свою UI), но оставляем
    # accent для блоков, чтобы при желании можно было визуально различить.
    "value": {
        "product": {"row": 1, "col": 1, "colspan": 6, "rowspan": 1, "accent": "primary"},
        "pains":   {"row": 2, "col": 1, "colspan": 3, "rowspan": 1, "accent": "danger"},
        "gains":   {"row": 2, "col": 4, "colspan": 3, "rowspan": 1, "accent": "ok"},
    },
    "fit": {
        "customer":      {"row": 1, "col": 1, "colspan": 6, "rowspan": 1, "accent": "primary"},
        "why_choose":    {"row": 2, "col": 1, "colspan": 3, "rowspan": 1, "accent": "ok"},
        "alternatives":  {"row": 2, "col": 4, "colspan": 3, "rowspan": 1},
        "usage_context": {"row": 3, "col": 1, "colspan": 6, "rowspan": 1, "accent": "warm"},
    },
    "canvas": {
        "problem":          {"row": 1, "col": 1, "colspan": 2, "rowspan": 2, "accent": "danger"},
        "solution":         {"row": 1, "col": 3, "colspan": 1, "rowspan": 1, "accent": "warm"},
        "metrics":          {"row": 2, "col": 3, "colspan": 1, "rowspan": 1},
        "value_prop":       {"row": 1, "col": 4, "colspan": 1, "rowspan": 2, "accent": "primary"},
        "unfair_advantage": {"row": 1, "col": 5, "colspan": 1, "rowspan": 1, "accent": "ok"},
        "channels":         {"row": 2, "col": 5, "colspan": 1, "rowspan": 1},
        "segments":         {"row": 1, "col": 6, "colspan": 1, "rowspan": 2, "accent": "ok"},
        "early_adopters":   {"row": 3, "col": 1, "colspan": 2, "rowspan": 1},
        "costs":            {"row": 3, "col": 3, "colspan": 2, "rowspan": 1, "accent": "danger"},
        "revenue":          {"row": 3, "col": 5, "colspan": 2, "rowspan": 1, "accent": "ok"},
    },
}


CONTENT = {
    "ru": {
        "title": "Путь Product Owner",
        "subtitle": "От «зачем людям наш продукт» до Lean Canvas",
        "intro": (
            "Это пошаговый воркшоп для будущих и действующих Product Owner. "
            "Возьмите свою идею (или одну из подсказок) и проведите её через 4 этапа: "
            "JTBD → Value Proposition → Market Fit → Lean Canvas. "
            "После каждого этапа вы отправляете работу фасилитатору, обсуждаете её с группой и только потом идёте дальше."
        ),
        "tips": [
            "Можно вернуться и переписать любой пройденный этап — но он снова уйдёт фасилитатору.",
            "Ничего не пропадёт: данные сохраняются автоматически и подтянутся, даже если обновить страницу.",
            "AI-помощник умеет переформулировать, задавать уточняющие и неудобные вопросы — но не оценивает.",
        ],
        "idea_examples": [
            "Маркетплейс домашних поваров для вечно занятых родителей",
            "Сервис подбора репетитора по подростку, а не по предмету",
            "Приложение, которое договаривается с банками за пенсионера",
            "Чат-бот, который превращает голосовые в TODO для small business",
            "Платформа коворкингов в маленьких городах для удалёнщиков",
        ],
        "stages": {
            "jtbd": {
                "title": "Этап 1 · Jobs To Be Done",
                "context": "Сначала разберёмся, какую «работу» человек нанимает наш продукт сделать.",
                "explainer": (
                    "JTBD = Когда [ситуация], я хочу [действие], чтобы [результат]. "
                    "Не привязывайтесь к решению — описывайте задачу человека."
                ),
                "fields": {
                    "job_statement": {
                        "label": "Job Statement",
                        "hint": "«Когда [ситуация], я хочу [действие], чтобы [результат]»",
                        "placeholder": "Когда у меня в семье болеет ребёнок, я хочу за 5 минут понять, к какому врачу идти, чтобы не терять день в гугле и звонках",
                    },
                    "trigger": {
                        "label": "Триггер",
                        "hint": "Спусковой крючок: что именно запускает эту работу прямо сейчас?",
                        "placeholder": "Ребёнок проснулся ночью с температурой 38,5 → паника родителей.",
                    },
                    "context": {
                        "label": "Контекст",
                        "hint": "Где, когда и при каких обстоятельствах работа возникает.",
                        "placeholder": "Будний вечер, оба родителя устали, поликлиника уже закрыта, симптомы непонятные.",
                    },
                    "frequency": {
                        "label": "Частота",
                        "hint": "Как часто человек сталкивается с этой работой? (раз в день/неделю/год)",
                        "placeholder": "5–8 раз в год; в сезон ОРВИ — почти каждые 2 недели.",
                    },
                    "motivation": {
                        "label": "Мотивация",
                        "hint": "Что человек на самом деле хочет — функционально, эмоционально, социально.",
                        "placeholder": "Спокойствие («сделал всё что мог»), быстрое решение, ощущение контроля.",
                    },
                    "outcomes": {
                        "label": "Желаемый исход",
                        "hint": "Что должно произойти, чтобы работа считалась выполненной хорошо.",
                        "placeholder": "За 5 минут получает чёткий план: «вызвать скорую / ждать утра / идти к ЛОРу» без сомнений.",
                    },
                    "current_solution": {
                        "label": "Как решает сейчас",
                        "hint": "Чем человек закрывает эту работу СЕГОДНЯ, без вашего продукта.",
                        "placeholder": "Гуглит симптомы 30 минут, потом звонит знакомой педиатру, потом всё равно вызывает скорую «на всякий».",
                    },
                    "barriers": {
                        "label": "Барьеры",
                        "hint": "Что мешает решить задачу прямо сейчас.",
                        "placeholder": "Google пугает; у знакомых врачей нет времени; платные приложения требуют подписки заранее.",
                    },
                    "fears": {
                        "label": "Страхи",
                        "hint": "Чего человек боится, выбирая решение.",
                        "placeholder": "Что нарвётся на «врача-консультанта», который ничего конкретного не скажет и заберёт деньги.",
                    },
                    "success_criteria": {
                        "label": "Критерии успеха",
                        "hint": "Как человек поймёт, что задача решена? Что он почувствует/увидит?",
                        "placeholder": "Ребёнок к утру стабилен; родитель чувствует «я сделал верно»; не пришлось тратить день на гугл.",
                    },
                },
            },
            "value": {
                "title": "Этап 2 · Value Proposition",
                "context": "Теперь покажем, как наш продукт решает эту задачу.",
                "explainer": (
                    "Идея: «Наш продукт помогает [сегмент] выполнить [job], "
                    "снимая [pains] и давая [gains]». Каждую боль и каждую выгоду опишите ОТДЕЛЬНО — "
                    "и для каждой сразу укажите, как продукт её закрывает или создаёт. Опирайтесь на JTBD из этапа 1 — он отображается рядом."
                ),
                "fields": {
                    "product": {
                        "label": "Продукт",
                        "hint": "Что мы вообще делаем — одним абзацем, без лишних деталей.",
                        "placeholder": "Чат-бот, который по симптомам ребёнка задаёт 5–7 уточняющих вопросов и в конце даёт маршрут с конкретным следующим шагом.",
                    },
                    "pains": {
                        "label": "Боли клиента",
                        "hint": (
                            "Каждая боль — отдельная карточка. Сначала формулируем саму боль, "
                            "потом — как именно продукт её снимает (pain reliever). 3–5 болей сильнее, чем 10."
                        ),
                        "placeholder_text": "Например: «Гуглит симптомы по 30 минут и не получает понятного ответа.»",
                        "placeholder_action": "Например: «Бот за 90 секунд проводит по чек-листу симптомов и выдаёт чёткий следующий шаг.»",
                        "label_text": "Описание боли",
                        "label_action": "Болеутоляющее (как продукт снимает)",
                        "add_label": "+ добавить боль",
                        "empty": "Пока не указано ни одной боли. Добавьте 3–5 — и для каждой опишите, как продукт её снимет.",
                    },
                    "gains": {
                        "label": "Выгоды клиента",
                        "hint": (
                            "Каждая выгода — отдельная карточка. Включая эмоции и статус. "
                            "Сразу укажите, как продукт эту выгоду создаёт (gain creator). Без маркетинговых штампов."
                        ),
                        "placeholder_text": "Например: «За 3 минуты — план действий и спокойствие.»",
                        "placeholder_action": "Например: «Бот сразу даёт следующий шаг: вызвать скорую / ждать утра / идти к ЛОРу.»",
                        "label_text": "Описание выгоды",
                        "label_action": "Создатель выгоды (как продукт её даёт)",
                        "add_label": "+ добавить выгоду",
                        "empty": "Пока не указано ни одной выгоды. Добавьте 3–5 и для каждой опишите, как именно продукт её создаёт.",
                    },
                },
            },
            "fit": {
                "title": "Этап 3 · Проверка гипотезы (Market Fit)",
                "context": "Прежде чем строить — проверим, есть ли вообще смысл это делать.",
                "explainer": (
                    "Опишите гипотезу о клиенте максимально конкретно. "
                    "Затем AI задаст 3–5 «неудобных» вопросов — на них стоит ответить честно, даже если ответы пока слабые."
                ),
                "fields": {
                    "customer": {
                        "label": "Кто клиент",
                        "hint": "Конкретный человек, не «все родители»: возраст, ситуация, доход, поведение.",
                        "placeholder": "Мама 30–42, ребёнок 0–10 лет, города-миллионники, 2 раза в год покупает онлайн-консультации.",
                    },
                    "why_choose": {
                        "label": "Почему он выберет вас",
                        "hint": "Реальная причина — не «потому что лучше».",
                        "placeholder": "Потому что в отличие от Skype-врача мы даём не диалог, а готовый маршрут на 30 секунд.",
                    },
                    "alternatives": {
                        "label": "Альтернативы",
                        "hint": "Чем сейчас закрывают эту job — включая «ничего не делать» и «спросить у мамы».",
                        "placeholder": "Гугл, чат с подругой-врачом, форум baby.ru, app «СберЗдоровье», ничего не делать.",
                    },
                    "usage_context": {
                        "label": "Когда будет использовать",
                        "hint": "В какой момент жизни триггерится использование? Что за «спусковой крючок»?",
                        "placeholder": "Ребёнок проснулся ночью с температурой → паника → приложение даёт ответ за 3 минуты.",
                    },
                },
                "ai_questions_intro": (
                    "Запросите у AI 3–5 неудобных вопросов и ответьте на каждый. "
                    "Цель — не «ответить правильно», а заметить слабые места гипотезы."
                ),
                "ai_starter_questions": [
                    "А если клиент не будет за это платить — что вы поменяете?",
                    "Чем вы лучше существующего решения, которым уже пользуется ваш клиент?",
                    "Сколько таких клиентов вы реально найдёте за месяц и где?",
                    "Что должно произойти в жизни клиента, чтобы он впервые открыл ваш продукт?",
                    "Какой результат он должен увидеть в первые 60 секунд, чтобы вернуться?",
                ],
            },
            "canvas": {
                "title": "Этап 4 · Lean Canvas",
                "context": "Соберём идею как бизнес. Поля проблемы и ценностного предложения мы автоматически предложим из предыдущих этапов — поправьте под себя.",
                "explainer": (
                    "Lean Canvas — 9 блоков на одном листе. Не пытайтесь заполнить всё идеально с первого раза, "
                    "цель — увидеть всю картину и обсудить её с фасилитатором."
                ),
                "fields": {
                    "problem": {
                        "label": "Проблема",
                        "hint": "Топ-3 проблемы клиента (мы знаем их из JTBD).",
                        "placeholder": "1. Долгий гугл; 2. Страх ошибиться; 3. Не понятно, к кому идти.",
                    },
                    "segments": {
                        "label": "Сегменты клиентов",
                        "hint": "Кому продаём в первую очередь.",
                        "placeholder": "Городские мамы 30–42, дети 0–10.",
                    },
                    "early_adopters": {
                        "label": "Early Adopters",
                        "hint": "Кто первым купит, даже если у нас всё некрасиво?",
                        "placeholder": "Мамы из родительских ТГ-чатов в Москве и Питере.",
                    },
                    "value_prop": {
                        "label": "Уникальное ценностное предложение",
                        "hint": "Одной строкой. Лучше с цифрой.",
                        "placeholder": "За 3 минуты — план действий с ребёнком, без блужданий по форумам.",
                    },
                    "solution": {
                        "label": "Решение",
                        "hint": "Топ-3 фичи, которые закрывают проблемы.",
                        "placeholder": "Чек-лист по симптомам · триаж «ждать/к врачу/скорая» · подбор клиники онлайн.",
                    },
                    "channels": {
                        "label": "Каналы",
                        "hint": "Через какие каналы продукт встретится с клиентом.",
                        "placeholder": "ТГ-каналы для родителей, контентный SEO, партнёрство с педиатрами.",
                    },
                    "revenue": {
                        "label": "Источники дохода",
                        "hint": "Как зарабатываем.",
                        "placeholder": "Подписка 290 ₽/мес + комиссия с консультаций партнёров.",
                    },
                    "costs": {
                        "label": "Структура затрат",
                        "hint": "Главные статьи расходов.",
                        "placeholder": "Команда (4 человека), AI-провайдер, медэксперт-консультант, маркетинг.",
                    },
                    "metrics": {
                        "label": "Ключевые метрики",
                        "hint": "Что будем мерить, чтобы понимать — растём ли.",
                        "placeholder": "DAU мам с детьми <10 лет, % дошедших до плана, повторные сессии за 30 дней.",
                    },
                    "unfair_advantage": {
                        "label": "Несправедливое преимущество",
                        "hint": "То, что нельзя быстро скопировать.",
                        "placeholder": "Партнёрство с НИИ педиатрии и большая база реальных диалогов.",
                    },
                },
                "auto_prefill_note": "Поля «Проблема» и «Уникальное ценностное предложение» можно автоматически взять из этапов 1–2. Можно отказаться от подсказки и написать с нуля.",
            },
        },
        "summary": {
            "title": "Финал · Полная картина",
            "subtitle": "Соберите всё с одного экрана и обсудите/распечатайте/поделитесь.",
        },
        "facilitator": {
            "approve": "Одобрить этап",
            "reject": "Вернуть на доработку",
            "comment_placeholder": "Что обсудили на группе, что стоит улучшить?",
        },
        "status_labels": {
            STATUS_DRAFT: "Черновик",
            STATUS_SUBMITTED: "На проверке",
            STATUS_IN_REVIEW: "На обсуждении",
            STATUS_APPROVED: "Одобрено",
            STATUS_NEEDS_REVISION: "На доработке",
        },
    },
    "en": {
        "title": "Product Owner Path",
        "subtitle": "From “why people need this” to a Lean Canvas",
        "intro": (
            "A step-by-step workshop for future and current Product Owners. "
            "Take your idea (or pick one from suggestions) and walk it through 4 stages: "
            "JTBD → Value Proposition → Market Fit → Lean Canvas. "
            "After each stage you submit it to the facilitator, discuss with the group, and only then move on."
        ),
        "tips": [
            "You can come back and rewrite any approved stage — but it will be sent for review again.",
            "Nothing gets lost: data is saved automatically and survives a page refresh.",
            "The AI helper can rephrase text, ask clarifying and uncomfortable questions, but never grades you.",
        ],
        "idea_examples": [
            "A marketplace of home cooks for busy parents",
            "Tutor matching by the teen, not by the subject",
            "An app that talks to banks for your retired parents",
            "A bot that turns voice notes into TODOs for small business owners",
            "A coworking platform for remote workers in small towns",
        ],
        "stages": {
            "jtbd": {
                "title": "Stage 1 · Jobs To Be Done",
                "context": "First, what “job” does a person hire your product to do?",
                "explainer": (
                    "JTBD = When [situation], I want [action], so that [outcome]. "
                    "Avoid solutions — describe the person’s job."
                ),
                "fields": {
                    "job_statement": {
                        "label": "Job Statement",
                        "hint": "“When [situation], I want [action], so that [outcome]”",
                        "placeholder": "When my child gets sick at night, I want to know in 5 minutes which doctor to go to, so I don’t spend the day googling.",
                    },
                    "trigger": {
                        "label": "Trigger",
                        "hint": "What exactly fires this job RIGHT NOW?",
                        "placeholder": "Child wakes up at night with 38.5°C fever → parents panic.",
                    },
                    "context": {
                        "label": "Context",
                        "hint": "Where and when this job pops up.",
                        "placeholder": "Weeknight, both parents tired, the clinic is closed, symptoms unclear.",
                    },
                    "frequency": {
                        "label": "Frequency",
                        "hint": "How often does the person face this job? (per day / week / year)",
                        "placeholder": "5–8 times a year; during flu season — almost every 2 weeks.",
                    },
                    "motivation": {
                        "label": "Motivation",
                        "hint": "What do they actually want — functional, emotional, social.",
                        "placeholder": "Calm (“I did everything I could”), a quick answer, sense of control.",
                    },
                    "outcomes": {
                        "label": "Desired outcome",
                        "hint": "What has to happen for this job to be done well.",
                        "placeholder": "Within 5 minutes — a clear plan: call ER / wait until morning / see ENT, no doubt.",
                    },
                    "current_solution": {
                        "label": "How they solve it today",
                        "hint": "How they close this job TODAY, without your product.",
                        "placeholder": "Googles symptoms for 30 min, calls a doctor friend, ends up calling ER “just in case”.",
                    },
                    "barriers": {
                        "label": "Barriers",
                        "hint": "What blocks them right now.",
                        "placeholder": "Google gives scary diagnoses, a doctor friend has no time, paid apps require a subscription.",
                    },
                    "fears": {
                        "label": "Fears",
                        "hint": "What are they afraid of when choosing a solution.",
                        "placeholder": "Hitting a “consultant doctor” that says nothing concrete and takes the money.",
                    },
                    "success_criteria": {
                        "label": "Success criteria",
                        "hint": "How will they know the job is done? What will they feel / see?",
                        "placeholder": "Child stable by morning; parent feels “I did the right thing”; no day lost to googling.",
                    },
                },
            },
            "value": {
                "title": "Stage 2 · Value Proposition",
                "context": "Now show how the product solves this job.",
                "explainer": (
                    "Idea: “Our product helps [segment] do [job], removing [pains] and giving [gains]”. "
                    "Describe each pain and each gain as a SEPARATE card — and right next to it write down how the product addresses it. "
                    "Lean on the JTBD from stage 1 — it stays visible next to you."
                ),
                "fields": {
                    "product": {
                        "label": "Product",
                        "hint": "What we’re actually building, in one paragraph.",
                        "placeholder": "A bot that asks 5–7 clarifying questions about symptoms and gives a clear next step.",
                    },
                    "pains": {
                        "label": "Customer pains",
                        "hint": (
                            "Each pain is its own card. First write the pain, then — how the product relieves it (pain reliever). "
                            "3–5 sharp pains beat 10 fuzzy ones."
                        ),
                        "placeholder_text": "E.g. “Spends 30 minutes googling and still gets no clear answer.”",
                        "placeholder_action": "E.g. “Bot walks them through a 90-second symptom checklist and gives a single next step.”",
                        "label_text": "Pain description",
                        "label_action": "Pain reliever (how the product solves it)",
                        "add_label": "+ add pain",
                        "empty": "No pains yet. Add 3–5 — for each one, describe how the product relieves it.",
                    },
                    "gains": {
                        "label": "Customer gains",
                        "hint": (
                            "Each gain is its own card — including emotions and status. "
                            "Right after the gain, describe how the product creates it (gain creator). No marketing fluff."
                        ),
                        "placeholder_text": "E.g. “In 3 minutes — a plan and calm.”",
                        "placeholder_action": "E.g. “Bot returns the next step: call ER / wait until morning / see ENT.”",
                        "label_text": "Gain description",
                        "label_action": "Gain creator (how the product gives it)",
                        "add_label": "+ add gain",
                        "empty": "No gains yet. Add 3–5 and describe how the product creates each one.",
                    },
                },
            },
            "fit": {
                "title": "Stage 3 · Market Fit hypothesis",
                "context": "Before we build — let’s check if this idea has a chance.",
                "explainer": (
                    "Describe the customer hypothesis very concretely. "
                    "Then ask AI for 3–5 uncomfortable questions and answer each — even if the answer feels weak right now."
                ),
                "fields": {
                    "customer": {
                        "label": "Who is the customer",
                        "hint": "Be concrete: age, situation, income, behavior — not “all parents”.",
                        "placeholder": "Moms 30–42, kids 0–10, big cities, buys 2 online consultations a year.",
                    },
                    "why_choose": {
                        "label": "Why will they choose you",
                        "hint": "The real reason — not “because we’re better”.",
                        "placeholder": "Unlike a Skype call with a doctor, we give a 30-second action plan, not a discussion.",
                    },
                    "alternatives": {
                        "label": "Alternatives",
                        "hint": "What do they currently use — including “do nothing” and “ask mom”.",
                        "placeholder": "Google, a friend who is a doctor, parenting forum, a clinic app, doing nothing.",
                    },
                    "usage_context": {
                        "label": "When they will use it",
                        "hint": "What life moment triggers usage?",
                        "placeholder": "Child wakes up with fever at night → panic → app gives an answer in 3 minutes.",
                    },
                },
                "ai_questions_intro": (
                    "Ask AI for 3–5 uncomfortable questions and answer each. "
                    "Goal: not “correct answers”, but spotting weak parts of your hypothesis."
                ),
                "ai_starter_questions": [
                    "What if the customer won’t pay for this — what would you change?",
                    "Why are you better than what they already use?",
                    "How many such customers can you really find in a month, and where?",
                    "What must happen in their life to open your product the very first time?",
                    "What outcome do they need to see in the first 60 seconds to come back?",
                ],
            },
            "canvas": {
                "title": "Stage 4 · Lean Canvas",
                "context": "Now we put the idea together as a business. The Problem and Unique Value Prop blocks are pre-filled from earlier stages — adjust as needed.",
                "explainer": (
                    "Lean Canvas is 9 blocks on a single sheet. Don’t aim for perfect on the first pass — "
                    "the goal is to see the whole picture and discuss it."
                ),
                "fields": {
                    "problem": {
                        "label": "Problem",
                        "hint": "Top 3 customer problems.",
                        "placeholder": "1. Long googling; 2. Fear of being wrong; 3. Don’t know who to talk to.",
                    },
                    "segments": {
                        "label": "Customer Segments",
                        "hint": "Who do we sell to first.",
                        "placeholder": "Urban moms 30–42, kids 0–10.",
                    },
                    "early_adopters": {
                        "label": "Early Adopters",
                        "hint": "Who buys even if everything is rough.",
                        "placeholder": "Moms in parenting Telegram chats in Moscow / SPb.",
                    },
                    "value_prop": {
                        "label": "Unique Value Proposition",
                        "hint": "One line, ideally with a number.",
                        "placeholder": "A 3-minute action plan for your sick child, no more forum hopping.",
                    },
                    "solution": {
                        "label": "Solution",
                        "hint": "Top 3 features that solve the problems.",
                        "placeholder": "Symptom checklist · triage (wait/doctor/ER) · clinic match.",
                    },
                    "channels": {
                        "label": "Channels",
                        "hint": "How will the product meet the customer.",
                        "placeholder": "Parents Telegram channels, content SEO, partnerships with pediatricians.",
                    },
                    "revenue": {
                        "label": "Revenue Streams",
                        "hint": "How we make money.",
                        "placeholder": "Subscription $4/mo + commission on partner consultations.",
                    },
                    "costs": {
                        "label": "Cost Structure",
                        "hint": "Main expenses.",
                        "placeholder": "Team of 4, AI provider, medical advisor, marketing.",
                    },
                    "metrics": {
                        "label": "Key Metrics",
                        "hint": "What we track to know we’re growing.",
                        "placeholder": "DAU of moms with kids <10, % reaching the plan, repeat sessions in 30 days.",
                    },
                    "unfair_advantage": {
                        "label": "Unfair Advantage",
                        "hint": "What can’t be easily copied.",
                        "placeholder": "Partnership with a pediatric institute and a corpus of real dialogues.",
                    },
                },
                "auto_prefill_note": "“Problem” and “Unique Value Proposition” can be auto-filled from stages 1–2. You can also start from scratch.",
            },
        },
        "summary": {
            "title": "Wrap-up · Full picture",
            "subtitle": "Everything on one screen — discuss, print or share.",
        },
        "facilitator": {
            "approve": "Approve stage",
            "reject": "Send back for revision",
            "comment_placeholder": "What did the group discuss, what to improve?",
        },
        "status_labels": {
            STATUS_DRAFT: "Draft",
            STATUS_SUBMITTED: "In review",
            STATUS_IN_REVIEW: "Under discussion",
            STATUS_APPROVED: "Approved",
            STATUS_NEEDS_REVISION: "Needs revision",
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


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _safe_json_load(raw: Optional[str]) -> Dict:
    if not raw:
        return {}
    try:
        v = json.loads(raw)
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def _clamp_text(value, limit: int = FIELD_TEXT_LIMIT) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    return s[:limit]


def _empty_stage_state() -> Dict:
    return {
        "status": STATUS_DRAFT,
        "data": {},
        "confidence": None,
        "comments": [],
        "submitted_at": None,
        "approved_at": None,
        "review_round": 0,
    }


def _ensure_state_shape(state: Dict) -> Dict:
    """Гарантирует, что в JSON есть current_stage и все 4 этапа."""
    if not isinstance(state, dict):
        state = {}
    cur = state.get("current_stage")
    if cur not in STAGE_SET and cur != "done":
        state["current_stage"] = "jtbd"
    stages = state.get("stages")
    if not isinstance(stages, dict):
        stages = {}
    for k in STAGES:
        st = stages.get(k)
        if not isinstance(st, dict):
            st = _empty_stage_state()
        else:
            st.setdefault("status", STATUS_DRAFT)
            if st["status"] not in ALL_STATUSES:
                st["status"] = STATUS_DRAFT
            if not isinstance(st.get("data"), dict):
                st["data"] = {}
            if not isinstance(st.get("comments"), list):
                st["comments"] = []
            st.setdefault("confidence", None)
            st.setdefault("submitted_at", None)
            st.setdefault("approved_at", None)
            st.setdefault("review_round", 0)
        if k == "value":
            _migrate_value_data_inplace(st.get("data") or {})
        stages[k] = st
    state["stages"] = stages
    if "ai_history" not in state or not isinstance(state["ai_history"], list):
        state["ai_history"] = []
    if "ai_calls" not in state:
        state["ai_calls"] = 0
    return state


def _recompute_progress(state: Dict) -> None:
    """Пересчитывает current_stage и общий счётчик. После approve — следующий этап."""
    state = _ensure_state_shape(state)
    cur = "done"
    completed = 0
    for k in STAGES:
        if state["stages"][k]["status"] == STATUS_APPROVED:
            completed += 1
            continue
        cur = k
        break
    state["current_stage"] = cur
    state["_stages_completed"] = completed


def _stage_field_keys(stage: str) -> List[str]:
    return STAGE_FIELDS.get(stage, [])


# ---------- value-stage list items (pains / gains) ----------


VALUE_LIST_LIMIT = 12  # сколько максимум болей/выгод храним


def _new_item_id() -> str:
    return secrets.token_hex(4)


_SEVERITY_LEVELS = {"low", "mid", "high"}


def _clean_value_items(raw, action_key: str) -> List[Dict]:
    """Нормализует список pains/gains.

    Принимает либо строку (legacy) — превратится в один элемент,
    либо список объектов вида {id, text, reliever|creator,
    severity|importance}.
    """
    weight_key = "severity" if action_key == "reliever" else "importance"
    default_weight = "mid"
    if isinstance(raw, str):
        text = _clamp_text(raw)
        if not text:
            return []
        return [{"id": _new_item_id(), "text": text, action_key: "", weight_key: default_weight}]
    if not isinstance(raw, list):
        return []
    out: List[Dict] = []
    for item in raw[:VALUE_LIST_LIMIT]:
        if not isinstance(item, dict):
            continue
        text = _clamp_text(item.get("text"))
        action = _clamp_text(item.get(action_key)) or ""
        if not text and not action:
            continue
        item_id = str(item.get("id") or "").strip()[:32] or _new_item_id()
        weight_raw = str(item.get(weight_key) or "").strip().lower()
        weight = weight_raw if weight_raw in _SEVERITY_LEVELS else default_weight
        out.append({
            "id": item_id,
            "text": text or "",
            action_key: action or "",
            weight_key: weight,
        })
    return out


def _clean_value_data(raw: Dict) -> Dict:
    out: Dict = {}
    if not isinstance(raw, dict):
        return out
    product = _clamp_text(raw.get("product"))
    if product is not None:
        out["product"] = product
    out["pains"] = _clean_value_items(raw.get("pains"), action_key="reliever")
    out["gains"] = _clean_value_items(raw.get("gains"), action_key="creator")
    return out


def _migrate_value_data_inplace(value_data: Dict) -> None:
    """Миграция старого формата (pains: str, pain_relievers: str) в списки."""
    if not isinstance(value_data, dict):
        return
    legacy_relievers = value_data.pop("pain_relievers", None) if isinstance(
        value_data.get("pain_relievers"), str
    ) else None
    pains = value_data.get("pains")
    if isinstance(pains, str):
        text = pains.strip()
        if text:
            new_pains = [{
                "id": _new_item_id(),
                "text": text[:FIELD_TEXT_LIMIT],
                "reliever": (legacy_relievers or "").strip()[:FIELD_TEXT_LIMIT],
                "severity": "mid",
            }]
        else:
            new_pains = []
        value_data["pains"] = new_pains
    elif isinstance(pains, list):
        value_data["pains"] = _clean_value_items(pains, action_key="reliever")
    else:
        value_data["pains"] = []
    gains = value_data.get("gains")
    if isinstance(gains, str):
        text = gains.strip()
        value_data["gains"] = [{
            "id": _new_item_id(),
            "text": text[:FIELD_TEXT_LIMIT],
            "creator": "",
            "importance": "mid",
        }] if text else []
    elif isinstance(gains, list):
        value_data["gains"] = _clean_value_items(gains, action_key="creator")
    else:
        value_data["gains"] = []
    if "pain_relievers" in value_data:
        value_data.pop("pain_relievers", None)


def _clean_stage_data(stage: str, raw: Dict) -> Dict:
    if stage == "value":
        return _clean_value_data(raw or {})
    out: Dict = {}
    if not isinstance(raw, dict):
        return out
    for key in _stage_field_keys(stage):
        v = raw.get(key)
        cleaned = _clamp_text(v)
        if cleaned is not None:
            out[key] = cleaned
    return out


def _stage_has_meaningful_content(stage: str, data: Dict) -> bool:
    """Готов ли этап к отправке — хотя бы 1 не-пустое ключевое поле."""
    if not isinstance(data, dict):
        return False
    if stage == "value":
        if (data.get("product") or "").strip():
            return True
        for it in (data.get("pains") or []):
            if isinstance(it, dict) and ((it.get("text") or "").strip() or (it.get("reliever") or "").strip()):
                return True
        for it in (data.get("gains") or []):
            if isinstance(it, dict) and ((it.get("text") or "").strip() or (it.get("creator") or "").strip()):
                return True
        return False
    for key in _stage_field_keys(stage):
        if (data.get(key) or "").strip():
            return True
    return False


def _flatten_value_for_text(value_data: Dict) -> str:
    """Превращает списки pains/gains в плоский текст для AI-контекста."""
    if not isinstance(value_data, dict):
        return ""
    parts: List[str] = []
    product = (value_data.get("product") or "").strip()
    if product:
        parts.append(f"product: {product[:300]}")
    for i, it in enumerate(value_data.get("pains") or [], 1):
        if not isinstance(it, dict):
            continue
        t = (it.get("text") or "").strip()
        r = (it.get("reliever") or "").strip()
        sev = (it.get("severity") or "mid").strip().lower()
        if not t and not r:
            continue
        parts.append(f"pain {i} [{sev}]: {t[:200]} | reliever: {r[:200]}")
    for i, it in enumerate(value_data.get("gains") or [], 1):
        if not isinstance(it, dict):
            continue
        t = (it.get("text") or "").strip()
        c = (it.get("creator") or "").strip()
        imp = (it.get("importance") or "mid").strip().lower()
        if not t and not c:
            continue
        parts.append(f"gain {i} [{imp}]: {t[:200]} | creator: {c[:200]}")
    return "\n".join(parts)


def _serialize_stage(state: Dict, stage: str) -> Dict:
    stages = state.get("stages") or {}
    st = stages.get(stage) or _empty_stage_state()
    out = {
        "stage": stage,
        "status": st.get("status") or STATUS_DRAFT,
        "data": st.get("data") or {},
        "confidence": st.get("confidence"),
        "comments": st.get("comments") or [],
        "submitted_at": st.get("submitted_at"),
        "approved_at": st.get("approved_at"),
        "review_round": int(st.get("review_round") or 0),
    }
    if stage == "fit":
        out["ai_questions"] = st.get("ai_questions") or []
    return out


def _serialize_answer(a: AgileTrainingPoPathAnswer) -> Dict:
    state = _ensure_state_shape(_safe_json_load(a.data_json))
    _recompute_progress(state)
    return {
        "id": a.id,
        "current_stage": state.get("current_stage"),
        "stages_completed": state.get("_stages_completed", 0),
        "stages": {k: _serialize_stage(state, k) for k in STAGES},
        "ai_calls": int(a.ai_calls or 0),
        "ai_calls_remaining": max(0, AI_CALLS_LIMIT_PER_PARTICIPANT - int(a.ai_calls or 0)),
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


def _persist_answer(a: AgileTrainingPoPathAnswer, state: Dict) -> None:
    state = _ensure_state_shape(state)
    _recompute_progress(state)
    a.current_stage = state.get("current_stage") or "jtbd"
    a.stages_completed = int(state.get("_stages_completed") or 0)
    statuses = [state["stages"][k]["status"] for k in STAGES]
    if all(s == STATUS_APPROVED for s in statuses):
        a.overall_status = "completed"
    elif any(s == STATUS_NEEDS_REVISION for s in statuses):
        a.overall_status = "revising"
    elif any(s == STATUS_SUBMITTED or s == STATUS_IN_REVIEW for s in statuses):
        a.overall_status = "review"
    else:
        a.overall_status = "in_progress"
    a.data_json = json.dumps(state, ensure_ascii=False)


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


def _get_or_create_answer(group_id: int, participant_id: int) -> AgileTrainingPoPathAnswer:
    a = (
        AgileTrainingPoPathAnswer.query
        .filter_by(participant_id=participant_id)
        .first()
    )
    if a:
        return a
    initial_state = _ensure_state_shape({})
    a = AgileTrainingPoPathAnswer(
        group_id=group_id,
        participant_id=participant_id,
        current_stage="jtbd",
        stages_completed=0,
        overall_status="in_progress",
        data_json=json.dumps(initial_state, ensure_ascii=False),
    )
    db.session.add(a)
    return a


# --------------------------- public ---------------------------


@bp_agile_po_path.get("/content")
def content_public():
    locale = _resolve_locale(request.args.get("locale"), None)
    bundle = CONTENT.get(locale, CONTENT["ru"])
    return jsonify({
        "locale": locale,
        "stages": list(STAGES),
        "stage_fields": STAGE_FIELDS,
        "stage_layout": STAGE_LAYOUT,
        "ai_calls_limit": AI_CALLS_LIMIT_PER_PARTICIPANT,
        "field_text_limit": FIELD_TEXT_LIMIT,
        **bundle,
    })


@bp_agile_po_path.get("/g/<slug>/state")
def participant_state(slug: str):
    g, sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    locale = _resolve_locale(request.args.get("locale"), sess)
    token = (request.args.get("participant_token") or "").strip()
    answer_payload: Optional[Dict] = None
    participant_known = False
    if token:
        p = _require_participant(g, token)
        if p:
            participant_known = True
            # Лениво создаём ответ при первом обращении: иначе после рефреша
            # клиент видит answer=null и сваливается обратно на welcome-экран,
            # даже если участник уже представился. Создание здесь дешёвое
            # (пустой шаблон 4-х этапов), и ровно симметрично остальным
            # ручкам, которые уже использовали `_get_or_create_answer`.
            a = _get_or_create_answer(g.id, p.id)
            db.session.commit()
            answer_payload = _serialize_answer(a)

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "session": {
            "id": sess.id if sess else None,
            "title": sess.title if sess else "",
            "exercise_key": sess.exercise_key if sess else "po_path",
            "locale": sess.locale if sess else "ru",
        },
        "effective_locale": locale,
        "content": CONTENT.get(locale, CONTENT["ru"]),
        "stages": list(STAGES),
        "stage_fields": STAGE_FIELDS,
        "stage_layout": STAGE_LAYOUT,
        "ai_calls_limit": AI_CALLS_LIMIT_PER_PARTICIPANT,
        "field_text_limit": FIELD_TEXT_LIMIT,
        "answer": answer_payload,
        "participant_known": participant_known,
        "token_provided": bool(token),
    })


@bp_agile_po_path.post("/g/<slug>/answer")
def participant_answer(slug: str):
    """Автосейв полей текущего этапа.

    body:
      participant_token, stage,
      data: {field_key: text, ...},
      confidence: 0..5 | null
    """
    g, _sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    stage = (body.get("stage") or "").strip().lower()
    if not token:
        return jsonify({"error": "participant_token required"}), 400
    if stage not in STAGE_SET:
        return jsonify({"error": "stage required (jtbd|value|fit|canvas)"}), 400

    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404

    a = _get_or_create_answer(g.id, p.id)
    state = _ensure_state_shape(_safe_json_load(a.data_json))

    # Защита от записи в "запертый" этап: пишем только если current_stage <= stage
    # (т.е. этап ещё не одобрен, либо это текущий, либо ранее approved и юзер
    #  явно вернулся через /return — тогда current_stage уже сдвинется на него).
    cur = state.get("current_stage") or "jtbd"
    if cur != "done":
        cur_idx = STAGES.index(cur)
        try:
            stage_idx = STAGES.index(stage)
        except ValueError:
            return jsonify({"error": "Bad stage"}), 400
        if stage_idx > cur_idx:
            return jsonify({"error": "stage_locked"}), 409

    incoming = _clean_stage_data(stage, body.get("data") or {})
    st = state["stages"][stage]
    st_data = st.get("data") or {}
    if not isinstance(st_data, dict):
        st_data = {}
    st_data.update(incoming)
    st["data"] = st_data
    if "confidence" in body:
        c = body.get("confidence")
        if c is None or c == "":
            st["confidence"] = None
        else:
            try:
                ic = int(c)
                if 0 <= ic <= 5:
                    st["confidence"] = ic
            except Exception:
                pass
    # В self-paced режиме НЕ сбрасываем статус на autosave: участник
    # может сохранять правки в одобренный этап (после /return) или продолжать
    # дописывать уже отправленный — статус не меняется. Реальный «откат»
    # одобрения происходит только через явный /return.

    _persist_answer(a, state)
    db.session.commit()
    return jsonify({"saved": True, "answer": _serialize_answer(a)})


@bp_agile_po_path.post("/g/<slug>/submit")
def participant_submit(slug: str):
    """Завершить этап и перейти к следующему (self-paced режим).

    В self-paced воркшопе нет блокировки фасилитатором: как только участник
    нажал «Дальше» с непустыми полями, этап одобряется автоматически и
    `current_stage` сдвигается. Фасилитатор всё равно может потом нажать
    «вернуть на доработку» в своей панели — тогда этап вернётся в
    needs_revision и текущим снова станет он.
    """
    g, _sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    stage = (body.get("stage") or "").strip().lower()
    if not token:
        return jsonify({"error": "participant_token required"}), 400
    if stage not in STAGE_SET:
        return jsonify({"error": "stage required"}), 400
    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404
    a = _get_or_create_answer(g.id, p.id)
    state = _ensure_state_shape(_safe_json_load(a.data_json))
    cur = state.get("current_stage") or "jtbd"
    if cur != stage:
        return jsonify({"error": "stage_not_current", "current_stage": cur}), 409

    st = state["stages"][stage]
    if not _stage_has_meaningful_content(stage, st.get("data") or {}):
        return jsonify({"error": "stage_empty"}), 400
    st["status"] = STATUS_APPROVED
    now = _now_iso()
    st["submitted_at"] = now
    st["approved_at"] = now
    _persist_answer(a, state)
    db.session.commit()
    next_stage = NEXT_STAGE.get(stage, "done")
    return jsonify({
        "submitted": True,
        "approved": True,
        "next_stage": next_stage,
        "answer": _serialize_answer(a),
    })


@bp_agile_po_path.post("/g/<slug>/return")
def participant_return(slug: str):
    """Вернуться к более раннему (одобренному) этапу.

    Этот этап и все следующие сбрасываются в draft — каждый из них надо
    будет снова отправить фасилитатору. Данные при этом не теряются.
    """
    g, _sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    stage = (body.get("stage") or "").strip().lower()
    if not token or stage not in STAGE_SET:
        return jsonify({"error": "participant_token and stage required"}), 400
    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404
    a = _get_or_create_answer(g.id, p.id)
    state = _ensure_state_shape(_safe_json_load(a.data_json))

    target_idx = STAGES.index(stage)
    for i, k in enumerate(STAGES):
        if i >= target_idx:
            st = state["stages"][k]
            if st["status"] == STATUS_APPROVED:
                st["status"] = STATUS_DRAFT
                st["approved_at"] = None
            elif st["status"] in {STATUS_SUBMITTED, STATUS_IN_REVIEW, STATUS_NEEDS_REVISION}:
                st["status"] = STATUS_DRAFT
                st["submitted_at"] = None
    _persist_answer(a, state)
    db.session.commit()
    return jsonify({"returned_to": stage, "answer": _serialize_answer(a)})


@bp_agile_po_path.post("/g/<slug>/fit/answer-question")
def participant_answer_fit_question(slug: str):
    """Сохранить ответ участника на «неудобный вопрос» AI.

    body: participant_token, q_id, answer
    """
    g, _sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    q_id = (body.get("q_id") or "").strip()
    answer_text = _clamp_text(body.get("answer"))
    if not token or not q_id:
        return jsonify({"error": "participant_token and q_id required"}), 400
    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404
    a = _get_or_create_answer(g.id, p.id)
    state = _ensure_state_shape(_safe_json_load(a.data_json))
    fit = state["stages"]["fit"]
    questions = fit.get("ai_questions")
    if not isinstance(questions, list):
        questions = []
    found = False
    for q in questions:
        if isinstance(q, dict) and q.get("id") == q_id:
            q["answer"] = answer_text or ""
            q["answered_at"] = _now_iso()
            found = True
            break
    if not found:
        return jsonify({"error": "question_not_found"}), 404
    fit["ai_questions"] = questions
    _persist_answer(a, state)
    db.session.commit()
    return jsonify({"saved": True, "answer": _serialize_answer(a)})


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
        "Ты — доброжелательный фасилитатор для будущих Product Owner. "
        "Учеников может быть много из не-IT. Никогда не оценивай и не пиши «правильно/неправильно». "
        "Помогай: переформулируй коротко и понятно, задавай 2–3 уточняющих вопроса, предлагай альтернативные варианты. "
        "Пиши кратко, тепло, в Markdown — короткие абзацы, списки, **жирным** ключевое. Не выдумывай факты о продукте."
    ),
    "en": (
        "You are a friendly facilitator for future Product Owners. "
        "Many learners are not from IT. Never grade and never say 'correct/incorrect'. "
        "Help by: rephrasing short and clear, asking 2–3 clarifying questions, suggesting alternatives. "
        "Be concise and warm. Use Markdown — short paragraphs, lists, **bold** for emphasis. Don’t invent facts about the product."
    ),
}


def _ai_mode_instruction(mode: str, locale: str) -> str:
    mode = (mode or "").strip().lower()
    if locale == "en":
        table = {
            "improve": "The learner wants you to rephrase or polish their text. Offer 1 cleaner version and 1 alternative angle. Keep meaning intact.",
            "questions": "Ask 3 short clarifying questions that help the learner make their text more concrete.",
            "uncomfortable": "Ask 5 short uncomfortable questions about market fit. Be specific, not abstract. No diagnoses, just questions.",
            "jtbd_help": "Help formulate a Job Statement: 'When [situation], I want [action], so that [outcome]'. Suggest one filled-in version.",
            "value_help": "Help connect pains and gains to a clear value proposition in one paragraph.",
            "canvas_help": "Suggest 2 short variants for the canvas block. No marketing fluff.",
            "generic": "Help the learner. Ask 1–2 clarifying questions and suggest one next step.",
        }
    else:
        table = {
            "improve": "Ученик просит переписать его текст чище. Предложи 1 более ясный вариант и 1 другой ракурс. Смысл сохрани.",
            "questions": "Задай 3 коротких уточняющих вопроса, которые помогут сделать текст конкретнее.",
            "uncomfortable": "Задай 5 коротких неудобных вопросов про market fit. Конкретно, без абстракций. Только вопросы.",
            "jtbd_help": "Помоги сформулировать Job Statement: «Когда [ситуация], я хочу [действие], чтобы [результат]». Предложи 1 заполненный пример на основе вводных.",
            "value_help": "Помоги связать боли и выгоды с понятным ценностным предложением в одном абзаце.",
            "canvas_help": "Предложи 2 коротких варианта для блока Lean Canvas. Без маркетингового шума.",
            "generic": "Помоги ученику. Задай 1–2 уточняющих вопроса и предложи следующий шаг.",
        }
    return table.get(mode, table["generic"])


def _scripted_assist(mode: str, locale: str, user_input: str) -> str:
    """Fallback без OpenAI."""
    mode = (mode or "").strip().lower()
    if locale == "en":
        bank = {
            "improve": (
                "**Try a cleaner version**\n\n"
                "- Keep one main subject in the sentence.\n"
                "- Use a verb in the present tense.\n"
                "- Cut adjectives that don’t change meaning.\n\n"
                "Example reshape: replace “a great solution that helps people who…” with “helps [who] do [job] when [situation]”."
            ),
            "questions": (
                "**Ask yourself**\n\n"
                "- Who exactly is this for? Be specific.\n"
                "- What changes for them after they use it once?\n"
                "- Why now, why not last year?"
            ),
            "uncomfortable": (
                "**Uncomfortable questions**\n\n"
                "1. What if no one will pay for this — what would you change?\n"
                "2. Why are you better than what they already use today?\n"
                "3. How will the first 100 customers find you?\n"
                "4. What outcome must they see in the first 60 seconds to come back?\n"
                "5. What would have to be true for this idea to fail in 6 months?"
            ),
            "jtbd_help": (
                "**Try the template**\n\n"
                "_When [situation], I want [action], so that [outcome]._\n\n"
                "Tip: avoid solutions in the action part — say what the person wants to do, not how."
            ),
            "value_help": (
                "**One-paragraph template**\n\n"
                "Our product helps [segment] do [job], removing [top 1-2 pains] and giving them [top 1-2 gains]. "
                "Unlike [alternative], we [unique angle]."
            ),
            "canvas_help": (
                "**Try two angles**\n\n"
                "1. From the user’s pain.\n"
                "2. From the unfair advantage you have.\n\n"
                "Pick the one that sounds most concrete to a non-IT friend."
            ),
            "generic": "Take a breath. What is the one most important thing the customer must believe for this to work?",
        }
    else:
        bank = {
            "improve": (
                "**Попробуйте короче и яснее**\n\n"
                "- Один главный предмет в предложении.\n"
                "- Глагол в настоящем времени.\n"
                "- Уберите прилагательные, которые ничего не меняют.\n\n"
                "Пример замены: вместо «отличное решение для тех, кто…» → «помогает [кому] делать [работу], когда [ситуация]»."
            ),
            "questions": (
                "**Спросите себя**\n\n"
                "- Для кого именно это? Будьте конкретны.\n"
                "- Что изменится в его жизни после первого использования?\n"
                "- Почему сейчас, а не год назад?"
            ),
            "uncomfortable": (
                "**Неудобные вопросы**\n\n"
                "1. А если за это никто не будет платить — что вы поменяете?\n"
                "2. Чем вы лучше того, чем клиент уже пользуется сегодня?\n"
                "3. Как первые 100 клиентов найдут вас?\n"
                "4. Какой результат он должен увидеть за 60 секунд, чтобы вернуться?\n"
                "5. Что должно произойти, чтобы за 6 месяцев идея провалилась?"
            ),
            "jtbd_help": (
                "**Шаблон**\n\n"
                "_Когда [ситуация], я хочу [действие], чтобы [результат]._\n\n"
                "Совет: в «действии» не описывайте решение — говорите, что человек хочет сделать, а не как."
            ),
            "value_help": (
                "**Шаблон одного абзаца**\n\n"
                "Наш продукт помогает [сегмент] сделать [работу], снимая [1–2 боли] и давая [1–2 выгоды]. "
                "В отличие от [альтернативы], мы [уникальный угол]."
            ),
            "canvas_help": (
                "**Два угла зрения**\n\n"
                "1. От боли пользователя.\n"
                "2. От вашего несправедливого преимущества.\n\n"
                "Возьмите вариант, который звучит конкретнее для друга не из IT."
            ),
            "generic": "Сделайте паузу. Какая одна вещь должна быть правдой про клиента, чтобы идея сработала?",
        }
    return bank.get(mode, bank["generic"])


@bp_agile_po_path.post("/g/<slug>/ai-assist")
def participant_ai_assist(slug: str):
    """Анонимный AI-помощник.

    body:
      participant_token, mode (improve|questions|jtbd_help|value_help|canvas_help|generic),
      stage (для контекста), user_input, locale.
    """
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
    a = _get_or_create_answer(g.id, p.id)
    if int(a.ai_calls or 0) >= AI_CALLS_LIMIT_PER_PARTICIPANT:
        return jsonify({
            "error": "ai_limit_exceeded",
            "limit": AI_CALLS_LIMIT_PER_PARTICIPANT,
            "ai_calls": int(a.ai_calls or 0),
        }), 429

    mode = (body.get("mode") or "generic").strip().lower()
    stage_for_ctx = (body.get("stage") or "").strip().lower()
    locale = _resolve_locale(body.get("locale"), sess)
    user_input = _clamp_text(body.get("user_input"), AI_PROMPT_LIMIT_CHARS) or ""

    state = _ensure_state_shape(_safe_json_load(a.data_json))
    ctx_lines: List[str] = []
    if stage_for_ctx in STAGE_SET:
        d = state["stages"][stage_for_ctx].get("data") or {}
        if isinstance(d, dict) and d:
            ctx_lines.append("Что участник пока написал на этом этапе:")
            if stage_for_ctx == "value":
                flat = _flatten_value_for_text(d)
                if flat:
                    for line in flat.splitlines():
                        ctx_lines.append(f"- {line}")
            else:
                for k, v in d.items():
                    if isinstance(v, str):
                        ctx_lines.append(f"- {k}: {v[:300]}")
    # Подмешаем краткую сводку по предыдущим этапам — чтобы AI был связным
    for k in STAGES:
        if k == stage_for_ctx:
            break
        d = state["stages"][k].get("data") or {}
        if not d:
            continue
        if k == "value":
            flat = _flatten_value_for_text(d)
            if flat:
                ctx_lines.append(f"[value] {flat[:600]}")
        else:
            parts = []
            for kk, vv in d.items():
                if isinstance(vv, str):
                    parts.append(f"{kk}: {vv[:120]}")
            if parts:
                ctx_lines.append(f"[{k}] {' / '.join(parts)}")

    client = _openai_client()
    reply_text = ""
    model_used = None
    if client:
        system = _SYSTEM_PROMPTS.get(locale, _SYSTEM_PROMPTS["ru"])
        instruction = _ai_mode_instruction(mode, locale)
        user_msg = (
            f"{instruction}\n\n"
            f"Контекст:\n{chr(10).join(ctx_lines) if ctx_lines else '(пусто)'}\n\n"
            f"Что прислал участник для текущего шага:\n{user_input or '(пусто)'}"
        )
        try:
            resp = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.6,
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
    history = state.get("ai_history") or []
    if not isinstance(history, list):
        history = []
    history.append({
        "mode": mode,
        "stage": stage_for_ctx or None,
        "input": user_input,
        "reply": reply_text,
        "model": model_used,
        "ts": _now_iso(),
    })
    state["ai_history"] = history[-30:]
    _persist_answer(a, state)
    db.session.commit()

    return jsonify({
        "reply": reply_text,
        "model": model_used,
        "ai_calls": int(a.ai_calls or 0),
        "ai_calls_remaining": max(0, AI_CALLS_LIMIT_PER_PARTICIPANT - int(a.ai_calls or 0)),
    })


@bp_agile_po_path.post("/g/<slug>/ai-uncomfortable")
def participant_ai_uncomfortable(slug: str):
    """Сгенерировать 3–5 неудобных вопросов для market fit и сохранить их в стейт.

    body: participant_token, locale.
    """
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
    a = _get_or_create_answer(g.id, p.id)
    if int(a.ai_calls or 0) >= AI_CALLS_LIMIT_PER_PARTICIPANT:
        return jsonify({"error": "ai_limit_exceeded"}), 429

    locale = _resolve_locale(body.get("locale"), sess)
    state = _ensure_state_shape(_safe_json_load(a.data_json))

    fit_data = state["stages"]["fit"].get("data") or {}
    earlier = []
    for k in ("jtbd", "value"):
        d = state["stages"][k].get("data") or {}
        if not d:
            continue
        if k == "value":
            flat = _flatten_value_for_text(d)
            if flat:
                earlier.append(f"[value] {flat[:600]}")
        else:
            for kk, vv in d.items():
                if isinstance(vv, str):
                    earlier.append(f"[{k}/{kk}] {vv[:240]}")

    questions: List[str] = []
    client = _openai_client()
    model_used = None
    if client:
        sys_prompt = _SYSTEM_PROMPTS.get(locale, _SYSTEM_PROMPTS["ru"])
        instr = _ai_mode_instruction("uncomfortable", locale)
        user_msg = (
            f"{instr}\n\n"
            f"Гипотеза market fit:\n"
            + "\n".join(f"- {k}: {v[:260]}" for k, v in fit_data.items() if v)
            + "\n\nКонтекст из предыдущих этапов:\n"
            + ("\n".join(earlier) if earlier else "(пусто)")
            + "\n\nОтветь СТРОГО списком из 5 коротких вопросов, по одному на строку. Никаких заголовков и нумерации."
        )
        try:
            resp = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.7,
                max_tokens=400,
            )
            choice = resp.choices[0] if resp.choices else None
            if choice and getattr(choice, "message", None):
                txt = (choice.message.content or "").strip()
                for line in txt.splitlines():
                    line = line.strip().lstrip("-•0123456789. )")
                    if line:
                        questions.append(line[:280])
            model_used = getattr(resp, "model", None)
        except Exception as exc:
            model_used = f"error:{type(exc).__name__}"

    if not questions:
        starter = (CONTENT.get(locale, CONTENT["ru"]).get("stages") or {}).get("fit", {}).get("ai_starter_questions") or []
        questions = list(starter)[:5]
        model_used = model_used or "scripted"

    questions = questions[:5]
    fit = state["stages"]["fit"]
    existing = fit.get("ai_questions") or []
    if not isinstance(existing, list):
        existing = []
    by_id = {q.get("id"): q for q in existing if isinstance(q, dict)}
    new_questions = []
    for i, q_text in enumerate(questions):
        q_id = f"q{i+1}_{secrets.token_hex(2)}"
        prev_answer = ""
        if i < len(existing) and isinstance(existing[i], dict):
            prev_answer = existing[i].get("answer") or ""
        new_questions.append({
            "id": q_id,
            "q": q_text,
            "answer": prev_answer,
            "answered_at": None,
        })
    fit["ai_questions"] = new_questions

    a.ai_calls = int(a.ai_calls or 0) + 1
    history = state.get("ai_history") or []
    history.append({
        "mode": "uncomfortable",
        "stage": "fit",
        "input": json.dumps(fit_data, ensure_ascii=False)[:500],
        "reply": "\n".join(questions),
        "model": model_used,
        "ts": _now_iso(),
    })
    state["ai_history"] = history[-30:]
    _persist_answer(a, state)
    db.session.commit()

    return jsonify({
        "questions": new_questions,
        "model": model_used,
        "ai_calls": int(a.ai_calls or 0),
        "ai_calls_remaining": max(0, AI_CALLS_LIMIT_PER_PARTICIPANT - int(a.ai_calls or 0)),
    })


# --------------------------- facilitator (JWT) ---------------------------


def _own_group(group_id: int, uid: int) -> Optional[AgileTrainingGroup]:
    return (
        AgileTrainingGroup.query
        .join(AgileTrainingSession, AgileTrainingSession.id == AgileTrainingGroup.session_id)
        .filter(AgileTrainingGroup.id == group_id, AgileTrainingSession.owner_user_id == uid)
        .first()
    )


def _participant_summary_row(p: AgileTrainingParticipant, idx: int) -> Dict:
    a = AgileTrainingPoPathAnswer.query.filter_by(participant_id=p.id).first()
    if not a:
        return {
            "id": p.id,
            "display_name": p.display_name or f"#{idx}",
            "anonymous_label": f"#{idx}",
            "joined_at": p.created_at.isoformat() if p.created_at else None,
            "has_answer": False,
            "current_stage": "jtbd",
            "stages_completed": 0,
            "stage_statuses": {k: STATUS_DRAFT for k in STAGES},
            "needs_action": False,
            "updated_at": None,
        }
    state = _ensure_state_shape(_safe_json_load(a.data_json))
    _recompute_progress(state)
    statuses = {k: state["stages"][k]["status"] for k in STAGES}
    needs_action = any(s in {STATUS_SUBMITTED, STATUS_IN_REVIEW} for s in statuses.values())
    return {
        "id": p.id,
        "display_name": p.display_name or f"#{idx}",
        "anonymous_label": f"#{idx}",
        "joined_at": p.created_at.isoformat() if p.created_at else None,
        "has_answer": True,
        "current_stage": state.get("current_stage"),
        "stages_completed": int(state.get("_stages_completed") or 0),
        "stage_statuses": statuses,
        "needs_action": needs_action,
        "ai_calls": int(a.ai_calls or 0),
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


@bp_agile_po_path.get("/groups/<int:group_id>/participants")
@jwt_required()
def group_participants(group_id: int):
    uid = _uid()
    g = _own_group(group_id, uid)
    if not g:
        return jsonify({"error": "Not found"}), 404
    participants = (
        AgileTrainingParticipant.query
        .filter_by(group_id=g.id)
        .order_by(AgileTrainingParticipant.id.asc())
        .all()
    )
    rows = [_participant_summary_row(p, i + 1) for i, p in enumerate(participants)]
    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants": rows,
        "stages": list(STAGES),
    })


@bp_agile_po_path.get("/groups/<int:group_id>/participants/<int:participant_id>")
@jwt_required()
def participant_detail(group_id: int, participant_id: int):
    uid = _uid()
    g = _own_group(group_id, uid)
    if not g:
        return jsonify({"error": "Not found"}), 404
    p = AgileTrainingParticipant.query.filter_by(id=participant_id, group_id=g.id).first()
    if not p:
        return jsonify({"error": "Not found"}), 404
    a = AgileTrainingPoPathAnswer.query.filter_by(participant_id=p.id).first()
    payload = _serialize_answer(a) if a else None
    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participant": {
            "id": p.id,
            "display_name": p.display_name or f"#{p.id}",
            "joined_at": p.created_at.isoformat() if p.created_at else None,
        },
        "answer": payload,
    })


@bp_agile_po_path.post("/groups/<int:group_id>/participants/<int:participant_id>/review")
@jwt_required()
def participant_review(group_id: int, participant_id: int):
    """Approve / reject (одобрить или вернуть на доработку) этап участника.

    body: stage, action ("approve"|"reject"), comment (optional).
    """
    uid = _uid()
    g = _own_group(group_id, uid)
    if not g:
        return jsonify({"error": "Not found"}), 404
    p = AgileTrainingParticipant.query.filter_by(id=participant_id, group_id=g.id).first()
    if not p:
        return jsonify({"error": "Not found"}), 404
    body = request.get_json(silent=True) or {}
    stage = (body.get("stage") or "").strip().lower()
    action = (body.get("action") or "").strip().lower()
    comment = _clamp_text(body.get("comment"), COMMENT_LIMIT)
    if stage not in STAGE_SET:
        return jsonify({"error": "stage required"}), 400
    if action not in {"approve", "reject"}:
        return jsonify({"error": "action must be approve|reject"}), 400
    a = AgileTrainingPoPathAnswer.query.filter_by(participant_id=p.id).first()
    if not a:
        return jsonify({"error": "Answer not found"}), 404
    state = _ensure_state_shape(_safe_json_load(a.data_json))
    st = state["stages"][stage]
    st.setdefault("comments", [])
    if action == "approve":
        st["status"] = STATUS_APPROVED
        st["approved_at"] = _now_iso()
        if comment:
            st["comments"].append({
                "author": "facilitator",
                "kind": "review",
                "verdict": "approved",
                "text": comment,
                "ts": _now_iso(),
            })
    else:
        st["status"] = STATUS_NEEDS_REVISION
        st["review_round"] = int(st.get("review_round") or 0) + 1
        if comment:
            st["comments"].append({
                "author": "facilitator",
                "kind": "review",
                "verdict": "needs_revision",
                "text": comment,
                "ts": _now_iso(),
            })
    _persist_answer(a, state)
    db.session.commit()
    return jsonify({"reviewed": True, "answer": _serialize_answer(a)})


@bp_agile_po_path.post("/groups/<int:group_id>/participants/<int:participant_id>/comment")
@jwt_required()
def participant_comment(group_id: int, participant_id: int):
    """Свободный комментарий фасилитатора без смены статуса."""
    uid = _uid()
    g = _own_group(group_id, uid)
    if not g:
        return jsonify({"error": "Not found"}), 404
    p = AgileTrainingParticipant.query.filter_by(id=participant_id, group_id=g.id).first()
    if not p:
        return jsonify({"error": "Not found"}), 404
    body = request.get_json(silent=True) or {}
    stage = (body.get("stage") or "").strip().lower()
    text = _clamp_text(body.get("text"), COMMENT_LIMIT)
    if stage not in STAGE_SET or not text:
        return jsonify({"error": "stage and text required"}), 400
    a = AgileTrainingPoPathAnswer.query.filter_by(participant_id=p.id).first()
    if not a:
        return jsonify({"error": "Answer not found"}), 404
    state = _ensure_state_shape(_safe_json_load(a.data_json))
    st = state["stages"][stage]
    st.setdefault("comments", [])
    st["comments"].append({
        "author": "facilitator",
        "kind": "note",
        "text": text,
        "ts": _now_iso(),
    })
    _persist_answer(a, state)
    db.session.commit()
    return jsonify({"saved": True, "answer": _serialize_answer(a)})


@bp_agile_po_path.get("/groups/<int:group_id>/results")
@jwt_required()
def group_results(group_id: int):
    """Сводка по группе для фасилитатора."""
    uid = _uid()
    g = _own_group(group_id, uid)
    if not g:
        return jsonify({"error": "Not found"}), 404
    rows = AgileTrainingPoPathAnswer.query.filter_by(group_id=g.id).all()
    by_stage_status: Dict[str, Dict[str, int]] = {k: {s: 0 for s in ALL_STATUSES} for k in STAGES}
    needs_action = 0
    completed = 0
    for r in rows:
        state = _ensure_state_shape(_safe_json_load(r.data_json))
        statuses = [state["stages"][k]["status"] for k in STAGES]
        if all(s == STATUS_APPROVED for s in statuses):
            completed += 1
        if any(s in {STATUS_SUBMITTED, STATUS_IN_REVIEW} for s in statuses):
            needs_action += 1
        for k in STAGES:
            s = state["stages"][k]["status"]
            by_stage_status[k][s] = by_stage_status[k].get(s, 0) + 1
    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants_count": g.participants.count(),
        "answers_count": len(rows),
        "completed_count": completed,
        "needs_action_count": needs_action,
        "by_stage_status": by_stage_status,
        "stages": list(STAGES),
    })


@bp_agile_po_path.post("/groups/<int:group_id>/reset")
@jwt_required()
def group_reset(group_id: int):
    uid = _uid()
    g = _own_group(group_id, uid)
    if not g:
        return jsonify({"error": "Not found"}), 404
    AgileTrainingPoPathAnswer.query.filter_by(group_id=g.id).delete()
    db.session.commit()
    return jsonify({"reset": True})
