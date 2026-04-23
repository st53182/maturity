"""Статический контент тренажёров продуктового мышления (API → фронт).

exercise_key: product_stories | user_story_map | kanban_system
"""

from __future__ import annotations

from typing import Any, Dict


def _t(obj: Dict[str, str], locale: str) -> str:
    if not isinstance(obj, dict):
        return ""
    return obj.get(locale) or obj.get("ru") or obj.get("en") or ""


def get_workshop_content(exercise_key: str, locale: str) -> Dict[str, Any]:
    loc = locale if locale in {"ru", "en"} else "ru"
    if exercise_key == "product_stories":
        return _content_product_stories(loc)
    if exercise_key == "user_story_map":
        return _content_user_story_map(loc)
    if exercise_key == "kanban_system":
        return _content_kanban_system(loc)
    return {}


def _content_product_stories(loc: str) -> Dict[str, Any]:
    R = {
        "title": "User Story и Job Story",
        "contextCase": "Клиенты хотят записываться на приём онлайн, не звоня",
        "instability": "Система записи сейчас работает нестабильно — это отправная точка для обсуждения.",
        "example": {
            "us": "Как клиент, я хочу записаться онлайн, чтобы не тратить время на звонки",
            "js": "Когда мне нужно записаться, я хочу сделать это онлайн, чтобы быстро выбрать удобное время",
            "diff": "User Story фокусируется на роли и ценности. Job Story — на ситуации и работе, которую пользователь \"нанимает\" продукт сделать.",
        },
        "usPrompts": [
            "Кто пользователь?",
            "Что он хочет сделать?",
            "Зачем ему это?",
        ],
        "jsPrompts": [
            "Когда это происходит?",
            "Что человек хочет сделать?",
            "Зачем?",
        ],
        "decompGuidanceQ": [
            "Можно ли это сделать в разумно коротком цикле (поставить и проверить)?",
            "Есть ли польза, если поставить этот кусок отдельно?",
            "Как поймёте, что результат достигнут (тест, интервью, метрика)?",
        ],
        "epicTitle": "Эпик, который предстоит расколоть",
        "epicBody": (
            "Онлайн-запись в вашем контексте — крупный объём работы: его редко «закрывают одним куском». "
            "Как правило, его раскладывают на меньшие части с понятной ценностью — так проще планировать и не терять прозрачность. "
            "Ниже — пример, как мыслить о частях."
        ),
        "compareLead": "Нет кнопки «сдал / не сдал» — это подсказки к живому обсуждению с фасилитатором. Обратите внимание на:",
        "s10improvementLead": (
            "С учётом SPIDR / 7 dimensions уточните шаги: переименуйте, укрупните, раздробите, если это помогает. "
            "Цель — список, по которому команде и стейкхолдерам понятно, что поставляется."
        ),
        "decompExample": ["Выбрать дату", "Выбрать время", "Подтвердить запись", "Получить уведомление"],
        "toolSpidr": "SPIDR: Spikes, Performance, Internationalization, Data, Re-engineering. Отметьте, что важно уточнить в вашем контексте.",
        "tool7d": "7 dimensions: вопросы о ценности, рисках, неопределённости, зависимостях и т.д. — кратко отметьте, что важно для вас.",
        "discussionQ": [
            "Понятно ли, кто пользователь?",
            "Есть ли ценность в формулировке?",
            "Можно ли проверить результат тестом или исследованием?",
        ],
    }
    E = {
        "title": "User Story and Job Story",
        "contextCase": "Clients want to book an appointment online without calling",
        "instability": "The booking system is unstable today — a starting point for discussion.",
        "example": {
            "us": "As a client, I want to book online so I don't spend time on phone calls",
            "js": "When I need an appointment, I want to do it online so I can quickly pick a convenient time",
            "diff": "A User Story centres on a role and value. A Job Story centres on a situation and the job the user is hiring the product to do.",
        },
        "usPrompts": [
            "Who is the user?",
            "What do they want to do?",
            "Why do they need it?",
        ],
        "jsPrompts": [
            "When does it happen?",
            "What does the person want to do?",
            "Why (what outcome)?",
        ],
        "decompGuidanceQ": [
            "Can you ship and verify it in a reasonably short loop?",
            "Is there value if you deliver this part on its own?",
            "How will you know it worked (test, interview, metric)?",
        ],
        "epicTitle": "A big epic to break down",
        "epicBody": (
            "Online booking, in a real org, is usually a large body of work — rarely a single 'done' chunk. "
            "Most teams break it into smaller, checkable parts so planning stays clear. "
            "Below is an example of how to think in parts."
        ),
        "compareLead": "There is no 'pass / fail' — use these for live discussion with the facilitator. Look at:",
        "s10improvementLead": (
            "With SPIDR / 7 dimensions in mind, refine the steps: rename, split, or merge. "
            "Aim for a list that stakeholders and the team can align on as shippable value."
        ),
        "decompExample": ["Pick a date", "Pick a time", "Confirm the booking", "Get a notification"],
        "toolSpidr": "SPIDR: Spikes, Performance, Internationalization, Data, Re-engineering — note what matters in your context.",
        "tool7d": "7 dimensions: value, risk, uncertainty, dependencies — short notes on what matters for you.",
        "discussionQ": [
            "Is the user clear?",
            "Is there value in the wording?",
            "Can the outcome be tested or validated?",
        ],
    }
    S = R if loc == "ru" else E
    return {
        "exercise_key": "product_stories",
        "locale": loc,
        "intro": S,
    }


def _content_user_story_map(loc: str) -> Dict[str, Any]:
    R = {
        "title": "User Story Map",
        "processes": [
            {"key": "ticket", "label": "Покупка билета (авиа, кино…)"},
            {"key": "registration", "label": "Регистрация пользователя"},
            {"key": "order", "label": "Оформление заказа"},
            {"key": "custom", "label": "Свой вариант"},
        ],
        "example": {
            "role": "Пользователь",
            "goal": "Купить билет быстро и удобно",
            "steps": ["Выбрать направление", "Выбрать дату", "Выбрать билет", "Оплатить"],
            "stories": ["Выбрать страну", "Посмотреть цены", "Выбрать место", "Оплатить картой"],
        },
        "roleHints": ["Кто выполняет действие? Клиент, сотрудник или партнёр?"],
        "goalHints": ["Что пользователь хочет получить? Почему это важно?"],
        "backboneHints": ["С чего начинается путь? Что дальше? Как завершается?"],
    }
    E = {
        "title": "User Story Map",
        "processes": [
            {"key": "ticket", "label": "Buying a ticket (flights, cinema…)"},
            {"key": "registration", "label": "User registration"},
            {"key": "order", "label": "Placing an order"},
            {"key": "custom", "label": "Custom case"},
        ],
        "example": {
            "role": "User",
            "goal": "Buy a ticket quickly and easily",
            "steps": ["Choose route", "Choose date", "Choose ticket", "Pay"],
            "stories": ["Pick a country", "See prices", "Pick a seat", "Pay by card"],
        },
        "roleHints": ["Who acts? Client, staff or partner?"],
        "goalHints": ["What does the user want? Why does it matter?"],
        "backboneHints": ["Where does the journey start? What happens next? How does it end?"],
    }
    S = R if loc == "ru" else E
    return {"exercise_key": "user_story_map", "locale": loc, "intro": S}


def _content_kanban_system(loc: str) -> Dict[str, Any]:
    R = {
        "title": "Kanban и система",
        "context": {
            "text": "Компания: аренда недвижимости. ~50 сотрудников, разные типы клиентов (VIP, корпоративные, частные), срочные и плановые задачи, высокая вариативность запросов.",
            "unstable": "Система работы нестабильна — это не приговор, а точка для анализа и улучшения.",
        },
        "staticExample": {
            "satisfaction": "Долгие ответы, авралы, непонятные приоритеты",
            "types": "Срочные заявки, плановые, документы, эскалации",
            "arrival": "Почта, CRM, телефон; пик на старте недели",
            "team": "Роли пересекаются, ответственность размыта",
            "inventory": "Много заявок «в работе» без завершения",
            "kanban": "Доска есть, политик и WIP мало",
        },
        "staticKeys": [
            ("satisfaction", "Источники удовлетворенности (S)"),
            ("types", "Виды работ (T)"),
            ("arrival", "Паттерн прибытия работ (A)"),
            ("team", "Команда / способ организации (T)"),
            ("inventory", "Запасы / незавершёнка (I)"),
            ("kanban", "Практики Kanban (K)"),
        ],
        "cosConflict": "Если всё помечать как срочное — ничего не будет по-настоящему срочным.",
    }
    E = {
        "title": "Kanban and the system",
        "context": {
            "text": "Company: real estate rentals. ~50 people, different client types (VIP, corporate, private), urgent and planned work, high variability of requests.",
            "unstable": "The work system is unstable — not a verdict, a starting point for analysis.",
        },
        "staticExample": {
            "satisfaction": "Long waits, firefighting, unclear priorities",
            "types": "Urgent cases, planned work, documents, escalations",
            "arrival": "Email, CRM, phone; peaks at week start",
            "team": "Roles overlap, ownership fuzzy",
            "inventory": "Many items in progress without done",
            "kanban": "A board exists; few policies and WIP limits",
        },
        "staticKeys": [
            ("satisfaction", "Satisfaction (S)"),
            ("types", "Types of work (T)"),
            ("arrival", "Arrival pattern (A)"),
            ("team", "Team / how work is organised (T)"),
            ("inventory", "Inventory (I)"),
            ("kanban", "Kanban practices (K)"),
        ],
        "cosConflict": "If everything is urgent, nothing is truly urgent.",
    }
    S = R if loc == "ru" else E
    return {"exercise_key": "kanban_system", "locale": loc, "intro": S}
