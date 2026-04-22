"""Контент для упражнения Cynefin в Agile Training.

Содержит 8 универсальных кейсов (не только про IT), типовые стратегии
действий для каждого домена и текстовые последствия ошибочного выбора.
Вся логика — чистые функции, не зависящие от Flask-контекста.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set


DOMAIN_KEYS: List[str] = ["obvious", "complicated", "complex", "chaotic"]


# ---- типовые стратегии по доменам ----
#
# У каждого домена — 3 универсальные стратегии + возможность ввести свою.
# Ключи не локализуются и хранятся в БД; `label_ru`/`label_en` — для UI.
STRATEGIES: Dict[str, List[Dict]] = {
    "obvious": [
        {"key": "follow_standard",
         "label_ru": "Следовать стандарту / инструкции",
         "label_en": "Follow the standard / best practice"},
        {"key": "train_staff",
         "label_ru": "Обучить сотрудников соблюдению",
         "label_en": "Train people to comply with the rules"},
        {"key": "automate",
         "label_ru": "Автоматизировать исполнение процесса",
         "label_en": "Automate execution of the process"},
    ],
    "complicated": [
        {"key": "expert_analysis",
         "label_ru": "Провести анализ с экспертами",
         "label_en": "Run an expert analysis"},
        {"key": "plan_and_execute",
         "label_ru": "Составить детальный план и следовать ему",
         "label_en": "Build a detailed plan and execute it"},
        {"key": "data_driven",
         "label_ru": "Собрать данные и выбрать лучший вариант",
         "label_en": "Gather data and pick the best option"},
    ],
    "complex": [
        {"key": "run_experiment",
         "label_ru": "Запустить пилот / эксперимент",
         "label_en": "Run a pilot / experiment"},
        {"key": "short_iterations",
         "label_ru": "Работать короткими итерациями",
         "label_en": "Work in short iterations"},
        {"key": "feedback_loops",
         "label_ru": "Быстрая обратная связь и адаптация",
         "label_en": "Fast feedback loops and adaptation"},
    ],
    "chaotic": [
        {"key": "stabilize",
         "label_ru": "Немедленно стабилизировать ситуацию",
         "label_en": "Stabilise the situation immediately"},
        {"key": "command",
         "label_ru": "Возглавить и быстро действовать",
         "label_en": "Take command and act fast"},
        {"key": "inform",
         "label_ru": "Проинформировать ключевые стороны",
         "label_en": "Inform key stakeholders"},
    ],
}


# ---- 8 кейсов ----
CASES: List[Dict] = [
    {
        "key": "gov_services",
        "category": {"ru": "Гос. управление", "en": "Public sector"},
        "title": {"ru": "Новые правила госуслуг",
                  "en": "New rules for public services"},
        "scenario": {
            "ru": "В регионе вводят новые правила оказания госуслуг. "
                  "Требования сверху меняются каждые несколько недель, "
                  "сотрудники не успевают адаптироваться, растёт недовольство граждан.",
            "en": "A region rolls out new rules for delivering public services. "
                  "Requirements from the top change every few weeks, "
                  "employees can't keep up and citizen dissatisfaction is growing.",
        },
        "expert_domain": "complicated",
        "expert_rationale": {
            "ru": "Правила заданы нормативно — это известная экспертная область. "
                  "Нужен план адаптации с обучением, стандартами работы и каналом "
                  "быстрой обратной связи в центр.",
            "en": "The rules are defined by law — this is a known expert field. "
                  "You need an adaptation plan with training, working standards and "
                  "a fast feedback channel back to the centre.",
        },
        "consequences": {
            "obvious": {
                "ru": "Сотрудники попробуют работать «как всегда», не учтут новых нюансов — "
                      "вырастут ошибки и жалобы.",
                "en": "Staff will keep working 'the old way', miss the new nuances — "
                      "errors and complaints will grow.",
            },
            "complicated": {
                "ru": "Правильно: план адаптации, обучение, методологи и юристы — "
                      "рост жалоб замедляется.",
                "en": "Right move: adaptation plan, training, methodologists and lawyers — "
                      "complaints start slowing down.",
            },
            "complex": {
                "ru": "Бесконечные «эксперименты» на гражданах без чётких стандартов "
                      "будут расценены как саботаж регламента.",
                "en": "Endless 'experiments' with citizens without clear standards "
                      "will look like sabotage of the regulation.",
            },
            "chaotic": {
                "ru": "«Командный центр» и ручное управление истощат людей и не решат "
                      "системной причины — частой смены требований.",
                "en": "A 'command centre' and manual firefighting will burn people out "
                      "without fixing the real cause — frequent rule changes.",
            },
        },
    },
    {
        "key": "factory_line",
        "category": {"ru": "Производство", "en": "Manufacturing"},
        "title": {"ru": "Сбои на заводской линии", "en": "Breakdowns on the factory line"},
        "scenario": {
            "ru": "На заводе регулярно возникают сбои на линии. Причины неочевидны: "
                  "иногда это оборудование, иногда люди, иногда поставщики.",
            "en": "A factory line suffers repeated breakdowns. The causes are not obvious: "
                  "sometimes equipment, sometimes people, sometimes suppliers.",
        },
        "expert_domain": "complicated",
        "expert_rationale": {
            "ru": "Классическая задача для анализа первопричин с экспертами: собрать данные, "
                  "построить диаграмму Ишикавы, устранить корневые причины по порядку.",
            "en": "A classic root-cause analysis task: gather data, build an Ishikawa diagram "
                  "and fix the root causes one by one.",
        },
        "consequences": {
            "obvious": {
                "ru": "Инструкция «делать аккуратнее» не закроет системные сбои оборудования "
                      "и поставок.",
                "en": "A 'be more careful' instruction won't fix systemic equipment or supply "
                      "failures.",
            },
            "complicated": {
                "ru": "Правильно: инженеры и качество проведут анализ и закроют корневые "
                      "причины — сбои станут реже.",
                "en": "Right move: engineers and quality people diagnose root causes and "
                      "close them — breakdowns go down.",
            },
            "complex": {
                "ru": "Запускать эксперименты на действующей линии без диагностики — "
                      "рискованно и дорого.",
                "en": "Experimenting on a live line without diagnosis is risky and expensive.",
            },
            "chaotic": {
                "ru": "Авральная остановка линии нужна только в настоящем кризисе — здесь "
                      "мы потеряем выпуск без пользы.",
                "en": "An emergency stop only makes sense in a real crisis — here you lose "
                      "output for nothing.",
            },
        },
    },
    {
        "key": "university_platform",
        "category": {"ru": "Образование", "en": "Education"},
        "title": {"ru": "Новая онлайн-платформа в вузе",
                  "en": "New online platform at the university"},
        "scenario": {
            "ru": "Университет внедряет новую онлайн-платформу обучения. Преподаватели "
                  "используют её по-разному, студенты жалуются на непоследовательность.",
            "en": "A university rolls out a new online learning platform. Lecturers use it "
                  "in very different ways; students complain about inconsistency.",
        },
        "expert_domain": "complex",
        "expert_rationale": {
            "ru": "Поведение людей непредсказуемо — у каждого преподавателя свой стиль. "
                  "Нужны пилоты, обратная связь и постепенное «приживление» практик.",
            "en": "Human behaviour is unpredictable — every lecturer has their own style. "
                  "You need pilots, feedback loops and gradual adoption of practices.",
        },
        "consequences": {
            "obvious": {
                "ru": "Жёсткий регламент вызовет саботаж и тихий возврат к «как раньше».",
                "en": "A rigid regulation will trigger sabotage and a quiet return to the old way.",
            },
            "complicated": {
                "ru": "Идеальный план внедрения «от экспертов» не переживёт столкновения с "
                      "реальными привычками преподавателей.",
                "en": "A perfect top-down rollout plan won't survive contact with real "
                      "teaching habits.",
            },
            "complex": {
                "ru": "Правильно: пилотная группа, сбор обратной связи, шаринг удачных "
                      "практик — платформа постепенно становится общей нормой.",
                "en": "Right move: pilot group, feedback collection, sharing what works — "
                      "the platform gradually becomes the norm.",
            },
            "chaotic": {
                "ru": "Отмена и замена «пожарным порядком» только усилит хаос и недоверие.",
                "en": "Cancelling and replacing it in firefighting mode will deepen chaos "
                      "and distrust.",
            },
        },
    },
    {
        "key": "new_product_launch",
        "category": {"ru": "Продукт", "en": "Product"},
        "title": {"ru": "Запуск нового продукта", "en": "Launching a new product"},
        "scenario": {
            "ru": "Компания запускает новый продукт на рынок, но не до конца понимает "
                  "потребности клиентов. Продажи нестабильны.",
            "en": "A company launches a new product but doesn't fully understand customer "
                  "needs. Sales are unstable.",
        },
        "expert_domain": "complex",
        "expert_rationale": {
            "ru": "Поведение рынка предсказать нельзя — тестируйте гипотезы, смотрите на "
                  "реакцию и быстро двигайтесь.",
            "en": "Market behaviour can't be predicted — test hypotheses, watch the response "
                  "and move fast.",
        },
        "consequences": {
            "obvious": {
                "ru": "Скопировать чужой playbook без проверки гипотез — потеряете бюджет "
                      "и время.",
                "en": "Copying someone else's playbook without testing hypotheses burns "
                      "budget and time.",
            },
            "complicated": {
                "ru": "Долгий анализ и идеальный стратегический план устареют раньше, "
                      "чем вы его запустите.",
                "en": "A long analysis and a perfect strategic plan will go stale before "
                      "you ship it.",
            },
            "complex": {
                "ru": "Правильно: 2–3 гипотезы, быстрые пилоты, честная метрика — "
                      "оставляете то, что работает.",
                "en": "Right move: 2–3 hypotheses, fast pilots, honest metrics — keep "
                      "what actually works.",
            },
            "chaotic": {
                "ru": "«Всё горит, скидки на всё» без гипотез приведёт к операционному "
                      "хаосу и демпингу.",
                "en": "'Everything is on fire, discounts everywhere' without hypotheses "
                      "leads to operational chaos and dumping.",
            },
        },
    },
    {
        "key": "reputation_crisis",
        "category": {"ru": "Кризис", "en": "Crisis"},
        "title": {"ru": "Репутационный кризис в соцсетях",
                  "en": "Reputation crisis on social media"},
        "scenario": {
            "ru": "Произошёл репутационный скандал в соцсетях. Информация распространяется "
                  "быстро, ситуация ухудшается каждый час.",
            "en": "A reputation scandal breaks out on social media. The story spreads fast "
                  "and the situation gets worse every hour.",
        },
        "expert_domain": "chaotic",
        "expert_rationale": {
            "ru": "Когда ситуация горит и ухудшается каждый час — сначала остановите "
                  "кровотечение: публичная реакция, единый голос, контроль каналов. "
                  "Анализ потом.",
            "en": "When the situation is burning and getting worse every hour — stop the "
                  "bleeding first: public statement, single voice, channel control. "
                  "Analysis comes later.",
        },
        "consequences": {
            "obvious": {
                "ru": "Следовать стандартному PR-регламенту — процесс займёт дни, а "
                      "нарратив «сгорит» за часы.",
                "en": "Following the standard PR playbook — the process takes days while "
                      "the narrative burns in hours.",
            },
            "complicated": {
                "ru": "Недели на анализ и идеальное заявление — репутация тем временем "
                      "упадёт ниже, чем можно восстановить.",
                "en": "Weeks of analysis and a perfect statement — by then reputation drops "
                      "below recoverable.",
            },
            "complex": {
                "ru": "«Поэкспериментируем с разными реакциями» — худший сигнал в кризисе, "
                      "усилит ощущение хаоса.",
                "en": "'Let's experiment with different reactions' is the worst signal in a "
                      "crisis — it amplifies the sense of chaos.",
            },
            "chaotic": {
                "ru": "Правильно: штаб, один голос, жёсткая приоритизация каналов — "
                      "стабилизируете ситуацию и только потом анализ.",
                "en": "Right move: war room, single voice, ruthless channel prioritisation "
                      "— stabilise first, analyse later.",
            },
        },
    },
    {
        "key": "team_demotivation",
        "category": {"ru": "HR / команда", "en": "HR / team"},
        "title": {"ru": "Демотивированная команда", "en": "Demotivated team"},
        "scenario": {
            "ru": "Команда демотивирована после серии неудачных проектов. Нет явной "
                  "причины, но производительность падает.",
            "en": "A team is demotivated after a series of unsuccessful projects. There is "
                  "no single obvious cause, but performance keeps dropping.",
        },
        "expert_domain": "complex",
        "expert_rationale": {
            "ru": "Мотивация — система из множества факторов. Здесь нужны разговор 1:1, "
                  "маленькие эксперименты с практиками, наблюдение за динамикой.",
            "en": "Motivation is a system of many factors. You need 1:1 conversations, "
                  "small experiments with practices, watching the dynamic.",
        },
        "consequences": {
            "obvious": {
                "ru": "«Тимбилдинг по чек-листу» воспринимается как формальность и "
                      "ухудшает атмосферу.",
                "en": "A checklist-style team-building feels performative and makes the "
                      "atmosphere worse.",
            },
            "complicated": {
                "ru": "Глубокое HR-исследование без быстрых действий — команда развалится, "
                      "пока готовится отчёт.",
                "en": "A deep HR study without fast actions — the team falls apart while "
                      "the report is being written.",
            },
            "complex": {
                "ru": "Правильно: 1:1, ретро, 2–3 маленьких изменения в неделю, честная "
                      "обратная связь — энергия возвращается.",
                "en": "Right move: 1:1s, retros, 2–3 small weekly changes, honest feedback "
                      "— energy comes back.",
            },
            "chaotic": {
                "ru": "Увольнять и разгонять команду «по-быстрому» — перетащит проблему "
                      "в новую команду.",
                "en": "Firing and breaking up the team fast just drags the same problem "
                      "into a new team.",
            },
        },
    },
    {
        "key": "changing_requirements",
        "category": {"ru": "IT / цифровой сервис", "en": "IT / digital service"},
        "title": {"ru": "Цифровой сервис с меняющимися требованиями",
                  "en": "Digital service with changing requirements"},
        "scenario": {
            "ru": "Компания разрабатывает новый цифровой сервис, но требования часто "
                  "меняются, пользователи сами не до конца понимают, что им нужно.",
            "en": "A company is building a new digital service, but requirements keep "
                  "changing and users themselves don't fully know what they need.",
        },
        "expert_domain": "complex",
        "expert_rationale": {
            "ru": "Потребность проявляется только через использование. Нужны MVP, короткие "
                  "итерации, быстрая обратная связь и готовность выбрасывать лишнее.",
            "en": "The real need only emerges through usage. You need an MVP, short "
                  "iterations, fast feedback and the courage to throw things away.",
        },
        "consequences": {
            "obvious": {
                "ru": "«Делаем как у конкурента» — продукт окажется не про вашу аудиторию.",
                "en": "'Let's copy the competitor' — the product won't fit your audience.",
            },
            "complicated": {
                "ru": "Детальное ТЗ на год вперёд устареет ещё до выхода первой версии.",
                "en": "A detailed year-long spec will be outdated before the first version "
                      "ships.",
            },
            "complex": {
                "ru": "Правильно: MVP, частые релизы, метрики реального использования — "
                      "требования стабилизируются сами.",
                "en": "Right move: MVP, frequent releases, usage metrics — requirements "
                      "start stabilising on their own.",
            },
            "chaotic": {
                "ru": "«Быстро-быстро, любой ценой» создаст технический долг, который "
                      "потом потопит команду.",
                "en": "'Fast at any cost' will create tech debt that drowns the team later.",
            },
        },
    },
    {
        "key": "process_workarounds",
        "category": {"ru": "Процедуры / регламент", "en": "Process / regulation"},
        "title": {"ru": "Сотрудники обходят регламент",
                  "en": "Employees bypass the procedure"},
        "scenario": {
            "ru": "В организации есть чётко описанный процесс согласования документов, "
                  "но сотрудники часто его обходят, чтобы ускорить работу.",
            "en": "The organisation has a clearly defined document approval process, but "
                  "employees often bypass it to speed their work up.",
        },
        "expert_domain": "obvious",
        "expert_rationale": {
            "ru": "Процесс описан и работает, когда по нему идут. Правильная реакция — "
                  "обеспечить соблюдение: напоминания, контроль, автоматизация согласования. "
                  "Спор с «complicated» здесь ожидаем — многие считают, что сначала нужно "
                  "анализировать, почему обходят.",
            "en": "The process is defined and works when people follow it. The right "
                  "response is to enforce it: reminders, controls, automated routing. "
                  "A debate with 'complicated' is expected — many will argue you must "
                  "first analyse why people bypass it.",
        },
        "consequences": {
            "obvious": {
                "ru": "Правильно: напоминания, прозрачные сроки, автоматизация "
                      "согласования — большинство вернётся в процесс.",
                "en": "Right move: reminders, transparent SLAs, automated routing — most "
                      "people come back into the process.",
            },
            "complicated": {
                "ru": "Большой редизайн регламента по результатам анализа — пока длится "
                      "исследование, все продолжают обходить.",
                "en": "A big redesign based on analysis — while the study runs, everyone "
                      "keeps bypassing the rules.",
            },
            "complex": {
                "ru": "«Поэкспериментируем с разными правилами» в формальном "
                      "документообороте приведёт к хаосу и юридическим рискам.",
                "en": "'Let's experiment with different rules' in formal document flow "
                      "ends in chaos and legal risk.",
            },
            "chaotic": {
                "ru": "Штрафы и разгон «виновных» решат симптом на день, но заложат страх "
                      "и ещё более изобретательные обходы.",
                "en": "Fines and witch-hunts fix the symptom for a day but plant fear and "
                      "even more creative workarounds.",
            },
        },
    },
]


def _loc(locale: str) -> str:
    return "en" if (locale or "").lower() == "en" else "ru"


def get_cases_for_locale(locale: str) -> List[Dict]:
    """Компактный список кейсов для экрана участника (без дебрифа)."""
    lc = _loc(locale)
    return [
        {
            "key": c["key"],
            "order": i + 1,
            "category": c["category"][lc],
            "title": c["title"][lc],
            "scenario": c["scenario"][lc],
        }
        for i, c in enumerate(CASES)
    ]


def get_case_debrief(case_key: str, locale: str) -> Optional[Dict]:
    """Возвращает экспертный домен, объяснение и последствия по каждому домену."""
    lc = _loc(locale)
    for c in CASES:
        if c["key"] == case_key:
            return {
                "key": c["key"],
                "expert_domain": c["expert_domain"],
                "expert_rationale": c["expert_rationale"][lc],
                "consequences": {
                    dk: c["consequences"][dk][lc] for dk in DOMAIN_KEYS
                },
            }
    return None


def get_strategies_for_locale(locale: str) -> Dict[str, List[Dict]]:
    lc = _loc(locale)
    return {
        dk: [{"key": s["key"], "label": s["label_" + lc]} for s in arr]
        for dk, arr in STRATEGIES.items()
    }


def get_strategy_label(domain: str, strategy_key: str, locale: str) -> Optional[str]:
    lc = _loc(locale)
    for s in STRATEGIES.get(domain, []):
        if s["key"] == strategy_key:
            return s["label_" + lc]
    return None


def valid_case_keys() -> Set[str]:
    return {c["key"] for c in CASES}


def valid_domain_keys() -> Set[str]:
    return set(DOMAIN_KEYS)


def valid_strategy_keys(domain: str) -> Set[str]:
    return {s["key"] for s in STRATEGIES.get(domain, [])}
