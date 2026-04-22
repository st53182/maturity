"""Контент тренажёра MVP → MMP → MLP.

Каждый кейс — это гипотеза и набор фич. У каждой фичи:
  - weight: "critical" | "improve" | "optional"
      * critical  — без этой фичи проверить гипотезу невозможно
      * improve   — делает продукт пригодным к релизу (MMP) / приятным (MLP)
      * optional  — «wishlist», редко оправдывает себя на ранних этапах
  - expected_stage: "mvp" | "mmp" | "mlp" | "skip"
      * на какой итерации фича обычно уместна по экспертной версии.
      * `skip` — честно говоря, не нужно вообще, пример «красивая анимация
        загрузки» на этапе проверки идеи.

Оценка участника в каждой итерации (см. `evaluate_iteration`):
  MVP  — максимум 3 фичи; цель: проверить гипотезу.
  MMP  — всего до 6 фич; цель: продукт, пригодный к релизу.
  MLP  — всего до 9 фич; цель: продукт, который нравится пользователям.

Все строки локализованы RU / EN — фронт запрашивает нужную локаль.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set


STAGE_KEYS: List[str] = ["mvp", "mmp", "mlp"]
STAGE_LIMITS: Dict[str, int] = {"mvp": 3, "mmp": 6, "mlp": 9}
WEIGHT_KEYS: Set[str] = {"critical", "improve", "optional"}


# --------------------------- Кейсы ---------------------------

CASES: List[Dict] = [
    # ---------------- TAXI ----------------
    {
        "key": "taxi",
        "category": {"ru": "Сервисы", "en": "Services"},
        "title": {
            "ru": "Приложение для заказа такси",
            "en": "Taxi-hailing app",
        },
        "hypothesis": {
            "ru": "Если пользователи смогут заказывать такси через приложение, они перестанут звонить оператору.",
            "en": "If users can order a taxi through an app, they will stop calling the dispatcher.",
        },
        "context": {
            "ru": [
                "ресурсы команды ограничены: 1 спринт",
                "нужно быстро проверить идею, а не запускать флот",
                "у вас уже есть готовые водители и колл-центр для бэкапа",
            ],
            "en": [
                "limited team resources: 1 sprint",
                "need to validate the idea quickly, not launch a fleet",
                "you already have drivers and a fallback call center",
            ],
        },
        "features": [
            {"key": "pickup", "weight": "critical", "expected_stage": "mvp",
             "title": {"ru": "Выбор точки посадки", "en": "Pickup point selection"},
             "desc": {"ru": "На карте или адресом — куда приехать водителю", "en": "On map or by address — where the driver should arrive"}},
            {"key": "callcar", "weight": "critical", "expected_stage": "mvp",
             "title": {"ru": "Вызов машины", "en": "Request a car"},
             "desc": {"ru": "Кнопка, которая отправляет заказ", "en": "Button that sends the order"}},
            {"key": "price", "weight": "critical", "expected_stage": "mvp",
             "title": {"ru": "Расчёт стоимости", "en": "Fare estimate"},
             "desc": {"ru": "Примерная цена до подтверждения заказа", "en": "Approximate price before confirming"}},
            {"key": "map", "weight": "improve", "expected_stage": "mmp",
             "title": {"ru": "Карта с машиной", "en": "Live map with car"},
             "desc": {"ru": "Видно, где сейчас водитель", "en": "See where the driver is right now"}},
            {"key": "payment", "weight": "improve", "expected_stage": "mmp",
             "title": {"ru": "Оплата в приложении", "en": "In-app payment"},
             "desc": {"ru": "Безналичная оплата картой", "en": "Cashless card payment"}},
            {"key": "class", "weight": "improve", "expected_stage": "mmp",
             "title": {"ru": "Выбор класса машины", "en": "Car class selection"},
             "desc": {"ru": "Эконом / комфорт / бизнес", "en": "Economy / Comfort / Business"}},
            {"key": "history", "weight": "improve", "expected_stage": "mlp",
             "title": {"ru": "История поездок", "en": "Ride history"},
             "desc": {"ru": "Быстрый повтор частых маршрутов", "en": "Quickly repeat frequent routes"}},
            {"key": "rating", "weight": "improve", "expected_stage": "mlp",
             "title": {"ru": "Рейтинг водителя", "en": "Driver rating"},
             "desc": {"ru": "Отзыв и оценка после поездки", "en": "Feedback and rating after the ride"}},
            {"key": "loyalty", "weight": "optional", "expected_stage": "mlp",
             "title": {"ru": "Программа лояльности", "en": "Loyalty program"},
             "desc": {"ru": "Бонусные баллы за поездки", "en": "Bonus points for rides"}},
            {"key": "chat", "weight": "optional", "expected_stage": "skip",
             "title": {"ru": "Чат с водителем", "en": "Chat with the driver"},
             "desc": {"ru": "Встроенный мессенджер вместо звонка", "en": "Built-in messenger instead of a call"}},
            {"key": "skins", "weight": "optional", "expected_stage": "skip",
             "title": {"ru": "Тёмная тема и кастомизация", "en": "Dark theme and skins"},
             "desc": {"ru": "Настройки внешнего вида", "en": "Visual appearance settings"}},
        ],
        # Что сказать участнику в каждой итерации в зависимости от результата.
        "reactions": {
            "mvp": {
                "success": {
                    "ru": "«В целом работает: вбил адрес, нажал кнопку, приехала машина». Гипотеза подтверждена.",
                    "en": "'It basically works: typed address, tapped, a car arrived.' Hypothesis confirmed.",
                },
                "partial": {
                    "ru": "«Кажется, можно заказать, но непонятно, сколько будет стоить» — пользователи переключаются обратно на звонок.",
                    "en": "'I can maybe order, but I don't know the price' — users switch back to phone calls.",
                },
                "fail": {
                    "ru": "«Я не понимаю, как вообще оформить поездку». Звонков оператору меньше не стало.",
                    "en": "'I don't understand how to order at all.' Call volume didn't drop.",
                },
            },
            "mmp": {
                "success": {
                    "ru": "Продукт можно выпускать на широкую аудиторию: заказ, оплата, статус поездки работают.",
                    "en": "Product is ready for a public launch: ordering, payment and ride status work.",
                },
                "partial": {
                    "ru": "Пользоваться можно, но деньги брать неудобно — релиз блокируют платежи.",
                    "en": "Usable, but monetisation is awkward — payments block the release.",
                },
                "fail": {
                    "ru": "Ключевые сценарии ломаются — релизить рано.",
                    "en": "Core flows still break — too early to release.",
                },
            },
            "mlp": {
                "success": {
                    "ru": "Пользователи возвращаются сами и рекомендуют приложение. Это та «приятность», которой не хватало.",
                    "en": "Users come back on their own and recommend the app. That's the delight that was missing.",
                },
                "partial": {
                    "ru": "Продукт работает, но повторных заказов мало — нет ощущения удобства и персонализации.",
                    "en": "Product works, but repeat usage is low — no feeling of personal comfort.",
                },
                "fail": {
                    "ru": "Пользователи не видят разницы с обычным вызовом такси по телефону.",
                    "en": "Users don't see the difference from just calling a taxi.",
                },
            },
        },
    },
    # ---------------- FOOD DELIVERY ----------------
    {
        "key": "food",
        "category": {"ru": "Сервисы", "en": "Services"},
        "title": {
            "ru": "Доставка еды из ресторанов",
            "en": "Restaurant food delivery",
        },
        "hypothesis": {
            "ru": "Если клиенты смогут заказывать еду из ресторанов через приложение, рестораны получат дополнительный канал продаж.",
            "en": "If customers can order restaurant food through an app, restaurants will gain a new sales channel.",
        },
        "context": {
            "ru": [
                "партнёрские рестораны уже готовы подключиться",
                "собственных курьеров пока нет — заказы забирают сами клиенты",
                "нужно быстро проверить готовность платить комиссию",
            ],
            "en": [
                "partner restaurants are ready to join",
                "no own courier fleet — customers pick up themselves",
                "need to validate willingness to pay commission",
            ],
        },
        "features": [
            {"key": "menu", "weight": "critical", "expected_stage": "mvp",
             "title": {"ru": "Меню ресторана", "en": "Restaurant menu"},
             "desc": {"ru": "Блюда, описания и цены", "en": "Dishes, descriptions and prices"}},
            {"key": "order", "weight": "critical", "expected_stage": "mvp",
             "title": {"ru": "Оформление заказа", "en": "Place an order"},
             "desc": {"ru": "Положить блюдо в корзину и отправить", "en": "Add to cart and submit the order"}},
            {"key": "restaurants", "weight": "critical", "expected_stage": "mvp",
             "title": {"ru": "Список ресторанов рядом", "en": "Nearby restaurants"},
             "desc": {"ru": "Поиск заведений по городу / району", "en": "Browse venues by city / area"}},
            {"key": "pay_online", "weight": "improve", "expected_stage": "mmp",
             "title": {"ru": "Онлайн-оплата", "en": "Online payment"},
             "desc": {"ru": "Оплата картой в приложении", "en": "Pay by card in the app"}},
            {"key": "delivery", "weight": "improve", "expected_stage": "mmp",
             "title": {"ru": "Доставка курьером", "en": "Courier delivery"},
             "desc": {"ru": "Подключить внешних курьеров", "en": "Integrate external couriers"}},
            {"key": "status", "weight": "improve", "expected_stage": "mmp",
             "title": {"ru": "Статус заказа", "en": "Order status"},
             "desc": {"ru": "Готовится / забирается / в пути", "en": "Cooking / picking up / on the way"}},
            {"key": "reviews", "weight": "improve", "expected_stage": "mlp",
             "title": {"ru": "Отзывы на блюда", "en": "Dish reviews"},
             "desc": {"ru": "Рейтинг и комментарии посетителей", "en": "Ratings and customer comments"}},
            {"key": "favourites", "weight": "improve", "expected_stage": "mlp",
             "title": {"ru": "Избранные рестораны", "en": "Favourite restaurants"},
             "desc": {"ru": "Быстрый доступ к любимым заведениям", "en": "Quick access to favourite venues"}},
            {"key": "recs", "weight": "improve", "expected_stage": "mlp",
             "title": {"ru": "Персональные рекомендации", "en": "Personal recommendations"},
             "desc": {"ru": "Подборки на основе истории заказов", "en": "Suggestions based on order history"}},
            {"key": "gamif", "weight": "optional", "expected_stage": "skip",
             "title": {"ru": "Геймификация и ачивки", "en": "Gamification & achievements"},
             "desc": {"ru": "Бейджи за количество заказов", "en": "Badges for order count"}},
            {"key": "group_order", "weight": "optional", "expected_stage": "skip",
             "title": {"ru": "Групповой заказ с друзьями", "en": "Group order with friends"},
             "desc": {"ru": "Совместное редактирование корзины", "en": "Shared cart editing"}},
        ],
        "reactions": {
            "mvp": {
                "success": {
                    "ru": "«Нашёл ресторан, выбрал еду, оформил заказ — удобно». Рестораны получают первые оплаты.",
                    "en": "'Found a restaurant, picked food, placed an order — convenient.' Restaurants get first payments.",
                },
                "partial": {
                    "ru": "«Нашёл ресторан, но непонятно, заказ вообще дошёл или нет». Гипотеза подтверждается частично.",
                    "en": "'Found a restaurant, but I can't tell if the order reached them.' Hypothesis partially confirmed.",
                },
                "fail": {
                    "ru": "«Что этот экран должен делать?» Рестораны не получают ни одного заказа.",
                    "en": "'What is this screen supposed to do?' Restaurants receive zero orders.",
                },
            },
            "mmp": {
                "success": {
                    "ru": "Рестораны готовы платить комиссию — понятен статус заказа, есть доставка и онлайн-оплата.",
                    "en": "Restaurants are willing to pay commission — order status, delivery and online payment are in place.",
                },
                "partial": {
                    "ru": "Рестораны заказы получают, но не могут управлять доставкой и деньгами — жалобы.",
                    "en": "Restaurants receive orders but cannot manage delivery and payments — complaints rise.",
                },
                "fail": {
                    "ru": "Бизнес-ценности нет: клиенты жалуются, рестораны тоже.",
                    "en": "No business value: both customers and restaurants complain.",
                },
            },
            "mlp": {
                "success": {
                    "ru": "Пользователи возвращаются за избранным и рекомендациями, LTV растёт.",
                    "en": "Users come back for favourites and recommendations, LTV grows.",
                },
                "partial": {
                    "ru": "Заказать можно, но повторных покупок мало — нет причины возвращаться.",
                    "en": "They can order, but repeat purchases are low — no reason to come back.",
                },
                "fail": {
                    "ru": "Пользователи сравнивают с конкурентами и уходят — приложение не вызывает эмоций.",
                    "en": "Users compare with competitors and leave — the app doesn't trigger any emotion.",
                },
            },
        },
    },
    # ---------------- ONLINE LEARNING ----------------
    {
        "key": "courses",
        "category": {"ru": "EdTech", "en": "EdTech"},
        "title": {
            "ru": "Платформа онлайн-курсов",
            "en": "Online courses platform",
        },
        "hypothesis": {
            "ru": "Если дать людям возможность проходить короткие онлайн-курсы, они будут платить за обучение новым навыкам.",
            "en": "If people can take short online courses, they will pay to learn new skills.",
        },
        "context": {
            "ru": [
                "уже есть 3 автора контента",
                "нет собственной LMS, всё пока на Google-документах",
                "нужно проверить, готовы ли платить именно за этот формат",
            ],
            "en": [
                "3 content authors are already on board",
                "no LMS — everything still lives in Google docs",
                "need to validate willingness to pay for this format",
            ],
        },
        "features": [
            {"key": "catalog", "weight": "critical", "expected_stage": "mvp",
             "title": {"ru": "Каталог курсов", "en": "Course catalog"},
             "desc": {"ru": "Список доступных курсов с описанием", "en": "List of available courses with descriptions"}},
            {"key": "lessons", "weight": "critical", "expected_stage": "mvp",
             "title": {"ru": "Просмотр уроков", "en": "Lesson viewer"},
             "desc": {"ru": "Видео / текст одного урока", "en": "Video / text of a lesson"}},
            {"key": "paywall", "weight": "critical", "expected_stage": "mvp",
             "title": {"ru": "Оплата курса", "en": "Course payment"},
             "desc": {"ru": "Pay-wall, без этого гипотезу не проверить", "en": "Pay-wall — hypothesis impossible without it"}},
            {"key": "progress", "weight": "improve", "expected_stage": "mmp",
             "title": {"ru": "Прогресс по курсу", "en": "Course progress"},
             "desc": {"ru": "Пройдено X из Y уроков", "en": "X of Y lessons completed"}},
            {"key": "quiz", "weight": "improve", "expected_stage": "mmp",
             "title": {"ru": "Проверочные тесты", "en": "Quizzes"},
             "desc": {"ru": "Вопросы после урока", "en": "Questions after a lesson"}},
            {"key": "certificate", "weight": "improve", "expected_stage": "mmp",
             "title": {"ru": "Сертификат по завершении", "en": "Completion certificate"},
             "desc": {"ru": "PDF со статусом «пройдено»", "en": "PDF certifying completion"}},
            {"key": "community", "weight": "improve", "expected_stage": "mlp",
             "title": {"ru": "Сообщество студентов", "en": "Student community"},
             "desc": {"ru": "Обсуждения по урокам", "en": "Lesson discussions"}},
            {"key": "reminders", "weight": "improve", "expected_stage": "mlp",
             "title": {"ru": "Напоминания об учёбе", "en": "Study reminders"},
             "desc": {"ru": "Push: «не забывай возвращаться к курсу»", "en": "Push: 'don't forget to continue the course'"}},
            {"key": "mentor", "weight": "improve", "expected_stage": "mlp",
             "title": {"ru": "Живой наставник / Q&A", "en": "Live mentor / Q&A"},
             "desc": {"ru": "Ответы на вопросы от автора", "en": "Answers from the author"}},
            {"key": "gamif", "weight": "optional", "expected_stage": "skip",
             "title": {"ru": "Рейтинг студентов и бейджи", "en": "Student leaderboard & badges"},
             "desc": {"ru": "Геймификация прогресса", "en": "Progress gamification"}},
            {"key": "offline", "weight": "optional", "expected_stage": "skip",
             "title": {"ru": "Скачивание уроков офлайн", "en": "Offline lesson download"},
             "desc": {"ru": "Смотреть без интернета", "en": "Watch without internet"}},
        ],
        "reactions": {
            "mvp": {
                "success": {
                    "ru": "«Нашёл курс, оплатил, смотрю уроки» — первые покупатели есть, гипотеза о готовности платить подтверждается.",
                    "en": "'Found a course, paid, watching lessons' — first buyers appear, paying hypothesis confirmed.",
                },
                "partial": {
                    "ru": "«Уроки есть, но не понимаю, где оплатить» — покупок мало, гипотеза подтверждается слабо.",
                    "en": "'Lessons are here, but I can't find how to pay' — few purchases, hypothesis weakly supported.",
                },
                "fail": {
                    "ru": "Пользователи не доходят до оплаты — не получается проверить именно гипотезу «готовы платить».",
                    "en": "Users never reach the pay-wall — cannot validate the 'willing to pay' hypothesis.",
                },
            },
            "mmp": {
                "success": {
                    "ru": "Курсы можно продавать в B2B и SMB: есть прогресс, проверки знаний и сертификат.",
                    "en": "Courses can be sold to B2B / SMB: progress, quizzes and certificate are in place.",
                },
                "partial": {
                    "ru": "Продать можно, но студенты бросают курсы — страдает продление и LTV.",
                    "en": "Sellable, but students drop out — retention and LTV suffer.",
                },
                "fail": {
                    "ru": "Продукт сложно продавать: нет инструментов, чтобы студент дошёл до конца.",
                    "en": "Hard to sell: no tooling to help a student reach the end.",
                },
            },
            "mlp": {
                "success": {
                    "ru": "Студенты сами зовут друзей, рекомендуют курсы, возвращаются за следующими программами.",
                    "en": "Students invite friends, recommend courses and come back for new programmes.",
                },
                "partial": {
                    "ru": "Курсы оплачивают, но без эмоций: сообщества и поддержки не хватает.",
                    "en": "They pay, but without emotion: no community and no support.",
                },
                "fail": {
                    "ru": "Впечатление «ещё одной платформы курсов», переизбыток информации, уход к конкурентам.",
                    "en": "Feels like 'yet another course platform', users churn to competitors.",
                },
            },
        },
    },
]


def valid_case_keys() -> Set[str]:
    return {c["key"] for c in CASES}


def get_cases_for_locale(locale: str) -> List[Dict]:
    """Возвращает кейсы с уже локализованными строками для фронтенда."""
    loc = "en" if locale == "en" else "ru"
    out: List[Dict] = []
    for c in CASES:
        features = []
        for f in c["features"]:
            features.append({
                "key": f["key"],
                "title": f["title"][loc],
                "desc": f["desc"][loc],
                "weight": f["weight"],
                "expected_stage": f["expected_stage"],
            })
        out.append({
            "key": c["key"],
            "category": c["category"][loc],
            "title": c["title"][loc],
            "hypothesis": c["hypothesis"][loc],
            "context": list(c["context"][loc]),
            "features": features,
            "stage_limits": dict(STAGE_LIMITS),
        })
    return out


def _case(case_key: str) -> Optional[Dict]:
    for c in CASES:
        if c["key"] == case_key:
            return c
    return None


def _feature_map(case: Dict) -> Dict[str, Dict]:
    return {f["key"]: f for f in case["features"]}


# --------------------------- Оценка итерации ---------------------------


def _count_by_weight(selected_keys: List[str], feature_map: Dict[str, Dict]) -> Dict[str, int]:
    out = {"critical": 0, "improve": 0, "optional": 0, "skip": 0}
    for k in selected_keys:
        f = feature_map.get(k)
        if not f:
            continue
        out[f["weight"]] = out.get(f["weight"], 0) + 1
        if f.get("expected_stage") == "skip":
            out["skip"] += 1
    return out


def evaluate_iteration(case_key: str, stage: str, selected_keys: List[str]) -> Dict:
    """Возвращает результат одной итерации:
      - status: "success" | "partial" | "fail"
      - reaction (локализуется на клиенте — возвращаем просто статус + текст)
      - antipatterns: список ключей типовых ошибок
      - hint_keys: какие важные фичи забыли (feature keys)
    """
    case = _case(case_key)
    if case is None or stage not in STAGE_KEYS:
        return {
            "status": "fail",
            "reaction": None,
            "antipatterns": [],
            "hint_keys": [],
            "counts": {"critical": 0, "improve": 0, "optional": 0, "skip": 0},
        }

    fmap = _feature_map(case)
    # Только валидные и уникальные ключи
    selected_keys = [k for k in dict.fromkeys(selected_keys) if k in fmap]
    counts = _count_by_weight(selected_keys, fmap)
    limit = STAGE_LIMITS[stage]
    selected_keys = selected_keys[:limit]
    counts = _count_by_weight(selected_keys, fmap)

    total_critical = sum(1 for f in case["features"] if f["weight"] == "critical")

    antipatterns: List[str] = []
    hint_keys: List[str] = []

    # --- критичные забытые
    missing_critical = [
        f["key"] for f in case["features"]
        if f["weight"] == "critical" and f["key"] not in selected_keys
    ]

    if stage == "mvp":
        # антипаттерн «слишком много некритичных» — 2+ optional внутри MVP
        if counts["optional"] >= 2:
            antipatterns.append("too_many_optional_mvp")
        # «нет ключевой функции» — не хватает хотя бы одной critical
        if missing_critical:
            antipatterns.append("missing_critical")
        # «MVP раздут skip-фичами (то, что не нужно вообще)»
        if counts["skip"] >= 1:
            antipatterns.append("vanity_feature_mvp")

        if counts["critical"] >= total_critical:
            status = "success"
        elif counts["critical"] >= max(1, total_critical - 1):
            status = "partial"
        else:
            status = "fail"
        hint_keys = missing_critical[:3]

    elif stage == "mmp":
        if missing_critical:
            antipatterns.append("mmp_missing_critical")
        if counts["improve"] < 1:
            antipatterns.append("mmp_no_improvements")
        if counts["optional"] >= 3:
            antipatterns.append("mmp_bloat")

        has_all_critical = not missing_critical
        has_enough_improve = counts["improve"] >= 2
        if has_all_critical and has_enough_improve:
            status = "success"
        elif has_all_critical:
            status = "partial"
        else:
            status = "fail"
        # подсказки: критичные + типичные improve-фичи для MMP, которых нет
        mmp_improve_keys = [
            f["key"] for f in case["features"]
            if f["weight"] == "improve" and f.get("expected_stage") == "mmp"
               and f["key"] not in selected_keys
        ]
        hint_keys = (missing_critical + mmp_improve_keys)[:3]

    else:  # mlp
        if missing_critical:
            antipatterns.append("mlp_missing_critical")
        if counts["improve"] < 3:
            antipatterns.append("mlp_no_delight")
        if counts["skip"] >= 1:
            antipatterns.append("mlp_vanity")

        has_all_critical = not missing_critical
        if has_all_critical and counts["improve"] >= 4:
            status = "success"
        elif has_all_critical and counts["improve"] >= 2:
            status = "partial"
        else:
            status = "fail"
        mlp_improve_keys = [
            f["key"] for f in case["features"]
            if f["weight"] == "improve" and f.get("expected_stage") == "mlp"
               and f["key"] not in selected_keys
        ]
        hint_keys = (missing_critical + mlp_improve_keys)[:3]

    return {
        "status": status,
        "reaction_key": stage + "." + status,
        "reaction_text_locales": case["reactions"][stage][status],
        "antipatterns": antipatterns,
        "hint_keys": hint_keys,
        "counts": counts,
        "limit": limit,
    }


# --------------------------- Сводный скоринг ---------------------------


STATUS_SCORE = {"success": 2, "partial": 1, "fail": 0}


def iteration_score(status: str) -> int:
    return STATUS_SCORE.get(status, 0)


def total_score(mvp_status: Optional[str], mmp_status: Optional[str], mlp_status: Optional[str]) -> int:
    """Сумма баллов по всем трём итерациям (0..6)."""
    return (
        iteration_score(mvp_status or "")
        + iteration_score(mmp_status or "")
        + iteration_score(mlp_status or "")
    )
