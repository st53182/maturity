"""Backend тренинга «Продуктовое мышление: User Story / Job Story / декомпозиция».

API под префиксом `/api/agile-training/product-thinking`.

Использует общие сущности обучающего каркаса:
  - AgileTrainingSession (exercise_key = "product_thinking")
  - AgileTrainingGroup
  - AgileTrainingParticipant

Ответы храним одной записью на участника (JSON в data_json). Акцент тренинга —
обучение через практику и обсуждение, а не автоматическая оценка, поэтому в
бэкенде нет никакой "правильности": только хранение артефактов и AI-помощник
(анонимный, с лимитом обращений на участника).
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from typing import Dict, List, Optional

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database import db
from models import (
    AgileTrainingGroup,
    AgileTrainingParticipant,
    AgileTrainingProductThinkingAnswer,
    AgileTrainingSession,
)


bp_agile_product_thinking = Blueprint(
    "agile_product_thinking", __name__, url_prefix="/api/agile-training/product-thinking"
)


# --------------------------- constants / content ---------------------------


ALLOWED_TECHNIQUES = {"spidr", "seven_dim"}
AI_CALLS_LIMIT_PER_PARTICIPANT = 15
AI_PROMPT_LIMIT_CHARS = 2000

ALLOWED_STAGES = (
    "case_choice",
    "intro",
    "example",
    "user_story",
    "job_story",
    "compare",
    "epic",
    "decomposition_example",
    "decomposition",
    "technique",
    "improve",
    "summary",
)
STAGE_SET = set(ALLOWED_STAGES)

ALLOWED_CASE_KEYS = {"it", "event"}


CONTENT = {
    "ru": {
        "cases": [
            {
                "key": "it",
                "emoji": "💳",
                "label": "IT-кейс: премиум-карта банка",
                "short": "Реалистичный продуктовый эпик в банке — со стеком систем, архитектурой и ограничениями.",
                "title": "Запуск премиум дебетовой карты с умным кешбэком в мобильном приложении банка",
                "context": [
                    "Розничный банк, 8 млн клиентов, 15 лет на рынке",
                    "Уже есть обычные дебетовые карты и базовый кешбэк 1% на всё",
                    "У премиум-сегмента (доход от 250 тыс. ₽/мес) нет отдельного продукта",
                    "Конкуренты (Т-Банк, Сбер Premier) запустили умный кешбэк и активно забирают эту аудиторию",
                    "Маркетинговая кампания запуска запланирована через 4 месяца — это дедлайн",
                ],
                "goal": "Удержать и привлечь премиум-сегмент картой, выгода от которой заметна каждый месяц",
                "hint": "Опишите продукт так, чтобы команде из 15 разработчиков, 2 дизайнеров и 1 продакта было ясно, что и зачем делать",
                "epic_summary": "Премиум дебетовая карта с умным кешбэком (разные ставки по категориям) и консьерж-сервисом в мобильном приложении банка",
                "epic_why": (
                    "Внутри — целый набор сценариев: онбординг в продукт, заявка и KYC, "
                    "выпуск и доставка карты, активация, ежедневные покупки с расчётом "
                    "кешбэка, дашборд бонусов, трата бонусов, дополнительные виртуальные "
                    "карты для семьи, консьерж и поддержка. За один спринт это не сделать — "
                    "поэтому это эпик."
                ),
                "environment": {
                    "audience": [
                        "Действующие клиенты банка с доходом от 250 тыс. ₽/мес (выборка из CRM)",
                        "Новые премиум-клиенты по рефералке",
                        "Возраст 28–50, в основном IT и менеджмент, активные пользователи мобильного банка",
                    ],
                    "stack": [
                        "iOS — Swift + SwiftUI, релиз раз в 2 недели в App Store",
                        "Android — Kotlin + Jetpack Compose, релиз раз в 2 недели в Google Play",
                        "Backend — Java 17 / Spring Boot, 15 микросервисов",
                        "БД — Oracle (core banking), PostgreSQL (продуктовые данные), Redis (кэш)",
                        "Шина событий — Apache Kafka",
                        "Auth — OAuth2/OIDC + биометрия устройства; 3D Secure для онлайн-транзакций",
                        "Инфраструктура — Kubernetes on-prem, CI/CD на GitLab",
                    ],
                    "architecture": [
                        "API Gateway (Kong) на входе, единая точка для мобильных клиентов",
                        "Сервис карт → внешний процессинговый центр с проприетарным API",
                        "Сервис «Программа лояльности» — считает кешбэк, хранит бонусные балансы",
                        "Сервис «Транзакции» — публикует события покупок в Kafka (MCC-коды, сумма)",
                        "Compliance-сервис — отдельный контур PCI DSS и 152-ФЗ",
                        "CRM — Salesforce, сегментация и коммуникации",
                    ],
                    "existing": [
                        "Уже работают экраны обычной дебетовой карты в мобильном приложении",
                        "Есть начисление базового кешбэка 1% ежедневным ночным батчем",
                        "Есть push-уведомления о транзакциях в real-time",
                        "Выпуск и доставка карт курьером работают через процессинг",
                    ],
                    "constraints": [
                        "PCI DSS: номера карт не хранятся в наших системах, только в процессинге",
                        "152-ФЗ: персональные данные не покидают контур банка",
                        "Инструкция ЦБ РФ №338-И по выпуску карт и проверке клиента",
                        "Мобильный релизный поезд раз в 2 недели; бэкенд — непрерывно",
                        "Бюджет: ~30 млн ₽ + существующая команда, без найма",
                        "Дедлайн — 4 месяца до маркетинговой кампании",
                    ],
                    "stakeholders": [
                        "CPO розничного блока — владелец продукта",
                        "Маркетинг — зависит запуск кампании",
                        "Контакт-центр — готовит сценарии поддержки",
                        "Compliance и юристы — согласовывают условия и договор-оферту",
                        "Команда процессинга — внешняя, их релизы согласовываются отдельно",
                    ],
                },
                "examples": {
                    "scenario": "Мини-пример из совсем другой жизни: запись на стрижку через приложение барбершопа",
                    "user_story": "Как постоянный клиент, я хочу записываться к своему мастеру онлайн, чтобы не искать свободное время по звонку",
                    "job_story": "Когда у меня между встречами освободился час, я хочу быстро занять ближайший слот у своего мастера, чтобы не терять возможность",
                    "focus_us": "User Story — фокус на том, кем является человек (постоянный клиент, свой мастер)",
                    "focus_js": "Job Story — фокус на ситуации (окно между встречами, нужен слот быстро)",
                    "note": "Это НЕ готовый ответ к вашему эпику — это пример другой области, чтобы показать сам приём. Свой User Story и Job Story под банковский эпик вы напишете на следующих двух экранах.",
                },
                "decomposition_examples": [
                    {
                        "label": "Вариант 1 — по шагам клиента (customer journey)",
                        "subtitle": "Режем по пути пользователя: что он делает по очереди",
                        "items": [
                            "Онбординг: баннер и объяснение продукта на главной",
                            "Заявка: проверка дохода из CRM и согласие на условия",
                            "Выпуск и доставка: выбор способа, адрес, трекинг",
                            "Активация: ввод PIN, биометрия, первая транзакция",
                            "Использование: отметка категории и кешбэка в истории операций",
                            "Дашборд бонусов: текущая сумма, прогноз, топ-категории",
                            "Трата бонусов: рублями, баллами, сертификатами партнёров",
                        ],
                    },
                    {
                        "label": "Вариант 2 — от минимального к полному (инкрементально)",
                        "subtitle": "Режем по «богатству» продукта: сначала простой минимум, потом надстраиваем",
                        "items": [
                            "MVP: премиум-карта с фиксированным кешбэком 2% на всё, считается ночным батчем",
                            "+ Разные ставки по 2 категориям (рестораны 5%, путешествия 3%), остальное 1%",
                            "+ Ещё 6 категорий (АЗС, аптеки, такси, супермаркеты, кино, онлайн)",
                            "+ Real-time начисление по событию транзакции из Kafka (SLA 1 мин)",
                            "+ Дополнительные виртуальные карты для членов семьи",
                            "+ Консьерж-сервис: чат с оператором 24/7",
                        ],
                    },
                    {
                        "label": "Вариант 3 — по SPIDR",
                        "subtitle": "Spike · Path · Interfaces · Data · Rules — классическая продуктовая декомпозиция",
                        "items": [
                            {"tag": "S — Spike", "text": "Исследование на 1 неделю: как процессинг отдаёт MCC-коды и с какой задержкой — можно ли считать кешбэк в real-time или только батчем"},
                            {"tag": "P — Path", "text": "Самый тонкий end-to-end: клиент подаёт заявку → карту выпускают → активирует → совершает покупку → ночью видит +1% на балансе"},
                            {"tag": "I — Interfaces", "text": "Сначала только iOS, потом Android, потом веб-личный-кабинет. Внутри iOS: сначала для действующих клиентов, потом — для новых"},
                            {"tag": "D — Data", "text": "Сначала 1 валюта ₽ и 1 категория «Всё». Потом 8 категорий. Потом валютные операции и cross-border"},
                            {"tag": "R — Rules", "text": "Один уровень «Premium» с одной ставкой. Потом уровни Premium/Premium+ с прогрессивной шкалой по обороту"},
                        ],
                    },
                    {
                        "label": "Вариант 4 — по 7 dimensions",
                        "subtitle": "7 осей разбиения (Mike Cohn / Richard Lawrence): каждая даёт свой срез",
                        "items": [
                            {"tag": "1. Workflow steps", "text": "Этапы процесса: онбординг → заявка → KYC → выпуск → доставка → активация → использование. Делаем по одному этапу"},
                            {"tag": "2. Business rule variations", "text": "Вариации правил: один уровень кешбэка → уровни Premium/Premium+ → персональные ставки"},
                            {"tag": "3. Major effort", "text": "Платформы/каналы: iOS → Android → веб. Не запускаем на трёх сразу"},
                            {"tag": "4. Simple/complex", "text": "Простой случай — один клиент. Сложный — семья с дополнительными виртуальными картами и общими лимитами"},
                            {"tag": "5. Data variations", "text": "Типы данных: только ₽ → мультивалюта → учёт cashback-бонусов как отдельной «валюты»"},
                            {"tag": "6. Defer performance", "text": "Сначала батчем ночью (проще), потом — real-time через Kafka с SLA 1 мин"},
                            {"tag": "7. Operations/UI", "text": "Базовая отметка в истории → полноценный дашборд с графиками, сравнением месяцев и прогнозом"},
                        ],
                    },
                ],
                "good_task": "На экране «Премиум-карта» показать секцию «Кешбэк за месяц» с текущей суммой и топ-3 категориями (frontend-only, данные из нового endpoint /loyalty/summary, без анимаций)",
                "bad_task": "Сделать программу лояльности",
            },
            {
                "key": "event",
                "emoji": "🎉",
                "label": "Не-IT: корпоративный выезд-ретрит",
                "short": "Не из IT, но того же масштаба: двухдневный ретрит IT-компании на 150 человек.",
                "title": "Организовать двухдневный корпоративный выезд для IT-компании на 150 человек",
                "context": [
                    "Компания: IT-продукт, 150 человек, 60% удалённых сотрудников",
                    "Средний возраст 30, 70% — технические роли",
                    "Раньше был только корпоратив в ресторане в Москве на 100 человек",
                    "Задача поставлена 2 месяца назад, провести через 1 месяц",
                    "Октябрь, Подмосковье — погода может сорвать уличную программу",
                ],
                "goal": "Сплотить удалёнку с офисом, показать ценности компании и обсудить стратегию следующего года",
                "hint": "Опишите выезд так, чтобы HR-директор, офис-менеджер и представители команд понимали, что и зачем делать",
                "epic_summary": "Двухдневный ретрит на базе отдыха под Москвой: трансфер, ночёвка, программа, стратегическая сессия, кейтеринг, рассадка",
                "epic_why": (
                    "Внутри — десятки мелких задач: найти и проверить базу, организовать "
                    "транспорт, согласовать меню (веганы, аллергии), продумать программу "
                    "для разных групп, подготовить стратегическую сессию, закрыть вопросы "
                    "проживания, фотографа и сувениров. Одним вечером это не решается — "
                    "это эпик."
                ),
                "environment": {
                    "audience": [
                        "Инженеры (70%): техлиды, разработчики, тестировщики — 60% удалёнщики",
                        "Менеджмент и продукт (20%): продакты, тимлиды",
                        "HR и бэк-офис (10%)",
                        "Есть команды из разных часовых поясов (Москва, Казань, Новосибирск)",
                    ],
                    "stack": [
                        "Бюджет 4 млн ₽, согласован с CFO",
                        "Внешнее ивент-агентство не используем — делаем внутренним оргкомитетом",
                        "Подрядчики: база отдыха (1 контракт), кейтеринг (1 контракт), транспорт (2–3 автобуса)",
                        "Инструменты: Google Workspace для календаря, HRM для регистрации, Slack для анонсов",
                    ],
                    "architecture": [
                        "Оргкомитет: HR-директор, офис-менеджер, 2 волонтёра из команд",
                        "Поток регистрации: анкета в HRM → диета и согласия → рассадка по автобусам и номерам",
                        "Параллельно: фасилитация стратегической сессии CEO + CPO",
                        "Транспорт: сбор от 2 точек в Москве + свой способ добраться",
                    ],
                    "existing": [
                        "Есть опыт 3-часового корпоратива в ресторане на 100 человек",
                        "Есть контакты кейтеринга и баз отдыха из предыдущих попыток",
                        "В HRM уже есть форма с обязательными полями (диета, аллергии, размер одежды)",
                    ],
                    "constraints": [
                        "Октябрь, погода: нужен план Б в помещении",
                        "Удалёнщики из других городов: авиаперелёт — ещё ~0,8 млн ₽",
                        "Стратегическая сессия — не дольше 3 часов, иначе команда перестаёт воспринимать",
                        "Оплата подрядчикам строго по договору, не ранее чем за 2 недели до события",
                        "CEO подтверждает смету и программу за 2 недели до даты выезда",
                    ],
                    "stakeholders": [
                        "CEO — утверждает смету и стратегическую сессию",
                        "HR-директор — отвечает за атмосферу и результат",
                        "Тимлиды — помогают с программой своих команд",
                        "Удалённые сотрудники — им нужна прозрачная логистика",
                        "Подрядчики (база, транспорт, кейтеринг) — внешние",
                    ],
                },
                "examples": {
                    "scenario": "Мини-пример из совсем другой жизни: запись на стрижку через приложение барбершопа",
                    "user_story": "Как постоянный клиент, я хочу записываться к своему мастеру онлайн, чтобы не искать свободное время по звонку",
                    "job_story": "Когда у меня между встречами освободился час, я хочу быстро занять ближайший слот у своего мастера, чтобы не терять возможность",
                    "focus_us": "User Story — фокус на том, кем является человек (постоянный клиент, свой мастер)",
                    "focus_js": "Job Story — фокус на ситуации (окно между встречами, нужен слот быстро)",
                    "note": "Это НЕ готовый ответ к вашему эпику — это пример другой области, чтобы показать сам приём. Свой User Story и Job Story под выезд команды вы напишете на следующих двух экранах.",
                },
                "decomposition_examples": [
                    {
                        "label": "Вариант 1 — по шагам подготовки",
                        "subtitle": "Режем по этапам: от выбора базы до самого выезда",
                        "items": [
                            "Выбрать базу отдыха (шорт-лист из 3 вариантов → финал)",
                            "Согласовать бюджет с CEO",
                            "Собрать регистрацию: диеты, размеры, пожелания",
                            "Выбрать транспорт и точки сбора",
                            "Согласовать меню с кейтерингом",
                            "Сформировать программу двух дней (сессия + отдых)",
                            "Напоминания, рассадка, сувениры",
                            "День X — провести ретрит",
                            "После — собрать обратную связь и фото",
                        ],
                    },
                    {
                        "label": "Вариант 2 — от простого к полному",
                        "subtitle": "Режем по «богатству» выезда: сначала минимум, потом украшаем",
                        "items": [
                            "Минимум: один день, ближняя база, обед и одна активность",
                            "+ Ночёвка и ужин с культурной программой",
                            "+ Стратегическая сессия с CEO и CPO",
                            "+ Мастер-классы по ролям (инженеры / менеджеры / HR)",
                            "+ Фотограф, брендированные сувениры, итоговый ролик",
                        ],
                    },
                    {
                        "label": "Вариант 3 — по SPIDR",
                        "subtitle": "Spike · Path · Interfaces · Data · Rules в применении к ивенту",
                        "items": [
                            {"tag": "S — Spike", "text": "3 дня: объехать/созвониться с 3 потенциальными базами, собрать цены и вместимость, выбрать финалиста"},
                            {"tag": "P — Path", "text": "Самый простой end-to-end: автобус → приезд → обед → одна активность → ужин → сон → завтрак → отъезд"},
                            {"tag": "I — Interfaces", "text": "Разные аудитории: офисники (ближе, меньше логистики), удалёнщики (перелёт + трансфер), топ-менеджеры (отдельный номер и программа)"},
                            {"tag": "D — Data", "text": "Варианты меню: стандарт → веган/безглютен → кошер/халяль при необходимости"},
                            {"tag": "R — Rules", "text": "Политика рассадки в автобусе и номерах: по очереди → по командам → по «сближающим» правилам (новички + старожилы)"},
                        ],
                    },
                    {
                        "label": "Вариант 4 — по 7 dimensions",
                        "subtitle": "7 осей разбиения: можно начать с любой оси и тянуть её по одной",
                        "items": [
                            {"tag": "1. Workflow steps", "text": "Этапы: регистрация → логистика → проживание → программа → отчёт. Можно разобрать по одному"},
                            {"tag": "2. Business rule variations", "text": "Разные правила для ролей: топам — свой график, инженерам — игры, HR — фасилитация"},
                            {"tag": "3. Major effort", "text": "Один формат для всех vs. параллельные треки по интересам — начать с одного, расширять потом"},
                            {"tag": "4. Simple/complex", "text": "Простой случай — команда 30 человек в одном городе. Сложный — 150 из 3 городов с перелётами"},
                            {"tag": "5. Data variations", "text": "Размеры групп: пилот на 20 → 50 → 150. На 20 отрабатываем процесс"},
                            {"tag": "6. Defer performance", "text": "Сначала бумажные списки и Google Forms; в следующий раз — автоматизация в HRM"},
                            {"tag": "7. Operations/UI", "text": "Начать с коротких анонсов в Slack, позже — брендированный лендинг события, QR-код на бейдже"},
                        ],
                    },
                ],
                "good_task": "Созвониться с 3 базами отдыха из списка и получить КП на 150 чел, 2 ночи, кейтеринг на 5 приёмов пищи, с указанием цены и свободных дат в октябре",
                "bad_task": "Организовать корпоративный выезд",
            },
        ],
        "primer": {
            "epic_title": "Что такое «эпик»?",
            "epic_text": (
                "Эпик — это большая задача. Её нельзя сделать за один день, "
                "потому что внутри много маленьких шагов. Когда мы «декомпозируем», "
                "мы режем эпик на эти маленькие шаги, которые команда сможет делать по очереди."
            ),
            "decomposition_title": "Что такое «декомпозиция»?",
            "decomposition_text": (
                "Декомпозиция — это разделить одну большую цель на маленькие задачи. "
                "Хорошая маленькая задача — та, которую понятно, как сделать, и "
                "можно проверить отдельно. Плохая — это ещё целый проект, просто с новым словом."
            ),
            "good_task_label": "Так выглядит маленькая задача — её видно, что делать",
            "bad_task_label": "А это ещё не задача, а целый эпик — его надо резать дальше",
            "start_small_hint": (
                "Не пытайтесь описать всё идеально. Начните с 3–5 задач — каждую "
                "можно уточнить или разбить позже. Подглядывайте в примеры выше, "
                "но формулируйте под свой эпик, а не копируйте."
            ),
        },
        "techniques": {
            "spidr": {
                "title": "SPIDR",
                "subtitle": "5 способов разрезать эпик, если он «не режется»",
                "items": [
                    {"tag": "S — Spike", "text": "Исследование/эксперимент с фиксированной длительностью: когда неясно, как делать"},
                    {"tag": "P — Path", "text": "Самый тонкий сценарий end-to-end: одна ветка пользователя от начала до конца"},
                    {"tag": "I — Interfaces", "text": "Разные интерфейсы/каналы/аудитории: iOS → Android → веб; клиент → сотрудник"},
                    {"tag": "D — Data", "text": "Разные данные: одна валюта → много; одна категория → много"},
                    {"tag": "R — Rules", "text": "Разные бизнес-правила: один уровень/ставка → много; простое правило → сложное"},
                ],
            },
            "seven_dim": {
                "title": "7 dimensions of decomposition",
                "subtitle": "7 осей разбиения (Cohn / Lawrence): если эпик большой, двигайтесь по одной оси",
                "items": [
                    {"tag": "1. Workflow steps", "text": "По этапам бизнес-процесса: шаг за шагом"},
                    {"tag": "2. Business rule variations", "text": "По вариациям правил: начать с одного, добавлять постепенно"},
                    {"tag": "3. Major effort", "text": "По крупным усилиям: одна платформа → другая, один сегмент → другой"},
                    {"tag": "4. Simple/complex", "text": "Сначала простой случай, потом сложный (с исключениями, граничными случаями)"},
                    {"tag": "5. Data variations", "text": "По типам/объёмам данных: начать с узкого, расширять"},
                    {"tag": "6. Defer performance", "text": "Сначала корректно и медленно, потом — быстро и оптимизированно"},
                    {"tag": "7. Operations/UI", "text": "Базовый UI и операции → красивый дашборд, автоматизация, аналитика"},
                ],
            },
        },
    },
    "en": {
        "cases": [
            {
                "key": "it",
                "emoji": "💳",
                "label": "IT case: bank premium card",
                "short": "A realistic product epic at a retail bank — with tech stack, architecture and constraints.",
                "title": "Launch a premium debit card with smart cashback in the bank's mobile app",
                "context": [
                    "Retail bank, 8M customers, 15 years on the market",
                    "Regular debit cards already exist, plus a flat 1% cashback on everything",
                    "Premium segment (income > $3K/month) has no dedicated product",
                    "Competitors launched smart-cashback cards and are winning this audience",
                    "Launch deadline: 4 months, tied to a big marketing campaign",
                ],
                "goal": "Retain and attract the premium segment with a card whose value is visible every month",
                "hint": "Describe the product so a team of 15 devs, 2 designers and 1 product manager understands what and why to build",
                "epic_summary": "Premium debit card with smart cashback (per-category rates) and a concierge service in the mobile banking app",
                "epic_why": (
                    "It covers a whole set of flows: product onboarding, application and KYC, "
                    "card issuing and delivery, activation, daily purchases with cashback, "
                    "bonus dashboard, spending bonuses, additional virtual cards for family, "
                    "concierge and support. You can't ship all of that in one sprint — "
                    "that's why it's an epic."
                ),
                "environment": {
                    "audience": [
                        "Existing bank customers with income > $3K/month (CRM segment)",
                        "New premium customers via referral programme",
                        "Age 28–50, mostly IT and management, active mobile-bank users",
                    ],
                    "stack": [
                        "iOS — Swift + SwiftUI, biweekly App Store release train",
                        "Android — Kotlin + Jetpack Compose, biweekly Google Play release train",
                        "Backend — Java 17 / Spring Boot, 15 microservices",
                        "DBs — Oracle (core banking), PostgreSQL (product data), Redis (cache)",
                        "Event bus — Apache Kafka",
                        "Auth — OAuth2/OIDC + device biometrics; 3-D Secure for online transactions",
                        "Infra — Kubernetes on-prem, CI/CD on GitLab",
                    ],
                    "architecture": [
                        "API Gateway (Kong) as the single entrypoint for mobile clients",
                        "Cards service → external processing centre with a proprietary API",
                        "«Loyalty» service — computes cashback and stores bonus balances",
                        "«Transactions» service — publishes purchase events (MCC, amount) to Kafka",
                        "Compliance service — separated contour for PCI DSS and PII",
                        "CRM — Salesforce, segmentation and comms",
                    ],
                    "existing": [
                        "Regular debit-card screens are already live in the mobile app",
                        "Flat 1% cashback works as a nightly batch job",
                        "Real-time push notifications about transactions are in place",
                        "Card issuing and courier delivery already work via processing",
                    ],
                    "constraints": [
                        "PCI DSS: card PANs live only in processing, never in our systems",
                        "Local privacy law: personal data must stay inside the bank perimeter",
                        "Central-bank regulation on card issuing and customer checks",
                        "Mobile release train biweekly; backend releases continuously",
                        "Budget ~$300K + existing team, no new hires",
                        "Deadline: 4 months until the marketing campaign",
                    ],
                    "stakeholders": [
                        "Retail CPO — product owner",
                        "Marketing — blocked by the launch date",
                        "Contact-centre — prepares support scenarios",
                        "Compliance and legal — approve T&Cs and the offer contract",
                        "Processing team — external, their release cadence is separate",
                    ],
                },
                "examples": {
                    "scenario": "A tiny example from a completely different world: booking a haircut via a barbershop app",
                    "user_story": "As a regular customer, I want to book my usual barber online, so I don't have to hunt for a slot over the phone",
                    "job_story": "When an hour opens up between meetings, I want to grab the nearest free slot with my barber, so I don't miss the chance",
                    "focus_us": "User Story — focuses on WHO the person is (a regular customer, with their own barber)",
                    "focus_js": "Job Story — focuses on the SITUATION (a sudden gap between meetings, needs a slot fast)",
                    "note": "This is NOT the ready answer to your epic — it's just a different-domain illustration of the pattern. You'll write your own User Story and Job Story for the banking epic on the next two screens.",
                },
                "decomposition_examples": [
                    {
                        "label": "Option 1 — along the customer journey",
                        "subtitle": "Slice by user path: what the customer does step by step",
                        "items": [
                            "Onboarding: banner and product explanation on the home screen",
                            "Application: income check in CRM and T&Cs consent",
                            "Issuing and delivery: method, address, tracking",
                            "Activation: PIN, biometrics, first transaction",
                            "Usage: category tag and cashback line in operation history",
                            "Bonus dashboard: current balance, forecast, top categories",
                            "Spending bonuses: as rubles, points or partner vouchers",
                        ],
                    },
                    {
                        "label": "Option 2 — from minimum to full (incremental)",
                        "subtitle": "Slice by richness: start with the simplest thing, then grow it",
                        "items": [
                            "MVP: premium card with flat 2% cashback, computed by the nightly batch",
                            "+ Different rates across 2 categories (restaurants 5%, travel 3%), the rest 1%",
                            "+ 6 more categories (gas, pharmacy, taxi, groceries, cinema, online)",
                            "+ Real-time cashback on a Kafka transaction event, SLA 1 min",
                            "+ Additional virtual cards for family members",
                            "+ Concierge service: chat with an operator 24/7",
                        ],
                    },
                    {
                        "label": "Option 3 — by SPIDR",
                        "subtitle": "Spike · Path · Interfaces · Data · Rules — a classic product decomposition",
                        "items": [
                            {"tag": "S — Spike", "text": "1-week research: how processing returns MCC codes and at what latency — can we compute cashback in real time, or only in a batch?"},
                            {"tag": "P — Path", "text": "Thinnest end-to-end: customer applies → card is issued → activates → makes a purchase → sees +1% on balance overnight"},
                            {"tag": "I — Interfaces", "text": "iOS first, then Android, then web account. Within iOS: existing customers first, then new ones"},
                            {"tag": "D — Data", "text": "One currency and one category «All» first, then 8 categories, then FX / cross-border"},
                            {"tag": "R — Rules", "text": "One «Premium» level with one rate first, then Premium / Premium+ progressive tiers by turnover"},
                        ],
                    },
                    {
                        "label": "Option 4 — by 7 dimensions",
                        "subtitle": "7 axes of decomposition (Mike Cohn / Richard Lawrence): each gives a separate slice",
                        "items": [
                            {"tag": "1. Workflow steps", "text": "Process phases: onboarding → application → KYC → issuing → delivery → activation → usage. Ship one phase at a time"},
                            {"tag": "2. Business rule variations", "text": "Rule variations: one cashback level → Premium/Premium+ tiers → personalised rates"},
                            {"tag": "3. Major effort", "text": "Platforms/channels: iOS → Android → web. Don't launch on all three at once"},
                            {"tag": "4. Simple/complex", "text": "Simple case — a single customer. Complex — a family with additional virtual cards and shared limits"},
                            {"tag": "5. Data variations", "text": "Data types: single currency → multi-currency → bonuses as a separate «currency»"},
                            {"tag": "6. Defer performance", "text": "Nightly batch first (simpler), real-time via Kafka with 1-min SLA later"},
                            {"tag": "7. Operations/UI", "text": "Basic line in history → full dashboard with charts, month-over-month comparison and forecast"},
                        ],
                    },
                ],
                "good_task": "On the «Premium card» screen show a «Cashback this month» section with the current amount and top-3 categories (frontend-only, data from a new /loyalty/summary endpoint, no animations)",
                "bad_task": "Build a loyalty programme",
            },
            {
                "key": "event",
                "emoji": "🎉",
                "label": "Non-IT: corporate offsite retreat",
                "short": "Not IT, same scale: a two-day retreat for an IT company of 150 people.",
                "title": "Organize a two-day corporate offsite for an IT company of 150 people",
                "context": [
                    "Company: product IT, 150 people, 60% remote",
                    "Average age 30, 70% technical roles",
                    "Previously: only a 3-hour party in a Moscow restaurant for 100 people",
                    "Task was given 2 months ago, to happen in 1 month",
                    "October, near Moscow — weather may kill outdoor programme",
                ],
                "goal": "Bring remote and office people together, convey company values and discuss next year's strategy",
                "hint": "Describe the offsite so HR, office manager and team leads all understand what and why to do",
                "epic_summary": "Two-day retreat at a countryside resort: transport, accommodation, programme, strategy session, catering, seating",
                "epic_why": (
                    "It's dozens of small tasks: find and vet a venue, arrange transport, "
                    "agree on the menu (vegans, allergies), design programme for different "
                    "groups, prep the strategy session, sort accommodation, photographer "
                    "and gifts. One evening is not enough — it's an epic."
                ),
                "environment": {
                    "audience": [
                        "Engineers (70%): tech leads, devs, QA — 60% remote",
                        "Management and product (20%): product managers, team leads",
                        "HR and back-office (10%)",
                        "Teams across time zones (Moscow, Kazan, Novosibirsk)",
                    ],
                    "stack": [
                        "Budget $50K, approved by the CFO",
                        "No external event agency — done by an internal orgcommittee",
                        "Vendors: resort (1 contract), catering (1 contract), transport (2–3 buses)",
                        "Tools: Google Workspace for the calendar, HRM for registration, Slack for announcements",
                    ],
                    "architecture": [
                        "Orgcommittee: HR-director, office manager, 2 volunteers from teams",
                        "Registration flow: HRM form → diet and consents → bus / room assignments",
                        "In parallel: facilitation of the CEO + CPO strategy session",
                        "Transport: pickup from 2 points in the city + own way option",
                    ],
                    "existing": [
                        "3-hour restaurant party for 100 people is a known experience",
                        "Contacts of caterers and resorts from previous attempts",
                        "HRM form with mandatory fields (diet, allergies, T-shirt size)",
                    ],
                    "constraints": [
                        "October weather: need a plan B indoors",
                        "Remote people from other cities: flights add ~$10K",
                        "Strategy session must be no longer than 3 hours",
                        "Vendor payments strictly by contract, not earlier than 2 weeks before",
                        "CEO approves the budget and programme 2 weeks before the date",
                    ],
                    "stakeholders": [
                        "CEO — approves budget and strategy session",
                        "HR director — owns atmosphere and outcome",
                        "Team leads — help with their teams' programme",
                        "Remote employees — need transparent logistics",
                        "Vendors (resort, transport, catering) — external",
                    ],
                },
                "examples": {
                    "scenario": "A tiny example from a completely different world: booking a haircut via a barbershop app",
                    "user_story": "As a regular customer, I want to book my usual barber online, so I don't have to hunt for a slot over the phone",
                    "job_story": "When an hour opens up between meetings, I want to grab the nearest free slot with my barber, so I don't miss the chance",
                    "focus_us": "User Story — focuses on WHO the person is (a regular customer, with their own barber)",
                    "focus_js": "Job Story — focuses on the SITUATION (a sudden gap between meetings, needs a slot fast)",
                    "note": "This is NOT the ready answer to your epic — it's just a different-domain illustration of the pattern. You'll write your own User Story and Job Story for the offsite on the next two screens.",
                },
                "decomposition_examples": [
                    {
                        "label": "Option 1 — along preparation steps",
                        "subtitle": "Slice by phases: from picking a venue to the day itself",
                        "items": [
                            "Pick a resort (shortlist of 3 → finalist)",
                            "Align the budget with the CEO",
                            "Collect registration: diets, sizes, preferences",
                            "Choose transport and pickup points",
                            "Agree the menu with catering",
                            "Design the two-day programme (session + rest)",
                            "Reminders, seating, gifts",
                            "Day X — run the retreat",
                            "After — collect feedback and photos",
                        ],
                    },
                    {
                        "label": "Option 2 — from simple to rich",
                        "subtitle": "Slice by how elaborate the offsite is: start small, then decorate",
                        "items": [
                            "Minimum: one day, nearby resort, lunch + one activity",
                            "+ Overnight stay and an evening programme",
                            "+ Strategy session with the CEO and CPO",
                            "+ Role-based workshops (engineers / managers / HR)",
                            "+ Photographer, branded gifts, a highlight video",
                        ],
                    },
                    {
                        "label": "Option 3 — by SPIDR",
                        "subtitle": "Spike · Path · Interfaces · Data · Rules applied to an event",
                        "items": [
                            {"tag": "S — Spike", "text": "3 days: visit/call 3 shortlisted resorts, collect pricing and capacity, pick a finalist"},
                            {"tag": "P — Path", "text": "Simplest end-to-end: bus → arrival → lunch → one activity → dinner → sleep → breakfast → departure"},
                            {"tag": "I — Interfaces", "text": "Different audiences: office (closer, lighter logistics), remote (flights + transfer), top management (own room and programme)"},
                            {"tag": "D — Data", "text": "Menu variations: default → vegan/gluten-free → kosher/halal if needed"},
                            {"tag": "R — Rules", "text": "Seating policies for bus and rooms: by order → by teams → by «mixing» rules (newcomers + long-tenured)"},
                        ],
                    },
                    {
                        "label": "Option 4 — by 7 dimensions",
                        "subtitle": "7 axes of decomposition: pick one axis and pull it through first",
                        "items": [
                            {"tag": "1. Workflow steps", "text": "Phases: registration → logistics → accommodation → programme → report. Unpack one at a time"},
                            {"tag": "2. Business rule variations", "text": "Different rules by role: custom schedule for top management, games for engineers, facilitation for HR"},
                            {"tag": "3. Major effort", "text": "Single format vs. parallel tracks by interest — start with single, expand later"},
                            {"tag": "4. Simple/complex", "text": "Simple — 30 people in one city. Complex — 150 from 3 cities with flights"},
                            {"tag": "5. Data variations", "text": "Group sizes: pilot for 20 → 50 → 150. Iterate on the process at 20"},
                            {"tag": "6. Defer performance", "text": "Paper lists and Google Forms first; HRM automation next time"},
                            {"tag": "7. Operations/UI", "text": "Short Slack announcements first, branded event landing and QR badges later"},
                        ],
                    },
                ],
                "good_task": "Call 3 resorts from the shortlist and get a proposal for 150 people, 2 nights, catering for 5 meals, including the price and available October dates",
                "bad_task": "Organize the corporate offsite",
            },
        ],
        "primer": {
            "epic_title": "What is an «epic»?",
            "epic_text": (
                "An epic is a big task. You can't finish it in a day because it "
                "contains many small steps. When we «decompose», we slice the epic "
                "into those small steps so the team can tackle them one by one."
            ),
            "decomposition_title": "What is «decomposition»?",
            "decomposition_text": (
                "Decomposition is splitting one big goal into small tasks. A good "
                "small task is one you clearly know how to do and can verify on its "
                "own. A bad one is still a whole project in disguise."
            ),
            "good_task_label": "This looks like a small task — you can tell what to do",
            "bad_task_label": "This is still an epic — it needs more splitting",
            "start_small_hint": (
                "Don't try to be perfect. Start with 3–5 tasks — you can refine or "
                "split them later. Use the examples above as inspiration, but phrase "
                "tasks under your own epic instead of copy-pasting."
            ),
        },
        "techniques": {
            "spidr": {
                "title": "SPIDR",
                "subtitle": "5 ways to slice an epic that «won't slice»",
                "items": [
                    {"tag": "S — Spike", "text": "A time-boxed research/experiment when it's unclear how to build something"},
                    {"tag": "P — Path", "text": "Thinnest end-to-end scenario: one user path from start to finish"},
                    {"tag": "I — Interfaces", "text": "Different interfaces/channels/audiences: iOS → Android → web; customer → employee"},
                    {"tag": "D — Data", "text": "Different data: one currency → many; one category → many"},
                    {"tag": "R — Rules", "text": "Different business rules: one level/rate → many; simple rule → complex one"},
                ],
            },
            "seven_dim": {
                "title": "7 dimensions of decomposition",
                "subtitle": "7 axes (Cohn / Lawrence): if the epic is big, move along a single axis",
                "items": [
                    {"tag": "1. Workflow steps", "text": "Along the business process: step by step"},
                    {"tag": "2. Business rule variations", "text": "Along rule variations: start with one, grow gradually"},
                    {"tag": "3. Major effort", "text": "Along major effort: one platform → another, one segment → another"},
                    {"tag": "4. Simple/complex", "text": "Simple case first, complex (edge cases and exceptions) next"},
                    {"tag": "5. Data variations", "text": "Along data types/volumes: narrow first, grow later"},
                    {"tag": "6. Defer performance", "text": "Correct and slow first, then fast and optimised"},
                    {"tag": "7. Operations/UI", "text": "Basic UI and operations → dashboard, automation, analytics"},
                ],
            },
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


def _clean_tasks(raw: Optional[List]) -> List[Dict]:
    out: List[Dict] = []
    if not isinstance(raw, list):
        return out
    for idx, item in enumerate(raw[:30]):
        title = ""
        note = ""
        if isinstance(item, str):
            title = item
        elif isinstance(item, dict):
            title = str(item.get("title") or item.get("text") or "")
            note = str(item.get("note") or "")
        title = title.strip()[:240]
        note = note.strip()[:400]
        if not title:
            continue
        out.append({"id": f"t{idx+1}", "title": title, "note": note or None})
    return out


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


def _get_or_create_answer(group_id: int, participant_id: int) -> AgileTrainingProductThinkingAnswer:
    a = (
        AgileTrainingProductThinkingAnswer.query
        .filter_by(participant_id=participant_id)
        .first()
    )
    if a:
        return a
    a = AgileTrainingProductThinkingAnswer(
        group_id=group_id,
        participant_id=participant_id,
        data_json=json.dumps({}, ensure_ascii=False),
    )
    db.session.add(a)
    return a


def _serialize_answer(a: AgileTrainingProductThinkingAnswer) -> Dict:
    data = _safe_json_load(a.data_json)
    case_key = data.get("case_key")
    if case_key not in ALLOWED_CASE_KEYS:
        case_key = None
    return {
        "stage": a.stage,
        "case_key": case_key,
        "user_story": a.user_story,
        "job_story": a.job_story,
        "chosen_technique": a.chosen_technique,
        "tasks": data.get("tasks") or [],
        "improved_tasks": data.get("improved_tasks") or [],
        "notes": data.get("notes") or {},
        "ai_history": data.get("ai_history") or [],
        "ai_calls": int(a.ai_calls or 0),
        "ai_calls_remaining": max(0, AI_CALLS_LIMIT_PER_PARTICIPANT - int(a.ai_calls or 0)),
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


# --------------------------- public (participant) ---------------------------


@bp_agile_product_thinking.get("/content")
def content_public():
    locale = _resolve_locale(request.args.get("locale"), None)
    return jsonify({"locale": locale, **CONTENT.get(locale, CONTENT["ru"])})


@bp_agile_product_thinking.get("/g/<slug>/state")
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
                AgileTrainingProductThinkingAnswer.query
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
            "exercise_key": sess.exercise_key if sess else "product_thinking",
            "locale": sess.locale if sess else "ru",
        },
        "effective_locale": locale,
        "content": CONTENT.get(locale, CONTENT["ru"]),
        "ai_calls_limit": AI_CALLS_LIMIT_PER_PARTICIPANT,
        "answer": answer_payload,
    })


@bp_agile_product_thinking.post("/g/<slug>/answer")
def participant_answer(slug: str):
    """Upsert всего артефакта участника.

    body:
      {
        "participant_token": "...",
        "stage": "user_story" | ...,
        "user_story": "...",
        "job_story": "...",
        "tasks": [{"title": ".."}, ...],
        "improved_tasks": [...],
        "chosen_technique": "spidr" | "seven_dim" | null,
        "notes": {"intro": "...", "compare": "..."},
        "clear_ai_history": bool
      }
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

    if "case_key" in body:
        ck = body.get("case_key")
        if ck is None or ck == "":
            data.pop("case_key", None)
        else:
            ck = str(ck).strip().lower()
            if ck in ALLOWED_CASE_KEYS:
                data["case_key"] = ck
    if "user_story" in body:
        a.user_story = _clamp_text(body.get("user_story"))
    if "job_story" in body:
        a.job_story = _clamp_text(body.get("job_story"))
    if "stage" in body:
        stg = (body.get("stage") or "").strip().lower()
        a.stage = stg if stg in STAGE_SET else a.stage
    if "chosen_technique" in body:
        tech = body.get("chosen_technique")
        if tech is None or tech == "":
            a.chosen_technique = None
        elif str(tech).strip().lower() in ALLOWED_TECHNIQUES:
            a.chosen_technique = str(tech).strip().lower()
    if "tasks" in body:
        cleaned = _clean_tasks(body.get("tasks"))
        data["tasks"] = cleaned
        a.tasks_count = len(cleaned)
    if "improved_tasks" in body:
        data["improved_tasks"] = _clean_tasks(body.get("improved_tasks"))
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

    a.data_json = json.dumps(data, ensure_ascii=False)
    db.session.commit()

    return jsonify({"saved": True, "answer": _serialize_answer(a)})


# --------------------------- AI helper (anonymous, limited per participant) ---------------------------


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
        "Ты — доброжелательный фасилитатор тренинга по продуктовому мышлению. "
        "Ученики — новички, не обязательно из IT. Никогда не говори «правильно/неправильно» "
        "и не выставляй оценок. Вместо этого задавай 1–3 коротких уточняющих вопроса, "
        "предложи вариант формулировки и коротко объясни, что можно улучшить. "
        "Пиши кратко, дружелюбно, по-русски, без жаргона. Отвечай в Markdown: "
        "короткие абзацы, списки, **жирный** для акцентов. Не придумывай факты о кейсе."
    ),
    "en": (
        "You are a friendly facilitator for a product-thinking training. "
        "Learners are beginners, not necessarily from IT. Never say 'correct/incorrect' "
        "and never grade. Instead ask 1-3 short clarifying questions, suggest a wording, "
        "and briefly explain what could be improved. Keep it short and friendly, in English, "
        "no jargon. Reply in Markdown: short paragraphs, lists, **bold** for emphasis. "
        "Do not invent facts about the case."
    ),
}


def _ai_mode_instruction(mode: str, locale: str) -> str:
    mode = (mode or "").strip().lower()
    if locale == "en":
        table = {
            "user_story": "The learner writes a User Story in the format \"As a [who], I want [what], so that [why]\". Ask about the user, need and value; suggest a clean User Story and note what could be clearer.",
            "job_story": "The learner writes a Job Story in the format \"When [situation], I want [motivation], so that [outcome]\". Help them reword it and briefly explain the difference from a User Story.",
            "decomposition": "The learner splits a solution into tasks. For each task ask: can it be done quickly? does it have standalone value? can it be tested? Suggest how to split items that look too big.",
            "improve": "The learner is improving their decomposition. Suggest new slices using SPIDR or 7 dimensions, and point to items that could still be split further.",
            "generic": "Help the learner move on. Ask 1-2 clarifying questions and suggest the next step.",
        }
    else:
        table = {
            "user_story": "Ученик пишет User Story в формате «Как [кто], я хочу [что], чтобы [зачем]». Задай вопросы про пользователя, потребность и ценность, предложи аккуратную User Story и отметь, что можно сделать яснее.",
            "job_story": "Ученик пишет Job Story в формате «Когда [ситуация], я хочу [мотивация], чтобы [результат]». Помоги переформулировать и коротко объясни разницу с User Story.",
            "decomposition": "Ученик разбивает решение на задачи. По каждой задаче спрашивай: можно ли сделать быстро? есть ли ценность отдельно? можно ли протестировать? Предложи, как разбить слишком крупные задачи.",
            "improve": "Ученик дорабатывает декомпозицию. Предложи новые срезы по SPIDR или 7 dimensions, укажи, где можно разбить ещё.",
            "generic": "Помоги ученику двигаться дальше. Задай 1–2 уточняющих вопроса и предложи следующий шаг.",
        }
    return table.get(mode, table["generic"])


def _scripted_assist(mode: str, locale: str, user_input: str) -> str:
    """Fallback без OpenAI: заготовленные наводящие вопросы."""
    mode = (mode or "").strip().lower()
    if locale == "en":
        bank = {
            "user_story": (
                "**Questions to think about**\n\n"
                "- Who is the user? Be specific: a new customer? a regular customer?\n"
                "- What exactly do they want to do?\n"
                "- Why is it important to them right now?\n\n"
                "**Try the template**: _As a [who], I want [what], so that [why]._\n\n"
                "_Example_: As a customer, I want to book online, so I don't waste time on phone calls."
            ),
            "job_story": (
                "**Questions to think about**\n\n"
                "- When does this happen? What is the situation?\n"
                "- What is the person trying to achieve?\n"
                "- What outcome do they want?\n\n"
                "**Template**: _When [situation], I want [motivation], so that [outcome]._"
            ),
            "decomposition": (
                "**Questions per task**\n\n"
                "- Can it be done quickly?\n"
                "- Does it bring value on its own?\n"
                "- Can it be tested?\n\n"
                "If a task feels too big, try splitting by data, rules, or user types."
            ),
            "improve": (
                "**Ideas to refine**\n\n"
                "- SPIDR: split by different paths, users, data, rules.\n"
                "- 7 dimensions: different cases, different complexity, different constraints.\n\n"
                "Pick one task and try two different ways to split it."
            ),
            "generic": "Take a breath. What is the very next thing a team would need to start working on?",
        }
    else:
        bank = {
            "user_story": (
                "**Подумайте над вопросами**\n\n"
                "- Кто пользователь? Будьте конкретны: новый клиент? постоянный?\n"
                "- Что именно он хочет сделать?\n"
                "- Почему это важно прямо сейчас?\n\n"
                "**Попробуйте шаблон**: _Как [кто], я хочу [что], чтобы [зачем]._\n\n"
                "_Пример_: Как клиент, я хочу записаться онлайн, чтобы не тратить время на звонки."
            ),
            "job_story": (
                "**Вопросы для размышления**\n\n"
                "- Когда это происходит? В какой ситуации?\n"
                "- Что человек пытается сделать?\n"
                "- Какой результат он хочет получить?\n\n"
                "**Шаблон**: _Когда [ситуация], я хочу [мотивация], чтобы [результат]._"
            ),
            "decomposition": (
                "**Вопросы по каждой задаче**\n\n"
                "- Можно ли сделать быстро?\n"
                "- Есть ли ценность отдельно?\n"
                "- Можно ли протестировать?\n\n"
                "Если задача выглядит слишком большой — попробуйте разбить по данным, правилам или типам пользователей."
            ),
            "improve": (
                "**Идеи для доработки**\n\n"
                "- SPIDR: разные сценарии, пользователи, данные, правила.\n"
                "- 7 dimensions: разные кейсы, уровни сложности, ограничения.\n\n"
                "Выберите одну задачу и попробуйте разбить её двумя разными способами."
            ),
            "generic": "Сделайте паузу. Что самое первое, с чего команде было бы удобно начать?",
        }
    return bank.get(mode, bank["generic"])


@bp_agile_product_thinking.post("/g/<slug>/ai-assist")
def participant_ai_assist(slug: str):
    """Анонимный AI-помощник. Лимит — AI_CALLS_LIMIT_PER_PARTICIPANT на участника.

    body:
      {
        "participant_token": "...",
        "mode": "user_story" | "job_story" | "decomposition" | "improve" | "generic",
        "user_input": "то, что человек пока написал",
        "locale": "ru" | "en"
      }
    """
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
    reply_text = ""
    model_used = None
    stored = _safe_json_load(a.data_json)
    chosen_case_key = stored.get("case_key")
    locale_content = CONTENT.get(locale, CONTENT["ru"])
    cases_list = locale_content.get("cases") or []
    case = None
    if chosen_case_key:
        case = next((c for c in cases_list if c.get("key") == chosen_case_key), None)
    if case is None and cases_list:
        case = cases_list[0]
    if client:
        system = _SYSTEM_PROMPTS.get(locale, _SYSTEM_PROMPTS["ru"])
        instruction = _ai_mode_instruction(mode, locale)
        if case:
            case_summary = f"{case['title']}. {' '.join(case.get('context') or [])} {case.get('goal') or ''}".strip()
        else:
            case_summary = ""
        user_msg = (
            f"{instruction}\n\n"
            f"Контекст кейса: {case_summary}\n\n"
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
                max_tokens=500,
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

    # Обновляем счётчик и историю
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
    data["ai_history"] = history[-20:]  # не раздуваем JSON
    a.data_json = json.dumps(data, ensure_ascii=False)
    db.session.commit()

    return jsonify({
        "reply": reply_text,
        "model": model_used,
        "ai_calls": int(a.ai_calls or 0),
        "ai_calls_remaining": max(0, AI_CALLS_LIMIT_PER_PARTICIPANT - int(a.ai_calls or 0)),
    })


# --------------------------- facilitator ---------------------------


@bp_agile_product_thinking.get("/groups/<int:group_id>/participants")
@jwt_required()
def group_participants(group_id: int):
    """Детали каждого участника: User Story / Job Story / задачи."""
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
            AgileTrainingProductThinkingAnswer.query
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
            "user_story": a.user_story,
            "job_story": a.job_story,
            "chosen_technique": a.chosen_technique,
            "tasks": data.get("tasks") or [],
            "improved_tasks": data.get("improved_tasks") or [],
            "notes": data.get("notes") or {},
            "ai_calls": int(a.ai_calls or 0),
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        })

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants": rows,
    })


@bp_agile_product_thinking.get("/groups/<int:group_id>/results")
@jwt_required()
def group_results(group_id: int):
    """Сводка по группе — сколько участников, сколько историй, техники."""
    uid = _uid()
    g = (
        AgileTrainingGroup.query
        .join(AgileTrainingSession, AgileTrainingSession.id == AgileTrainingGroup.session_id)
        .filter(AgileTrainingGroup.id == group_id, AgileTrainingSession.owner_user_id == uid)
        .first()
    )
    if not g:
        return jsonify({"error": "Not found"}), 404

    rows = AgileTrainingProductThinkingAnswer.query.filter_by(group_id=g.id).all()

    tech_counter: Counter = Counter()
    total_tasks = 0
    total_improved = 0
    user_story_count = 0
    job_story_count = 0
    with_any = 0
    stage_counter: Counter = Counter()
    for r in rows:
        if r.user_story:
            user_story_count += 1
        if r.job_story:
            job_story_count += 1
        if r.user_story or r.job_story:
            with_any += 1
        if r.chosen_technique:
            tech_counter[r.chosen_technique] += 1
        if r.stage:
            stage_counter[r.stage] += 1
        data = _safe_json_load(r.data_json)
        total_tasks += len(data.get("tasks") or [])
        total_improved += len(data.get("improved_tasks") or [])

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants_count": g.participants.count(),
        "answers_count": len(rows),
        "user_story_count": user_story_count,
        "job_story_count": job_story_count,
        "with_any_count": with_any,
        "techniques": dict(tech_counter),
        "stages": dict(stage_counter),
        "avg_tasks": round(total_tasks / len(rows), 1) if rows else 0.0,
        "avg_improved_tasks": round(total_improved / len(rows), 1) if rows else 0.0,
    })


@bp_agile_product_thinking.get("/sessions/<int:session_id>/results")
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
    totals = {"groups": 0, "participants": 0, "answers": 0, "user_story": 0, "job_story": 0}
    techniques: Counter = Counter()
    for g in groups:
        rows = AgileTrainingProductThinkingAnswer.query.filter_by(group_id=g.id).all()
        participants_count = g.participants.count()
        totals["groups"] += 1
        totals["participants"] += participants_count
        totals["answers"] += len(rows)
        user_story_count = 0
        job_story_count = 0
        for r in rows:
            if r.user_story:
                user_story_count += 1
                totals["user_story"] += 1
            if r.job_story:
                job_story_count += 1
                totals["job_story"] += 1
            if r.chosen_technique:
                techniques[r.chosen_technique] += 1
        groups_view.append({
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            "participants_count": participants_count,
            "answers_count": len(rows),
            "user_story_count": user_story_count,
            "job_story_count": job_story_count,
        })
    return jsonify({
        "session": {"id": sess.id, "title": sess.title, "locale": sess.locale},
        "totals": totals,
        "techniques": dict(techniques),
        "groups": groups_view,
    })


@bp_agile_product_thinking.post("/groups/<int:group_id>/reset")
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
    AgileTrainingProductThinkingAnswer.query.filter_by(group_id=g.id).delete()
    db.session.commit()
    return jsonify({"reset": True})
