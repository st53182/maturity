"""Контент тренажёра «Кто отвечает?» (упрощённый, для обсуждения с фасилитатором).

Участник видит реалистичные ситуации в работе продуктовой команды и для каждой
ставит роли по уровню вовлечённости:
  - responsible — Ответственный (и выполняет работу), может быть несколько;
  - participates — Участвующий (помогает, но не отвечает за итог);
  - informed     — Информируемый (его нужно держать в курсе);
  - not_involved — Не вовлекается.

Тут нет автоматической проверки и оценок — упражнение разбирается вместе с
фасилитатором. Поэтому в выдаче — расшифровка («почему так бывает») и типовая
ошибка для разговора, а не единственно правильный ответ.

Контент — на русском и английском.

Модуль задаёт:
  - LEVELS    — 4 уровня + локализация
  - ROLES     — 6 ролей (PO, SM, Agile-коуч, Product Manager / стрим-лидер,
                команда, Stakeholder)
  - SITUATIONS — список ситуаций c hint[role_key] = level (это «ориентир для
                обсуждения», не «правильный ответ»)
  - sanitize_selection — валидирует пришедший выбор
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set


# --------------------------- Уровни вовлечённости ---------------------------
#
# Сознательно сводим к 4 уровням «как принято разбирать с командой»:
# accountable + responsible (RACI) → один Ответственный, который и делает;
# consulted (RACI)                  → Участвующий;
# informed (RACI)                   → Информируемый;
# not involved                      → Не вовлекается.

LEVELS: List[Dict] = [
    {
        "key": "responsible",
        "title": {"ru": "Ответственный", "en": "Responsible"},
        "short": {"ru": "О", "en": "R"},
        "emoji": "👑",
        "desc": {
            "ru": "Несёт ответственность за результат и выполняет работу. На каждую ситуацию обычно ровно один.",
            "en": "Owns the outcome and does the work. Usually exactly one per situation.",
        },
    },
    {
        "key": "participates",
        "title": {"ru": "Участвующий", "en": "Participates"},
        "short": {"ru": "У", "en": "P"},
        "emoji": "🤝",
        "desc": {
            "ru": "Активно вовлечён: советует, согласовывает, помогает с экспертизой. Не отвечает за итог.",
            "en": "Actively involved: advises, aligns, contributes expertise — but doesn't own the outcome.",
        },
    },
    {
        "key": "informed",
        "title": {"ru": "Информируемый", "en": "Informed"},
        "short": {"ru": "И", "en": "I"},
        "emoji": "📣",
        "desc": {
            "ru": "Достаточно держать его в курсе: статус, итог, важные изменения. Без обсуждения по существу.",
            "en": "Just needs to be kept in the loop: status, outcome, key changes — no back-and-forth.",
        },
    },
    {
        "key": "not_involved",
        "title": {"ru": "Не вовлекается", "en": "Not involved"},
        "short": {"ru": "—", "en": "—"},
        "emoji": "⚪",
        "desc": {
            "ru": "В этой ситуации эта роль не нужна.",
            "en": "This role isn't needed for this situation.",
        },
    },
]

LEVEL_KEYS: List[str] = [l["key"] for l in LEVELS]


def valid_level_keys() -> Set[str]:
    return set(LEVEL_KEYS)


# --------------------------- Роли ---------------------------

ROLES: List[Dict] = [
    {
        "key": "po",
        "title": {"ru": "Product Owner / Владелец продукта", "en": "Product Owner"},
        "short": {"ru": "PO", "en": "PO"},
        "emoji": "📦",
        "desc": {
            "ru": "Отвечает за ценность продукта и приоритеты бэклога одной команды.",
            "en": "Owns product value and the single team's backlog priorities.",
        },
    },
    {
        "key": "sm",
        "title": {"ru": "Scrum Master", "en": "Scrum Master"},
        "short": {"ru": "SM", "en": "SM"},
        "emoji": "🧭",
        "desc": {
            "ru": "Помогает команде работать эффективно, убирает препятствия.",
            "en": "Helps the team be effective and removes impediments.",
        },
    },
    {
        "key": "pm",
        "title": {
            "ru": "Product Manager / лидер стрима",
            "en": "Product Manager / Stream lead",
        },
        "short": {"ru": "PM", "en": "PM"},
        "emoji": "🧑‍💼",
        "desc": {
            "ru": "Бизнес-лидер стрима/направления. Видит несколько команд и P&L.",
            "en": "Business lead across multiple teams. Owns the stream P&L.",
        },
    },
    {
        "key": "coach",
        "title": {"ru": "Agile-коуч / коуч стрима", "en": "Agile coach / Stream coach"},
        "short": {"ru": "Coach", "en": "Coach"},
        "emoji": "🌱",
        "desc": {
            "ru": "Учит команды и менеджмент работать по Agile, не управляет работой.",
            "en": "Teaches teams and managers how to work Agile, doesn't run delivery.",
        },
    },
    {
        "key": "team",
        "title": {"ru": "Команда разработки", "en": "Development team"},
        "short": {"ru": "Команда", "en": "Team"},
        "emoji": "👥",
        "desc": {
            "ru": "Делает продукт: проектирует, разрабатывает, тестирует, релизит.",
            "en": "Builds the product: design, code, test, release.",
        },
    },
    {
        "key": "stakeholder",
        "title": {"ru": "Заинтересованная сторона", "en": "Stakeholder"},
        "short": {"ru": "Stake", "en": "Stake"},
        "emoji": "🤝",
        "desc": {
            "ru": "Заказчик, спонсор, смежная команда, регулятор и др.",
            "en": "Customer, sponsor, partner team, regulator, etc.",
        },
    },
]

ROLE_KEYS: List[str] = [r["key"] for r in ROLES]


def valid_role_keys() -> Set[str]:
    return set(ROLE_KEYS)


# --------------------------- Ситуации ---------------------------
#
# `hint[role_key]` — это НЕ «правильный ответ», а ориентир для обсуждения.
# Не отображаем участнику автопроверкой; используем как подсказку «как это
# обычно бывает в типичной продуктовой команде» при разговоре с фасилитатором.

SITUATIONS: List[Dict] = [
    {
        "key": "team_metrics_request",
        "title": {
            "ru": "Заинтересованной стороне нужна информация о возможностях команды (метрики)",
            "en": "A stakeholder needs information about the team's capabilities (metrics)",
        },
        "subtitle": {
            "ru": "Внешний руководитель просит «дайте метрики, я хочу понимать, что вы можете».",
            "en": "An outside manager asks: 'show me metrics so I can understand what you can do'.",
        },
        "hint": {
            "po": "responsible",
            "sm": "participates",
            "pm": "participates",
            "coach": "informed",
            "team": "participates",
            "stakeholder": "informed",
        },
        "discussion": {
            "ru": "Часто метрики уходят без продуктового контекста — стейк видит цифры, но не понимает, что они значат для бизнеса. PO отвечает за «как это выглядит снаружи», SM помогает достать поставочные данные, команду спрашиваем по «как».",
            "en": "Numbers often leave the team without product context — the stakeholder sees figures but can't tell what they mean for the business. PO owns the outward picture, SM pulls delivery data, the team contributes the 'how'.",
        },
        "common_mistake": {
            "ru": "SM становится «ответственным», а PO «не в курсе» — внешним показывают цифры без продуктового смысла.",
            "en": "SM becomes 'the owner' while PO is out of the loop — stakeholders see numbers with no product context.",
        },
    },
    {
        "key": "raise_priority",
        "title": {
            "ru": "Мне необходимо повысить приоритет определённых задач",
            "en": "I need to raise the priority of specific tasks",
        },
        "subtitle": {
            "ru": "Кто-то приходит с запросом «сделайте быстрее» по конкретным задачам в бэклоге.",
            "en": "Someone shows up asking to bump specific backlog items.",
        },
        "hint": {
            "po": "responsible",
            "sm": "informed",
            "pm": "participates",
            "coach": "not_involved",
            "team": "participates",
            "stakeholder": "participates",
        },
        "discussion": {
            "ru": "Приоритеты бэклога — зона PO. PM/стейк дают контекст («почему сейчас это важнее»), команду слушаем про реализуемость, SM просто в курсе, чтобы планировать работу.",
            "en": "Backlog priorities live with the PO. PM/stakeholders bring context ('why now'), the team weighs in on feasibility, SM stays informed to plan delivery.",
        },
        "common_mistake": {
            "ru": "PM или стейк двигают задачи в бэклоге сами, в обход PO — PO теряет управление продуктом.",
            "en": "PM or a stakeholder reshuffles the backlog directly, bypassing the PO — product control is lost.",
        },
    },
    {
        "key": "calc_fte_budget",
        "title": {
            "ru": "Мне нужно посчитать бюджет по продукту, включая FTE",
            "en": "I need to calculate the product budget including FTE",
        },
        "subtitle": {
            "ru": "Полный бюджет продукта/стрима: люди, инфраструктура, подрядчики.",
            "en": "Full product/stream budget: people, infra, vendors.",
        },
        "hint": {
            "po": "participates",
            "sm": "informed",
            "pm": "responsible",
            "coach": "not_involved",
            "team": "informed",
            "stakeholder": "participates",
        },
        "discussion": {
            "ru": "Бюджет/FTE — стримовая зона PM. PO активно участвует по составу работ, команду и SM держим в курсе, стейк может уточнять рамки.",
            "en": "Budget and FTE belong to the PM's stream view. PO actively contributes scope, team and SM are informed, stakeholders may help frame constraints.",
        },
        "common_mistake": {
            "ru": "Бюджет считает PO «на коленке» — потом цифры не бьются с финмоделью.",
            "en": "PO eyeballs the budget — numbers later don't match the financial model.",
        },
    },
    {
        "key": "sync_teams",
        "title": {
            "ru": "Нужно синхронизировать команды и стейкхолдеров",
            "en": "Need to sync several teams and stakeholders",
        },
        "subtitle": {
            "ru": "Несколько команд внутри стрима делают связанные вещи — нужно общее понимание.",
            "en": "A few teams in the stream are doing related work — they need a shared picture.",
        },
        "hint": {
            "po": "participates",
            "sm": "participates",
            "pm": "responsible",
            "coach": "participates",
            "team": "informed",
            "stakeholder": "informed",
        },
        "discussion": {
            "ru": "Кросс-командный синк — обычно зона PM. PO активно участвует за свою команду, коуч помогает с форматом встречи, SM подключается по поставке.",
            "en": "Cross-team sync usually belongs to the PM. PO actively contributes for their team, the coach helps with the format, SM joins on delivery.",
        },
        "common_mistake": {
            "ru": "SM каждой команды «организует синк сам» — параллельные созвоны без общей картины.",
            "en": "Each SM organises their own sync — parallel calls with no shared picture.",
        },
    },
    {
        "key": "build_roadmap",
        "title": {
            "ru": "Нужно построить или обновить дорожную карту по продукту",
            "en": "Need to build or refresh the product roadmap",
        },
        "subtitle": {
            "ru": "Roadmap на 2–4 квартала: цели, гипотезы, крупные блоки работы.",
            "en": "A 2–4 quarter roadmap: goals, hypotheses, big chunks of work.",
        },
        "hint": {
            "po": "responsible",
            "sm": "informed",
            "pm": "participates",
            "coach": "not_involved",
            "team": "participates",
            "stakeholder": "participates",
        },
        "discussion": {
            "ru": "Roadmap — продуктовая зона. PO собирает, PM смотрит за стрим, команда говорит про реализуемость и риски, стейк — про ожидания.",
            "en": "Roadmap is product → PO. PM weighs in for the stream, team consults on feasibility, stakeholders on expectations.",
        },
        "common_mistake": {
            "ru": "Roadmap пишется «вверху» (PM/стейк), PO «доносит» — команда узнаёт постфактум, мотивация падает.",
            "en": "Roadmap is written 'at the top' and PO just communicates it — the team learns late, motivation drops.",
        },
    },
    {
        "key": "team_unhappy",
        "title": {
            "ru": "Я не удовлетворён отношениями и работой команды",
            "en": "I'm unhappy with how the team works together",
        },
        "subtitle": {
            "ru": "Конфликты, низкое доверие, плохое качество совместной работы.",
            "en": "Conflicts, low trust, poor collaboration quality.",
        },
        "hint": {
            "po": "participates",
            "sm": "responsible",
            "pm": "informed",
            "coach": "participates",
            "team": "participates",
            "stakeholder": "not_involved",
        },
        "discussion": {
            "ru": "Здоровье процесса и отношений — обычно зона SM, на тяжёлых случаях помогает коуч. PO и команда — собеседники, PM просто в курсе.",
            "en": "Process and relationship health usually sits with the SM; coach helps on harder cases. PO and team are conversation partners, PM is informed.",
        },
        "common_mistake": {
            "ru": "PM/PO «идут разбираться сами» — давление растёт, SM перестаёт работать с командой системно.",
            "en": "PM/PO 'go to fix it directly' — pressure rises, SM stops doing systemic work with the team.",
        },
    },
    {
        "key": "scope_feature",
        "title": {
            "ru": "Я хочу определить объём (scope) фичи",
            "en": "I want to define the scope of a feature",
        },
        "subtitle": {
            "ru": "Что входит в фичу, что нет, какая «достаточная версия» под цель.",
            "en": "What's in the feature, what's not, what 'enough' looks like for the goal.",
        },
        "hint": {
            "po": "responsible",
            "sm": "not_involved",
            "pm": "participates",
            "coach": "not_involved",
            "team": "participates",
            "stakeholder": "participates",
        },
        "discussion": {
            "ru": "Scope — продуктовое решение. PO решает, команда декомпозирует и говорит про сложность, PM — про бизнес-цели, стейк — про ожидания.",
            "en": "Scope is a product call. PO decides, team breaks it down and talks complexity, PM contributes business goals, stakeholders bring expectations.",
        },
        "common_mistake": {
            "ru": "Команда сама добавляет «полезные мелочи» в scope — фича расползается, релиз буксует.",
            "en": "The team silently adds 'small nice-to-haves' — scope creeps and release slips.",
        },
    },
    {
        "key": "monitor_project",
        "title": {
            "ru": "Мне необходимо организовать мониторинг проекта",
            "en": "I need to set up project monitoring",
        },
        "subtitle": {
            "ru": "Прозрачность статуса по работе для команды и за её пределами.",
            "en": "Status visibility for the team and outside.",
        },
        "hint": {
            "po": "participates",
            "sm": "responsible",
            "pm": "informed",
            "coach": "participates",
            "team": "participates",
            "stakeholder": "informed",
        },
        "discussion": {
            "ru": "Прозрачность поставки — обычно зона SM (доска, метрики, обзор). PO активно участвует по «что важно показать наружу».",
            "en": "Delivery transparency typically sits with the SM (board, metrics, review). PO actively contributes on 'what to show externally'.",
        },
        "common_mistake": {
            "ru": "PM строит свой trackeр поверх — команда заполняет 2 системы и теряет фокус.",
            "en": "PM builds a parallel tracker — the team fills two systems and loses focus.",
        },
    },
    {
        "key": "risk_strategy",
        "title": {
            "ru": "Нужно понять риски проекта и стратегию реагирования",
            "en": "Need to understand project risks and the response strategy",
        },
        "subtitle": {
            "ru": "Что может пойти не так, что мы делаем «если что», как мониторим.",
            "en": "What could go wrong, what we'll do if it does, how we'll watch for it.",
        },
        "hint": {
            "po": "participates",
            "sm": "participates",
            "pm": "responsible",
            "coach": "participates",
            "team": "participates",
            "stakeholder": "informed",
        },
        "discussion": {
            "ru": "Стратегия рисков по стриму — обычно за PM. PO собирает продуктовую часть, команду и SM подключаем по поставке и процессу.",
            "en": "Stream-level risk strategy is usually the PM's. PO assembles the product part; team and SM contribute on delivery and process.",
        },
        "common_mistake": {
            "ru": "Риски «знают только в голове PO», план реагирования не оформлен — стейк узнаёт о проблеме постфактум.",
            "en": "Risks live only in the PO's head, no documented response plan — stakeholders learn about issues too late.",
        },
    },
    {
        "key": "stakeholder_updates",
        "title": {
            "ru": "Мне нужно обеспечить заинтересованным сторонам нужный уровень обновлений",
            "en": "I need to give stakeholders the right level of updates",
        },
        "subtitle": {
            "ru": "Регулярные отчёты, демо, статус-апдейты для тех, кто не в команде.",
            "en": "Regular reports, demos, and status updates for people outside the team.",
        },
        "hint": {
            "po": "responsible",
            "sm": "participates",
            "pm": "participates",
            "coach": "informed",
            "team": "informed",
            "stakeholder": "informed",
        },
        "discussion": {
            "ru": "PO отвечает, что и как сообщаем; SM помогает форматами и фактами по поставке; PM подключается за стримовый контекст.",
            "en": "PO owns what and how we communicate; SM helps with formats and delivery facts; PM brings the stream context.",
        },
        "common_mistake": {
            "ru": "Каждый присылает свои отчёты — стейк получает 3 разные правды.",
            "en": "Everyone sends their own reports — stakeholders get three different versions of the truth.",
        },
    },
    {
        "key": "organize_meetings",
        "title": {
            "ru": "Я хочу организовать встречи — кого позвать?",
            "en": "I want to set up meetings — who should I invite?",
        },
        "subtitle": {
            "ru": "Регулярные церемонии команды и встречи со смежниками.",
            "en": "Team ceremonies and cross-team syncs.",
        },
        "hint": {
            "po": "participates",
            "sm": "responsible",
            "pm": "informed",
            "coach": "participates",
            "team": "participates",
            "stakeholder": "informed",
        },
        "discussion": {
            "ru": "Фасилитация команды — за SM, состав уточняется с PO/командой, коуч помогает с форматом.",
            "en": "Team facilitation belongs to SM; PO/team weigh in on attendees; coach helps with format.",
        },
        "common_mistake": {
            "ru": "PO собирает «свои» встречи параллельно с церемониями — у команды лоскутный календарь.",
            "en": "PO organises their own meetings in parallel — team's calendar becomes a patchwork.",
        },
    },
    {
        "key": "improve_process",
        "title": {
            "ru": "Я хочу способствовать изменениям в процессе работы",
            "en": "I want to drive improvements in the way we work",
        },
        "subtitle": {
            "ru": "Хочется поменять то, как команда работает — практики, ритуалы, договорённости.",
            "en": "Want to change how the team works — practices, rituals, agreements.",
        },
        "hint": {
            "po": "informed",
            "sm": "responsible",
            "pm": "informed",
            "coach": "participates",
            "team": "participates",
            "stakeholder": "not_involved",
        },
        "discussion": {
            "ru": "Процесс — совместная зона SM и команды, коуч помогает экспериментами; PO в курсе и подключается, если влияет на продукт.",
            "en": "Process is jointly owned by SM and team; coach supports with experiments; PO is consulted when it affects the product.",
        },
        "common_mistake": {
            "ru": "Коуч «приносит фреймворк сверху», команда не вовлечена — изменения не приживаются.",
            "en": "Coach 'imports' a framework, team isn't involved — change doesn't stick.",
        },
    },
    {
        "key": "add_backlog_items",
        "title": {
            "ru": "Мне нужно добавить новые требования от заинтересованных сторон в бэклог",
            "en": "I need to add new stakeholder requirements to the backlog",
        },
        "subtitle": {
            "ru": "Стейк пришёл с новой просьбой — куда и как её зафиксировать.",
            "en": "A stakeholder shows up with a new ask — where and how to capture it.",
        },
        "hint": {
            "po": "responsible",
            "sm": "informed",
            "pm": "participates",
            "coach": "not_involved",
            "team": "informed",
            "stakeholder": "participates",
        },
        "discussion": {
            "ru": "Бэклог принадлежит PO; он формулирует и приоритизирует. Стейк уточняет суть, PM смотрит, что это значит для стрима.",
            "en": "Backlog belongs to PO who phrases and prioritises items. Stakeholder is consulted on intent; PM checks the stream impact.",
        },
        "common_mistake": {
            "ru": "Стейк пишет задачу прямо в трекер — она «попадает в работу» в обход PO.",
            "en": "Stakeholder files the ticket directly — it sneaks into work bypassing the PO.",
        },
    },
    {
        "key": "release_dates",
        "title": {
            "ru": "Мне нужно скорректировать сроки выпуска продукта",
            "en": "I need to adjust the product release dates",
        },
        "subtitle": {
            "ru": "Бизнес-ситуация поменялась — нужны новые сроки.",
            "en": "Business situation changed — we need new dates.",
        },
        "hint": {
            "po": "responsible",
            "sm": "informed",
            "pm": "participates",
            "coach": "not_involved",
            "team": "participates",
            "stakeholder": "participates",
        },
        "discussion": {
            "ru": "Продукт-решение — за PO, но он не имеет права обещать сроки без оценки команды и согласования с PM/стейком.",
            "en": "Release timing is a product call but PO can't promise dates without team estimates and PM/stakeholder alignment.",
        },
        "common_mistake": {
            "ru": "PM сам объявляет новую дату стейкхолдерам — команда узнаёт постфактум и работает в режиме «надо к…».",
            "en": "PM announces a new date to stakeholders — team finds out after the fact and goes into 'must hit…' mode.",
        },
    },
    {
        "key": "client_demo",
        "title": {
            "ru": "Клиент хочет демо нашего продукта",
            "en": "A customer wants a demo of our product",
        },
        "subtitle": {
            "ru": "Внешний показ продукта потенциальному или реальному клиенту.",
            "en": "An external demo to a current or potential customer.",
        },
        "hint": {
            "po": "responsible",
            "sm": "informed",
            "pm": "participates",
            "coach": "not_involved",
            "team": "participates",
            "stakeholder": "informed",
        },
        "discussion": {
            "ru": "Демо клиенту — продуктовая история. PO готовит сценарий, команда показывает; PM подключается за коммерческий контекст.",
            "en": "A customer demo is a product story. PO sets the scenario, team demos; PM brings the commercial context.",
        },
        "common_mistake": {
            "ru": "Демо проводит SM «потому что у него есть слот» — пропадает продуктовый смысл.",
            "en": "SM runs the demo 'because they had a slot' — the product narrative is lost.",
        },
    },
    {
        "key": "facilitate_quarterly",
        "title": {
            "ru": "Нужно профасилитировать квартальное планирование",
            "en": "Need to facilitate quarterly planning",
        },
        "subtitle": {
            "ru": "Большая встреча на квартал: цели, ставки, синхронизация по командам.",
            "en": "A big quarterly meeting: goals, bets, cross-team alignment.",
        },
        "hint": {
            "po": "participates",
            "sm": "participates",
            "pm": "responsible",
            "coach": "participates",
            "team": "informed",
            "stakeholder": "participates",
        },
        "discussion": {
            "ru": "Кросс-командная сессия — PM как ответственный за итог, коуч ведёт фасилитацию, PO/SM активно участвуют по своей команде.",
            "en": "Cross-team session: PM owns the outcome, coach facilitates, PO/SM bring their team's view.",
        },
        "common_mistake": {
            "ru": "SM или PO «фасилитируют» квартал сами — нет нейтрального ведущего и теряется stream-уровень.",
            "en": "SM or PO 'facilitate' the quarter themselves — no neutral host, the stream-level view is lost.",
        },
    },
    {
        "key": "market_research",
        "title": {
            "ru": "Нужно изучить рынок и конкурентов",
            "en": "Need to study the market and competitors",
        },
        "subtitle": {
            "ru": "Понять, где мы относительно рынка, чем отличаемся, что выбирают клиенты.",
            "en": "Understand where we sit in the market, what's different, what customers pick.",
        },
        "hint": {
            "po": "participates",
            "sm": "not_involved",
            "pm": "responsible",
            "coach": "not_involved",
            "team": "informed",
            "stakeholder": "participates",
        },
        "discussion": {
            "ru": "Рынок и конкуренты — стримовый/продуктовый уровень PM. PO собирает продуктовую часть и фидбэк пользователей.",
            "en": "Market and competition is a PM/stream-level concern. PO gathers the product part and user feedback.",
        },
        "common_mistake": {
            "ru": "Команда «между делом» делает research — получается фрагментарно и без сравнимых критериев.",
            "en": "The team does research 'on the side' — it ends up fragmented with inconsistent criteria.",
        },
    },
    {
        "key": "monetization_model",
        "title": {
            "ru": "Нужно определить модель монетизации продукта",
            "en": "Need to define the product's monetization model",
        },
        "subtitle": {
            "ru": "Как продукт зарабатывает: подписка, реклама, freemium, B2B-контракты и т. п.",
            "en": "How the product earns: subscription, ads, freemium, B2B contracts, etc.",
        },
        "hint": {
            "po": "participates",
            "sm": "not_involved",
            "pm": "responsible",
            "coach": "not_involved",
            "team": "informed",
            "stakeholder": "participates",
        },
        "discussion": {
            "ru": "Бизнес-модель стрима — у PM, PO активно участвует с продуктовым ракурсом и UX-последствиями.",
            "en": "The stream's business model is PM-owned. PO actively contributes product fit and UX impact.",
        },
        "common_mistake": {
            "ru": "Модель «спускается» сверху без обсуждения с PO — продукт обрастает несовместимыми с UX механиками.",
            "en": "The model is dropped from above without PO input — UX-incompatible mechanics get bolted on.",
        },
    },
    {
        "key": "team_capacity",
        "title": {
            "ru": "Мне нужно понять, что команда сможет сделать в спринте",
            "en": "I need to know what the team can deliver this sprint",
        },
        "subtitle": {
            "ru": "Реалистичный объём работы на ближайший спринт/итерацию.",
            "en": "A realistic plan for the upcoming sprint.",
        },
        "hint": {
            "po": "participates",
            "sm": "informed",
            "pm": "informed",
            "coach": "not_involved",
            "team": "responsible",
            "stakeholder": "not_involved",
        },
        "discussion": {
            "ru": "Сколько и что взять — решает команда, потому что она и реализует. PO активно участвует по приоритетам.",
            "en": "How much and what to commit to is the team's call — they're the ones building it. PO actively contributes priorities.",
        },
        "common_mistake": {
            "ru": "PO «договаривается» о scope в обход команды — обещания не выполняются.",
            "en": "PO 'agrees on' scope without the team — promises don't land.",
        },
    },
    {
        "key": "production_incident",
        "title": {
            "ru": "На проде инцидент: продукт упал у клиентов",
            "en": "Production incident: customers can't use the product",
        },
        "subtitle": {
            "ru": "Срочное реагирование, восстановление работы, коммуникация наружу.",
            "en": "Urgent response, recovery, external communication.",
        },
        "hint": {
            "po": "participates",
            "sm": "informed",
            "pm": "informed",
            "coach": "not_involved",
            "team": "responsible",
            "stakeholder": "informed",
        },
        "discussion": {
            "ru": "Восстановление продукта — команда. PO держит продуктовую сторону (что говорим клиентам, какой режим), стейк/PM в курсе.",
            "en": "Recovery is the team's job. PO handles the product side (customer messaging, fallback mode); stakeholders/PM are informed.",
        },
        "common_mistake": {
            "ru": "PM или стейк «лезут в скайп» с командой во время инцидента — мешают реагированию.",
            "en": "PM or a stakeholder jumps into the team's call during the incident — slowing the response.",
        },
    },
]


def valid_situation_keys() -> Set[str]:
    return {s["key"] for s in SITUATIONS}


def _situation(key: str) -> Optional[Dict]:
    for s in SITUATIONS:
        if s["key"] == key:
            return s
    return None


# --------------------------- Локализация ---------------------------


def _loc(obj: Dict, locale: str) -> str:
    if not isinstance(obj, dict):
        return ""
    return obj.get(locale) or obj.get("ru") or obj.get("en") or ""


def get_content_for_locale(locale: str) -> Dict:
    locale = locale if locale in {"ru", "en"} else "ru"
    levels = [
        {
            "key": l["key"],
            "title": _loc(l["title"], locale),
            "short": _loc(l["short"], locale),
            "emoji": l["emoji"],
            "desc": _loc(l["desc"], locale),
        }
        for l in LEVELS
    ]
    roles = [
        {
            "key": r["key"],
            "title": _loc(r["title"], locale),
            "short": _loc(r["short"], locale),
            "emoji": r["emoji"],
            "desc": _loc(r["desc"], locale),
        }
        for r in ROLES
    ]
    situations = [
        {
            "key": s["key"],
            "title": _loc(s["title"], locale),
            "subtitle": _loc(s.get("subtitle") or {}, locale),
            "discussion": _loc(s.get("discussion") or {}, locale),
            "common_mistake": _loc(s.get("common_mistake") or {}, locale),
        }
        for s in SITUATIONS
    ]
    return {
        "levels": levels,
        "roles": roles,
        "situations": situations,
    }


# --------------------------- Валидация ---------------------------


def sanitize_selection(raw) -> Dict[str, Dict[str, Optional[str]]]:
    out: Dict[str, Dict[str, Optional[str]]] = {}
    if not isinstance(raw, dict):
        return out
    valid_situations = valid_situation_keys()
    for sit_key, roles_map in raw.items():
        if not isinstance(sit_key, str) or sit_key not in valid_situations:
            continue
        if not isinstance(roles_map, dict):
            continue
        clean: Dict[str, Optional[str]] = {}
        for role_key in ROLE_KEYS:
            val = roles_map.get(role_key)
            if val is None or val == "" or val == "none":
                clean[role_key] = None
                continue
            if isinstance(val, str) and val in LEVEL_KEYS:
                clean[role_key] = val
            else:
                clean[role_key] = None
        out[sit_key] = clean
    return out


def situation_title(key: str, locale: str) -> str:
    for s in SITUATIONS:
        if s["key"] == key:
            return _loc(s["title"], locale)
    return key


def role_title(key: str, locale: str) -> str:
    for r in ROLES:
        if r["key"] == key:
            return _loc(r["title"], locale)
    return key


def level_title(key: str, locale: str) -> str:
    for l in LEVELS:
        if l["key"] == key:
            return _loc(l["title"], locale)
    return key
