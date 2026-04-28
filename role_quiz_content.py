"""Контент тренажёра «Кто отвечает?» (RACI-quiz по ситуациям).

Участник видит реалистичные ситуации в работе продуктовой команды и для каждой
расставляет роли по уровню вовлечённости (RACI):
  - A (accountable) — главный ответственный, единственный «accountable»;
  - R (responsible) — выполняет работу;
  - C (consulted)   — у которого спрашивают мнение;
  - I (informed)    — кого нужно держать в курсе;
  - none            — не вовлечён.

Контент — на русском и английском. Все «правильные ответы» можно поправить —
это эталон, а не догма; в `rationale` объясняем, почему именно так.

Модуль задаёт:
  - LEVELS    — 5 уровней RACI + «not involved»
  - ROLES     — продуктовые роли (PO, SM, Agile-коуч, Product Manager / стрим-лидер,
                 команда, Stakeholder)
  - SITUATIONS — список ситуаций c expected[role_key] = level
  - sanitize_*, evaluate_selection — переиспользуем pattern из scrum_roles.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set


# --------------------------- Уровни RACI ---------------------------

LEVELS: List[Dict] = [
    {
        "key": "accountable",
        "title": {"ru": "Главный ответственный (A)", "en": "Accountable (A)"},
        "short": {"ru": "A", "en": "A"},
        "emoji": "👑",
        "desc": {
            "ru": "Один человек, отвечающий за исход. Если что — спрос с него.",
            "en": "Exactly one person owning the outcome. The buck stops here.",
        },
    },
    {
        "key": "responsible",
        "title": {"ru": "Выполняет (R)", "en": "Responsible (R)"},
        "short": {"ru": "R", "en": "R"},
        "emoji": "🛠",
        "desc": {
            "ru": "Делает работу руками. Может быть несколько человек.",
            "en": "Does the actual work. There can be several R's.",
        },
    },
    {
        "key": "consulted",
        "title": {"ru": "Консультируется (C)", "en": "Consulted (C)"},
        "short": {"ru": "C", "en": "C"},
        "emoji": "💬",
        "desc": {
            "ru": "С ним обсуждают до решения, его мнение влияет на выбор.",
            "en": "Two-way conversation before the decision; their input shapes it.",
        },
    },
    {
        "key": "informed",
        "title": {"ru": "Информируется (I)", "en": "Informed (I)"},
        "short": {"ru": "I", "en": "I"},
        "emoji": "📣",
        "desc": {
            "ru": "Должен знать о решении/результате, но в обсуждении не участвует.",
            "en": "Kept in the loop after the fact. No back-and-forth needed.",
        },
    },
    {
        "key": "not_involved",
        "title": {"ru": "Не вовлечён", "en": "Not involved"},
        "short": {"ru": "—", "en": "—"},
        "emoji": "⚪",
        "desc": {
            "ru": "Эта роль в данной ситуации не нужна.",
            "en": "This role is not needed for this situation.",
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
# expected[role_key] — эталонный уровень. Если уровень не указан — считаем
# "not_involved". В каждой ситуации ровно один accountable.

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
        "expected": {
            "po": "accountable",
            "sm": "responsible",
            "pm": "consulted",
            "coach": "informed",
            "team": "consulted",
            "stakeholder": "informed",
        },
        "rationale": {
            "ru": "PO отвечает, что наружу идёт корректная картина продукта; SM помогает достать метрики поставки; команду спрашиваем по «как», а не «дайте все цифры».",
            "en": "PO owns the outward picture; SM pulls delivery metrics; the team is consulted on 'how', not raw data dumps.",
        },
        "common_mistake": {
            "ru": "Часто SM делается accountable, а PO «не в курсе» — внешним показывают цифры без продуктового контекста.",
            "en": "Often SM becomes accountable while PO is out of the loop, so stakeholders see numbers with no product context.",
        },
    },
    {
        "key": "raise_priority",
        "title": {
            "ru": "Мне необходимо повысить приоритет определённых задач",
            "en": "I need to raise the priority of specific tasks",
        },
        "subtitle": {
            "ru": "В бэклоге накопились задачи, и кто-то приходит с запросом «сделайте быстрее».",
            "en": "Items pile up in the backlog and someone says: 'do these sooner'.",
        },
        "expected": {
            "po": "accountable",
            "sm": "informed",
            "pm": "consulted",
            "coach": "not_involved",
            "team": "consulted",
            "stakeholder": "consulted",
        },
        "rationale": {
            "ru": "Приоритеты бэклога — зона PO. PM/стейкхолдеров слушаем как контекст, команду спрашиваем про реализуемость, SM просто в курсе.",
            "en": "Backlog priorities are the PO's area. PM/stakeholders give context, the team is consulted on feasibility, SM is informed.",
        },
        "common_mistake": {
            "ru": "PM или стейкхолдер «двигает» задачи в бэклоге сам — PO теряет управление продуктом.",
            "en": "PM or a stakeholder reshuffles the backlog directly — PO loses control of the product.",
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
        "expected": {
            "po": "consulted",
            "sm": "informed",
            "pm": "accountable",
            "coach": "not_involved",
            "team": "informed",
            "stakeholder": "consulted",
        },
        "rationale": {
            "ru": "Бюджет/FTE — стримовая зона PM. PO консультирует по составу работ, команду и SM держим в курсе.",
            "en": "Budget and FTE belong to the PM's stream view. PO consults on scope, team and SM are informed.",
        },
        "common_mistake": {
            "ru": "Бюджет считает PO «на коленке» — потом цифры не бьются с реальной финансовой моделью.",
            "en": "PO eyeballs the budget and the numbers later don't match the real financial model.",
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
        "expected": {
            "po": "responsible",
            "sm": "consulted",
            "pm": "accountable",
            "coach": "consulted",
            "team": "informed",
            "stakeholder": "informed",
        },
        "rationale": {
            "ru": "Кросс-командная синхронизация — это PM. PO активно участвует за свою команду, коуч помогает с форматом встречи.",
            "en": "Cross-team sync is the PM's job. PO actively contributes for their team, the coach helps shape the format.",
        },
        "common_mistake": {
            "ru": "SM каждой команды «организует синк сам» — получаются параллельные созвоны без общей картины.",
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
        "expected": {
            "po": "accountable",
            "sm": "informed",
            "pm": "consulted",
            "coach": "not_involved",
            "team": "consulted",
            "stakeholder": "consulted",
        },
        "rationale": {
            "ru": "Roadmap — продукт, значит PO. PM смотрит за стрим, команду спрашиваем про реализуемость и риски, стейкхолдеров — про ожидания.",
            "en": "Roadmap is product → PO. PM weighs in for the stream, team consults on feasibility, stakeholders on expectations.",
        },
        "common_mistake": {
            "ru": "Roadmap пишут «вверху» (PM/стейкхолдер), а PO потом «доносит». Команда узнаёт всё постфактум — мотивация падает.",
            "en": "Roadmap is written 'at the top' and PO just communicates it. The team finds out late and motivation drops.",
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
        "expected": {
            "po": "consulted",
            "sm": "accountable",
            "pm": "informed",
            "coach": "responsible",
            "team": "consulted",
            "stakeholder": "not_involved",
        },
        "rationale": {
            "ru": "Здоровье процесса и отношений — SM, на тяжёлых случаях ему помогает коуч. PO и команда — собеседники, PM просто в курсе.",
            "en": "Process and relationship health is the SM's area; coach helps on harder cases. PO and team are consulted, PM is informed.",
        },
        "common_mistake": {
            "ru": "PM/PO «идёт разбираться сам» — увеличивается давление, SM перестаёт работать с командой системно.",
            "en": "PM/PO 'goes to fix it directly' — pressure rises, SM stops doing systemic work with the team.",
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
        "expected": {
            "po": "accountable",
            "sm": "not_involved",
            "pm": "consulted",
            "coach": "not_involved",
            "team": "responsible",
            "stakeholder": "consulted",
        },
        "rationale": {
            "ru": "Scope — продукт. PO решает, команда делает декомпозицию, PM консультирует по бизнес-целям, стейкхолдеры — по ожиданиям.",
            "en": "Scope is a product call. PO decides, team breaks it down, PM consults on business goals, stakeholders on expectations.",
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
        "expected": {
            "po": "consulted",
            "sm": "accountable",
            "pm": "informed",
            "coach": "consulted",
            "team": "responsible",
            "stakeholder": "informed",
        },
        "rationale": {
            "ru": "Прозрачность поставки — зона SM (доска, метрики, обзор). PO консультирует по «что важно показать наружу».",
            "en": "Delivery transparency is the SM's area (board, metrics, review). PO advises on what matters externally.",
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
        "expected": {
            "po": "responsible",
            "sm": "consulted",
            "pm": "accountable",
            "coach": "consulted",
            "team": "consulted",
            "stakeholder": "informed",
        },
        "rationale": {
            "ru": "Стратегия рисков по стриму — за PM. PO собирает продуктовую часть, команду и SM спрашиваем про поставку и процесс.",
            "en": "Stream-level risk strategy is the PM's. PO assembles the product part; team and SM consult on delivery and process.",
        },
        "common_mistake": {
            "ru": "Риски «знают только в голове PO», план реагирования не оформлен — стейкхолдеры узнают о проблеме постфактум.",
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
        "expected": {
            "po": "accountable",
            "sm": "responsible",
            "pm": "consulted",
            "coach": "informed",
            "team": "informed",
            "stakeholder": "informed",
        },
        "rationale": {
            "ru": "PO отвечает, что и как сообщаем; SM помогает форматами и фактами по поставке; PM смотрит за стримовый контекст.",
            "en": "PO owns what and how we communicate; SM helps with formats and delivery facts; PM keeps the stream context.",
        },
        "common_mistake": {
            "ru": "Каждый присылает свои отчёты — стейкхолдеры получают 3 разные правды.",
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
        "expected": {
            "po": "consulted",
            "sm": "accountable",
            "pm": "informed",
            "coach": "consulted",
            "team": "consulted",
            "stakeholder": "informed",
        },
        "rationale": {
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
        "expected": {
            "po": "consulted",
            "sm": "accountable",
            "pm": "informed",
            "coach": "responsible",
            "team": "responsible",
            "stakeholder": "not_involved",
        },
        "rationale": {
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
            "ru": "Стейкхолдер пришёл с новой просьбой — куда и как её зафиксировать.",
            "en": "A stakeholder shows up with a new ask — where and how to capture it.",
        },
        "expected": {
            "po": "accountable",
            "sm": "informed",
            "pm": "consulted",
            "coach": "not_involved",
            "team": "informed",
            "stakeholder": "consulted",
        },
        "rationale": {
            "ru": "Бэклог принадлежит PO; он формулирует и приоритизирует. Стейкхолдер уточняет суть, PM смотрит, что это значит для стрима.",
            "en": "Backlog belongs to PO who phrases and prioritises items. Stakeholder is consulted on intent; PM checks the stream impact.",
        },
        "common_mistake": {
            "ru": "Стейкхолдер пишет задачу прямо в трекер — она «попадает в работу» в обход PO.",
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
        "expected": {
            "po": "accountable",
            "sm": "informed",
            "pm": "consulted",
            "coach": "not_involved",
            "team": "consulted",
            "stakeholder": "consulted",
        },
        "rationale": {
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
        "expected": {
            "po": "accountable",
            "sm": "informed",
            "pm": "consulted",
            "coach": "not_involved",
            "team": "responsible",
            "stakeholder": "informed",
        },
        "rationale": {
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
        "expected": {
            "po": "consulted",
            "sm": "consulted",
            "pm": "accountable",
            "coach": "responsible",
            "team": "informed",
            "stakeholder": "consulted",
        },
        "rationale": {
            "ru": "Кросс-командная сессия — PM как accountable за итог, коуч ведёт фасилитацию, PO/SM активно участвуют по своей команде.",
            "en": "Cross-team session: PM is accountable for the outcome, coach facilitates, PO/SM bring their team's view.",
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
        "expected": {
            "po": "responsible",
            "sm": "not_involved",
            "pm": "accountable",
            "coach": "not_involved",
            "team": "informed",
            "stakeholder": "consulted",
        },
        "rationale": {
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
        "expected": {
            "po": "consulted",
            "sm": "not_involved",
            "pm": "accountable",
            "coach": "not_involved",
            "team": "informed",
            "stakeholder": "consulted",
        },
        "rationale": {
            "ru": "Бизнес-модель стрима — у PM, PO консультирует продуктовый ракурс и UX-последствия.",
            "en": "The stream's business model is PM-owned. PO advises on product fit and UX impact.",
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
        "expected": {
            "po": "consulted",
            "sm": "informed",
            "pm": "informed",
            "coach": "not_involved",
            "team": "accountable",
            "stakeholder": "not_involved",
        },
        "rationale": {
            "ru": "Сколько и что взять — решает команда, потому что она и реализует. PO консультирует по приоритетам.",
            "en": "How much and what to commit to is the team's call — they're the ones building it. PO consults on priorities.",
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
        "expected": {
            "po": "consulted",
            "sm": "informed",
            "pm": "informed",
            "coach": "not_involved",
            "team": "accountable",
            "stakeholder": "informed",
        },
        "rationale": {
            "ru": "Восстановление продукта — команда. PO держит продуктовую сторону (что говорим клиентам, какой режим), стейк/PM в курсе.",
            "en": "Recovery is the team's job. PO handles the product side (customer messaging, fallback mode); stakeholders/PM are informed.",
        },
        "common_mistake": {
            "ru": "PM или стейкхолдер «лезут в скайп» с командой во время инцидента — мешают реагированию.",
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
            "rationale": _loc(s["rationale"], locale),
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


def _expected_level(situation_key: str, role_key: str) -> str:
    s = _situation(situation_key)
    if not s:
        return "not_involved"
    return (s.get("expected") or {}).get(role_key, "not_involved")


def _expected_role(situation_key: str) -> Dict[str, str]:
    s = _situation(situation_key)
    if not s:
        return {}
    return dict(s.get("expected") or {})


# Близкие уровни — за них даём «жёлтый», за противоположные — «красный».
_NEIGHBOURS = {
    ("accountable", "responsible"),
    ("responsible", "accountable"),
    ("consulted", "informed"),
    ("informed", "consulted"),
    ("responsible", "consulted"),
    ("consulted", "responsible"),
    ("informed", "not_involved"),
    ("not_involved", "informed"),
}


def _classify(expected: str, picked: Optional[str]) -> str:
    """→ 'green' | 'yellow' | 'red' | 'missing'."""
    if picked is None:
        return "green" if expected == "not_involved" else "missing"
    if picked == expected:
        return "green"
    if (expected, picked) in _NEIGHBOURS:
        return "yellow"
    return "red"


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


def evaluate_selection(selection: Dict[str, Dict[str, Optional[str]]]) -> Dict:
    """Сравнивает выбор с эталоном.

    Возвращает структуру, аналогичную scrum_roles: per_role, total и
    разбор по каждой ситуации. Дополнительно отмечаем:
      - missing_accountable: ни одной A не выставлено;
      - extra_accountable: A назначена нескольким ролям сразу.
    """
    per_role = {rk: {"green": 0, "yellow": 0, "red": 0, "missing": 0} for rk in ROLE_KEYS}
    total = {"green": 0, "yellow": 0, "red": 0, "missing": 0}
    situations_eval: Dict[str, Dict] = {}
    answered = 0
    accountable_correct = 0

    for sit in SITUATIONS:
        sk = sit["key"]
        roles_eval: Dict[str, Dict] = {}
        colors_here: List[str] = []
        picked_count_a = 0
        picked_a_correct = False
        sel_for_situation = selection.get(sk) or {}
        any_picked = False
        for rk in ROLE_KEYS:
            expected = _expected_level(sk, rk)
            picked = sel_for_situation.get(rk)
            if picked:
                any_picked = True
                if picked == "accountable":
                    picked_count_a += 1
            color = _classify(expected, picked)
            roles_eval[rk] = {"expected": expected, "picked": picked, "color": color}
            per_role[rk][color] += 1
            total[color] += 1
            colors_here.append(color)
            if expected == "accountable" and picked == "accountable":
                picked_a_correct = True

        if any_picked:
            answered += 1
            if picked_a_correct and picked_count_a == 1:
                accountable_correct += 1

        if "red" in colors_here:
            sit_color = "red"
        elif "missing" in colors_here:
            sit_color = "red"
        elif "yellow" in colors_here:
            sit_color = "yellow"
        else:
            sit_color = "green"
        situations_eval[sk] = {
            "roles": roles_eval,
            "color": sit_color,
            "extra_accountable": picked_count_a > 1,
            "missing_accountable": picked_count_a == 0,
        }

    cells = len(SITUATIONS) * len(ROLE_KEYS)
    score = total["green"] * 2 + total["yellow"] * 1 - total["red"] * 1
    max_score = cells * 2
    health_pct = round(max(score, 0) / max_score * 100) if max_score > 0 else 0
    return {
        "situations": situations_eval,
        "per_role": per_role,
        "total": {**total, "max": max_score, "score": score, "health_pct": health_pct},
        "answered": answered,
        "accountable_correct": accountable_correct,
    }


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
