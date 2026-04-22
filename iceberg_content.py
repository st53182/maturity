"""Контент для упражнения «Айсберг» (системное мышление).

Модель имеет 4 уровня:
    events          — что произошло (видимая часть)
    patterns        — что повторяется
    structures      — как устроена система (процессы, стимулы, правила)
    mental_models   — убеждения, установки, «так принято»

Для каждого кейса подготовлен набор карточек с фразами, которые
участник должен разложить по уровням, а также:

* superficial_explanations — типовые поверхностные объяснения, среди
  которых участник должен отметить, какие являются симптомами, а не
  причинами;
* expert_interventions    — пример интервенций на каждом уровне
  (что изменить, какой эффект, через сколько времени);
* expert_summary          — общий экспертный разбор;
* consequences            — последствия «решения только на уровне
  событий» vs «работы с системой».

Все строки локализованы на русский и английский.
"""

from __future__ import annotations

from typing import Dict, List, Optional


LEVEL_KEYS: List[str] = ["events", "patterns", "structures", "mental_models"]

LEVEL_ORDER = {lk: i for i, lk in enumerate(LEVEL_KEYS)}

# Базовые веса уровней — используются в скоре «глубины мышления».
LEVEL_WEIGHTS: Dict[str, int] = {
    "events": 1,
    "patterns": 2,
    "structures": 3,
    "mental_models": 4,
}


LEVEL_META = {
    "events": {
        "name":   {"ru": "События",              "en": "Events"},
        "hint":   {"ru": "Что видимое произошло? Конкретный факт.",
                   "en": "What visibly happened? A concrete fact."},
        "icon":   "🌊",
    },
    "patterns": {
        "name":   {"ru": "Паттерны",             "en": "Patterns"},
        "hint":   {"ru": "Что повторяется снова и снова?",
                   "en": "What keeps repeating over and over?"},
        "icon":   "🔁",
    },
    "structures": {
        "name":   {"ru": "Системные структуры",  "en": "Structures"},
        "hint":   {"ru": "Как устроена система: процессы, правила, стимулы.",
                   "en": "How the system is built: processes, rules, incentives."},
        "icon":   "🏗️",
    },
    "mental_models": {
        "name":   {"ru": "Ментальные модели",    "en": "Mental models"},
        "hint":   {"ru": "Убеждения, установки, «так принято».",
                   "en": "Beliefs, assumptions, the unspoken 'we always do it this way'."},
        "icon":   "🧠",
    },
}


CASES: List[Dict] = [
    # ---------- 1. Бизнес ----------
    {
        "key": "sales_decline",
        "category": {"ru": "Бизнес", "en": "Business"},
        "title": {"ru": "Продажи падают, несмотря на рекламу",
                  "en": "Sales are falling despite heavy advertising"},
        "scenario": {
            "ru": "Компания запустила большую рекламную кампанию, но продажи падают третий квартал подряд. "
                  "Менеджеры винят сезон, рынок и конкурентов, но цифры продолжают ухудшаться.",
            "en": "The company ran a large advertising campaign, but sales have been falling three quarters in a row. "
                  "Managers blame the season, the market and competitors — yet numbers keep getting worse.",
        },
        "items": [
            # events
            {"key": "s_e1", "level": "events",
             "text": {"ru": "Продажи упали на 18% за квартал",
                      "en": "Sales dropped 18% this quarter"}},
            {"key": "s_e2", "level": "events",
             "text": {"ru": "Крупный клиент ушёл к конкуренту",
                      "en": "A major client switched to a competitor"}},
            # patterns
            {"key": "s_p1", "level": "patterns",
             "text": {"ru": "Клиенты возвращаются всё реже",
                      "en": "Customers come back less and less often"}},
            {"key": "s_p2", "level": "patterns",
             "text": {"ru": "Каждая кампания даёт всё меньше отдачи",
                      "en": "Every campaign brings less return than the previous one"}},
            # structures
            {"key": "s_st1", "level": "structures",
             "text": {"ru": "Продажники премируются только за закрытые сделки, не за удержание",
                      "en": "Sales are paid only for closed deals, never for retention"}},
            {"key": "s_st2", "level": "structures",
             "text": {"ru": "Продукт и маркетинг работают в разных KPI",
                      "en": "Product and marketing run on different KPIs"}},
            # mental models
            {"key": "s_m1", "level": "mental_models",
             "text": {"ru": "«Главное — налить трафик, продажи сами случатся»",
                      "en": "'Just pour traffic in — sales will happen by themselves'"}},
            {"key": "s_m2", "level": "mental_models",
             "text": {"ru": "«Если клиент ушёл — значит, он был не наш»",
                      "en": "'If a client leaves — they weren't ours anyway'"}},
        ],
        "superficial_explanations": [
            {"key": "s_sx1",
             "text": {"ru": "Сейчас не сезон, осенью вырастет",
                      "en": "It's just off-season, it'll recover in autumn"},
             "is_symptom": True,
             "explanation": {"ru": "Это объяснение на уровне события: оправдывает падение и не требует действий.",
                             "en": "An event-level explanation: it excuses the drop and doesn't require action."}},
            {"key": "s_sx2",
             "text": {"ru": "Конкуренты демпингуют",
                      "en": "Competitors are dumping prices"},
             "is_symptom": True,
             "explanation": {"ru": "Поверхностное: объясняет один эпизод, но не системное снижение за три квартала.",
                             "en": "Surface-level: it explains one episode but not the systemic decline across three quarters."}},
            {"key": "s_sx3",
             "text": {"ru": "Продавцы не мотивированы на удержание клиентов",
                      "en": "Salespeople aren't incentivised to retain clients"},
             "is_symptom": False,
             "explanation": {"ru": "Это уже структурная причина — стимулы в системе мотивации.",
                             "en": "This is a structural cause — incentives in the compensation system."}},
            {"key": "s_sx4",
             "text": {"ru": "Реклама стала дороже",
                      "en": "Advertising has become more expensive"},
             "is_symptom": True,
             "explanation": {"ru": "Симптом рынка, но не объясняет, почему отдача снижается именно у вас.",
                             "en": "A market symptom, but doesn't explain why ROI is falling specifically for you."}},
            {"key": "s_sx5",
             "text": {"ru": "Мы вложены в воронку привлечения, а не в ценность продукта",
                      "en": "We invest in the acquisition funnel, not in product value"},
             "is_symptom": False,
             "explanation": {"ru": "Глубинная причина: ментальная модель «главное трафик» ведёт к структурному перекосу бюджетов.",
                             "en": "A deep cause: the 'traffic first' mental model drives a structural budget skew."}},
        ],
        "expert_interventions": {
            "events": {
                "text": {"ru": "Провести разбор ухода ключевого клиента и быстро вернуть его пилотным предложением.",
                         "en": "Review why the key client left and win them back with a pilot offer."},
                "effect": {"ru": "Одна закрытая сделка, короткий позитивный сигнал рынку.",
                           "en": "One closed deal, a short positive signal to the market."},
                "horizon": "short",
            },
            "patterns": {
                "text": {"ru": "Запустить анализ удержания и измерять повторные покупки наравне с новыми.",
                         "en": "Start a retention analysis and track repeat purchases on par with new ones."},
                "effect": {"ru": "Видим, где «течёт ведро», и начинаем управлять этим числом.",
                           "en": "We see where the bucket leaks and start managing that number."},
                "horizon": "medium",
            },
            "structures": {
                "text": {"ru": "Переделать KPI и бонусы так, чтобы привлечение и удержание были одной командой.",
                         "en": "Redesign KPIs and bonuses so acquisition and retention form a single team."},
                "effect": {"ru": "Поведение команд меняется под новые стимулы, отдача от рекламы стабилизируется.",
                           "en": "Team behaviour shifts to the new incentives; ad ROI stabilises."},
                "horizon": "medium_long",
            },
            "mental_models": {
                "text": {"ru": "Обсудить на правлении и с командой убеждение «главное — трафик» и перейти к «ценность и удержание».",
                         "en": "Challenge the 'traffic is king' belief at the board level and shift to 'value and retention'."},
                "effect": {"ru": "Меняются критерии решений — выбор проектов и кампаний становится другим.",
                           "en": "Decision criteria change — project and campaign choices change too."},
                "horizon": "long",
            },
        },
        "expert_summary": {
            "ru": "Падение продаж при росте рекламных расходов почти всегда — системная история. На поверхности — «сезон» и «конкуренты», глубже — KPI, которые игнорируют удержание, и убеждение, что «трафик решает всё». Пока ментальная модель не сдвинется, любые новые кампании будут давать меньше и меньше.",
            "en": "Falling sales during rising ad spend is almost always systemic. On the surface — 'season' and 'competitors'; deeper — KPIs that ignore retention and a belief that 'traffic solves everything'. Until that mental model shifts, new campaigns will keep delivering less and less.",
        },
        "consequences_events_only": {
            "ru": "Каждый квартал будем героически «спасать продажи» скидками и новыми запусками, выгорая команду и не меняя кривую.",
            "en": "Every quarter will be a heroic 'save the numbers' sprint of discounts and launches that burns the team out without moving the curve.",
        },
        "consequences_system": {
            "ru": "Через 2–3 квартала удержание начинает расти, реклама снова работает, а команда перестаёт тушить пожары.",
            "en": "Over 2–3 quarters retention starts growing, advertising works again and the team stops firefighting.",
        },
    },
    # ---------- 2. Образование ----------
    {
        "key": "students_disengage",
        "category": {"ru": "Образование", "en": "Education"},
        "title": {"ru": "Студенты теряют интерес к обучению",
                  "en": "Students are losing interest in learning"},
        "scenario": {
            "ru": "На старших курсах посещаемость и вовлечённость падают. Студенты говорят, что «это всё можно загуглить», а преподаватели жалуются на «новое поколение».",
            "en": "In senior years attendance and engagement are falling. Students say 'you can just google all this' while lecturers complain about 'the new generation'.",
        },
        "items": [
            {"key": "ed_e1", "level": "events",
             "text": {"ru": "На семинаре по анализу данных пришло 6 человек из 40",
                      "en": "6 out of 40 students showed up to a data seminar"}},
            {"key": "ed_e2", "level": "events",
             "text": {"ru": "Два курсовых проекта скачаны из интернета",
                      "en": "Two course projects were copied from the internet"}},
            {"key": "ed_p1", "level": "patterns",
             "text": {"ru": "К третьему курсу вовлечённость стабильно падает",
                      "en": "Engagement consistently drops by year 3"}},
            {"key": "ed_p2", "level": "patterns",
             "text": {"ru": "Успешно сдают те, кто «знает, как оформить», а не «как думать»",
                      "en": "Those who 'know how to format papers' pass — not those who 'know how to think'"}},
            {"key": "ed_st1", "level": "structures",
             "text": {"ru": "Оценка строится на экзамене «по конспекту», без применения знаний",
                      "en": "Grading is based on a memorisation-style exam without real application"}},
            {"key": "ed_st2", "level": "structures",
             "text": {"ru": "Программа не обновляется годами, связь с практикой — опционально",
                      "en": "Curriculum isn't updated for years; practical relevance is optional"}},
            {"key": "ed_m1", "level": "mental_models",
             "text": {"ru": "«Наша задача — выдать материал, а поймут ли — их проблема»",
                      "en": "'Our job is to deliver material; whether they get it is their problem'"}},
            {"key": "ed_m2", "level": "mental_models",
             "text": {"ru": "«Современные студенты просто ленивые»",
                      "en": "'Modern students are simply lazy'"}},
        ],
        "superficial_explanations": [
            {"key": "ed_sx1",
             "text": {"ru": "Молодёжь пошла не та",
                      "en": "This generation is just different"},
             "is_symptom": True,
             "explanation": {"ru": "Типовой удобный нарратив, снимает ответственность с институции.",
                             "en": "A convenient narrative that shifts responsibility away from the institution."}},
            {"key": "ed_sx2",
             "text": {"ru": "Интернет отвлекает, во всём виноват телефон",
                      "en": "The internet distracts, phones are to blame"},
             "is_symptom": True,
             "explanation": {"ru": "Симптом среды, но не объясняет, почему именно ваша программа теряет людей.",
                             "en": "An environmental symptom; doesn't explain why your specific programme loses people."}},
            {"key": "ed_sx3",
             "text": {"ru": "Формат лекций не стимулирует мышление, а оценивание — применение",
                      "en": "Lectures don't stimulate thinking and grading doesn't reward application"},
             "is_symptom": False,
             "explanation": {"ru": "Структурная причина: сама архитектура курса и оценки.",
                             "en": "A structural cause: the architecture of the course and grading itself."}},
            {"key": "ed_sx4",
             "text": {"ru": "Преподаватели плохо преподают",
                      "en": "Lecturers teach poorly"},
             "is_symptom": True,
             "explanation": {"ru": "Персональная претензия не объясняет системного падения интереса.",
                             "en": "A personal complaint doesn't explain a systemic engagement drop."}},
            {"key": "ed_sx5",
             "text": {"ru": "Мы убеждены, что студент сам должен «догонять», а не мы — перестраиваться",
                      "en": "We believe the student must 'catch up', not that we should redesign"},
             "is_symptom": False,
             "explanation": {"ru": "Ментальная модель, которая закрывает вход в изменения программы.",
                             "en": "A mental model that blocks any change to the programme."}},
        ],
        "expert_interventions": {
            "events": {
                "text": {"ru": "Разобрать конкретный семинар: что не сработало, как переупаковать тему.",
                         "en": "Debrief one specific seminar: what didn't work and how to repackage the topic."},
                "effect": {"ru": "Один курс становится живее, сигнал преподавателям.",
                           "en": "One course becomes livelier and signals other lecturers."},
                "horizon": "short",
            },
            "patterns": {
                "text": {"ru": "Измерять не посещаемость, а вовлечённость: задавать вопросы, собирать обратную связь после модуля.",
                         "en": "Stop measuring attendance; measure engagement: ask questions, collect post-module feedback."},
                "effect": {"ru": "Становится видно, на каких модулях группа «отваливается».",
                           "en": "It becomes visible where the cohort disengages."},
                "horizon": "medium",
            },
            "structures": {
                "text": {"ru": "Переделать оценивание на проектное и применение знаний; обновить практическую часть.",
                         "en": "Redesign grading around projects and application; refresh the practical side."},
                "effect": {"ru": "Стимул учиться по-настоящему, а не «сдавать» — возвращается смысл.",
                           "en": "Incentive shifts to real learning instead of 'passing' — meaning comes back."},
                "horizon": "medium_long",
            },
            "mental_models": {
                "text": {"ru": "Проговорить на кафедре убеждение «наше дело — выдать материал» и сдвинуть к «наше дело — сформировать мышление».",
                         "en": "At the department level, challenge the 'our job is to deliver material' belief and shift to 'our job is to grow thinking'."},
                "effect": {"ru": "Меняется, как преподаватели готовят занятия и оценивают студентов.",
                           "en": "Changes how lecturers prepare sessions and assess students."},
                "horizon": "long",
            },
        },
        "expert_summary": {
            "ru": "За «ленивыми студентами» почти всегда стоит формат, где думать невыгодно. Пока оцениваем «знание конспекта», а не применение — рациональная стратегия студента — выучить конспект и забыть.",
            "en": "Behind 'lazy students' there is usually a format where thinking is not rewarded. As long as we grade 'knowing the notes' instead of applying knowledge, the student's rational strategy is to memorise and forget.",
        },
        "consequences_events_only": {
            "ru": "Будем каждый год «бороться с невовлечённостью» — новыми санкциями за прогулы — и удивляться, что не работает.",
            "en": "We'll 'fight disengagement' every year with new attendance penalties and wonder why it doesn't work.",
        },
        "consequences_system": {
            "ru": "Через 2–3 семестра активность возвращается, выпускники сильнее, а репутация программы растёт.",
            "en": "Within 2–3 semesters activity returns, graduates are stronger and the programme's reputation grows.",
        },
    },
    # ---------- 3. Гос. услуги ----------
    {
        "key": "gov_slow_services",
        "category": {"ru": "Гос. управление", "en": "Public sector"},
        "title": {"ru": "Граждане жалуются на медленные услуги",
                  "en": "Citizens complain about slow public services"},
        "scenario": {
            "ru": "Жители района всё чаще жалуются на медленное оказание госуслуг. Руководство уже дважды увеличивало штат и меняло регламенты, но очереди и недовольство возвращаются.",
            "en": "Residents complain more and more about slow public services. Management has already expanded headcount twice and changed the rules, but queues and frustration keep coming back.",
        },
        "items": [
            {"key": "g_e1", "level": "events",
             "text": {"ru": "В субботу гражданин ждал 3,5 часа",
                      "en": "On Saturday a citizen waited 3.5 hours"}},
            {"key": "g_e2", "level": "events",
             "text": {"ru": "Жалоба на «Госуслугах» получила 120 лайков",
                      "en": "A complaint on the portal got 120 upvotes"}},
            {"key": "g_p1", "level": "patterns",
             "text": {"ru": "Пики нагрузки каждый раз одинаковые, но планирование не меняется",
                      "en": "Load peaks are the same every time, but planning doesn't adjust"}},
            {"key": "g_p2", "level": "patterns",
             "text": {"ru": "Сотрудники регулярно обходят регламент ради скорости",
                      "en": "Staff regularly bypass the procedure to save time"}},
            {"key": "g_st1", "level": "structures",
             "text": {"ru": "KPI ведомства — «количество услуг», а не «время до результата»",
                      "en": "The agency's KPI is 'number of services', not 'time to result'"}},
            {"key": "g_st2", "level": "structures",
             "text": {"ru": "Документооборот жёстко бумажный, переход в цифру — опциональный",
                      "en": "Document flow is strictly paper-based; going digital is optional"}},
            {"key": "g_m1", "level": "mental_models",
             "text": {"ru": "«Гражданин должен подстроиться под процесс»",
                      "en": "'Citizens must adjust to the process'"}},
            {"key": "g_m2", "level": "mental_models",
             "text": {"ru": "«Чем больше контроль, тем меньше ошибок»",
                      "en": "'The more controls, the fewer errors'"}},
        ],
        "superficial_explanations": [
            {"key": "g_sx1",
             "text": {"ru": "Нам не хватает людей",
                      "en": "We don't have enough staff"},
             "is_symptom": True,
             "explanation": {"ru": "Типовой ответ-симптом: нанять ещё людей — не решает перегруза в пиках.",
                             "en": "Classic symptom: hiring more doesn't fix peak overload."}},
            {"key": "g_sx2",
             "text": {"ru": "Граждане приходят не подготовленными",
                      "en": "Citizens show up unprepared"},
             "is_symptom": True,
             "explanation": {"ru": "Перенос ответственности на пользователя — не причина, а следствие плохого сервиса.",
                             "en": "Shifting responsibility onto users — a consequence of poor service, not a cause."}},
            {"key": "g_sx3",
             "text": {"ru": "KPI ведомства не связан со временем обслуживания",
                      "en": "The agency's KPI isn't tied to service time"},
             "is_symptom": False,
             "explanation": {"ru": "Структурная причина: стимулируем не то, что ценно для гражданина.",
                             "en": "A structural cause: we reward the wrong outcome for citizens."}},
            {"key": "g_sx4",
             "text": {"ru": "Система устарела, нужен новый софт",
                      "en": "The system is outdated, we need new software"},
             "is_symptom": True,
             "explanation": {"ru": "Софт без изменения процессов и ментальных моделей закрепит текущую боль.",
                             "en": "New software without changing processes and mindsets locks the pain in."}},
            {"key": "g_sx5",
             "text": {"ru": "Мы верим, что контроль важнее скорости",
                      "en": "We believe control matters more than speed"},
             "is_symptom": False,
             "explanation": {"ru": "Ментальная модель: именно она оправдывает многоступенчатые согласования.",
                             "en": "A mental model — it justifies every layer of approval."}},
        ],
        "expert_interventions": {
            "events": {
                "text": {"ru": "Организовать дежурных по пикам: суббота + конец месяца.",
                         "en": "Introduce peak-time duty staff: Saturdays and end of month."},
                "effect": {"ru": "Среднее время ожидания падает в пиках.",
                           "en": "Average wait time in peaks goes down."},
                "horizon": "short",
            },
            "patterns": {
                "text": {"ru": "Отследить 3 самых долгих типа услуг и переупаковать их маршрут.",
                         "en": "Track the 3 slowest service types and redesign their route."},
                "effect": {"ru": "Повторяющийся «затык» уходит.",
                           "en": "The recurring bottleneck goes away."},
                "horizon": "medium",
            },
            "structures": {
                "text": {"ru": "Ввести KPI «время до результата» и упростить цепочку согласований.",
                         "en": "Introduce a 'time to result' KPI and shorten the approval chain."},
                "effect": {"ru": "Ведомство начинает управлять временем, а не объёмом.",
                           "en": "The agency starts managing time, not volume."},
                "horizon": "medium_long",
            },
            "mental_models": {
                "text": {"ru": "Перезапустить разговор: «мы работаем для гражданина, а не гражданин — для процесса».",
                         "en": "Reframe the conversation: 'we work for the citizen, not the citizen for the process'."},
                "effect": {"ru": "Меняется, как разрабатываются новые регламенты.",
                           "en": "Changes how new regulations are designed going forward."},
                "horizon": "long",
            },
        },
        "expert_summary": {
            "ru": "Повторяющиеся очереди и жалобы при расширении штата — сигнал, что проблема системная. Без изменения KPI и убеждения «гражданин должен подстраиваться» любое увеличение ресурсов будет «съедено».",
            "en": "Persistent queues and complaints despite staffing up is a systemic signal. Without changing KPIs and the 'citizens must adjust' belief, any new capacity gets eaten up.",
        },
        "consequences_events_only": {
            "ru": "Нанимаем ещё людей и пишем ещё регламенты — нагрузка растёт, жалобы возвращаются.",
            "en": "We hire more people and write more procedures — workload grows, complaints return.",
        },
        "consequences_system": {
            "ru": "Время на услугу падает, жалобы уменьшаются, сотрудники перестают обходить регламент.",
            "en": "Time per service drops, complaints decrease, staff stop bypassing the procedure.",
        },
    },
    # ---------- 4. Команда ----------
    {
        "key": "team_overtime",
        "category": {"ru": "HR / команда", "en": "HR / team"},
        "title": {"ru": "Команда перерабатывает, но результата нет",
                  "en": "The team overworks, but results don't improve"},
        "scenario": {
            "ru": "Команда регулярно задерживается и работает по выходным. Темп «максимум», но срокам это не помогает: дедлайны всё равно съезжают, а качество падает.",
            "en": "The team regularly stays late and works weekends. Pace is at the maximum, but deadlines still slip and quality drops.",
        },
        "items": [
            {"key": "t_e1", "level": "events",
             "text": {"ru": "В пятницу сдали фичу в 22:30",
                      "en": "Shipped a feature at 22:30 on Friday"}},
            {"key": "t_e2", "level": "events",
             "text": {"ru": "Разработчик ушёл на больничный после релиза",
                      "en": "An engineer went on sick leave after a release"}},
            {"key": "t_p1", "level": "patterns",
             "text": {"ru": "Каждый релиз — аврал в последние 3 дня",
                      "en": "Every release is a crunch in the last 3 days"}},
            {"key": "t_p2", "level": "patterns",
             "text": {"ru": "Задачи стабильно недооцениваются на 30–40%",
                      "en": "Tasks are consistently underestimated by 30–40%"}},
            {"key": "t_st1", "level": "structures",
             "text": {"ru": "Работа приходит в спринт в середине итерации",
                      "en": "New work lands mid-sprint"}},
            {"key": "t_st2", "level": "structures",
             "text": {"ru": "Нет ретроспектив, планирование — только «снизу вверх»",
                      "en": "No retrospectives; planning is only bottom-up"}},
            {"key": "t_m1", "level": "mental_models",
             "text": {"ru": "«Настоящая команда просто делает — и не жалуется»",
                      "en": "'A real team just delivers — no complaining'"}},
            {"key": "t_m2", "level": "mental_models",
             "text": {"ru": "«Планировать — значит тратить время зря»",
                      "en": "'Planning is a waste of time'"}},
        ],
        "superficial_explanations": [
            {"key": "t_sx1",
             "text": {"ru": "Команда просто слабая, нужны «звёзды»",
                      "en": "The team is just weak, we need 'rockstars'"},
             "is_symptom": True,
             "explanation": {"ru": "Обвинение людей в системной проблеме — почти всегда ложный след.",
                             "en": "Blaming people for a systemic problem is almost always a false lead."}},
            {"key": "t_sx2",
             "text": {"ru": "В этом квартале просто тяжёлые задачи",
                      "en": "This quarter's tasks just happen to be heavy"},
             "is_symptom": True,
             "explanation": {"ru": "Объясняет один квартал, а не закономерность переработок.",
                             "en": "Explains one quarter, not a recurring pattern of overtime."}},
            {"key": "t_sx3",
             "text": {"ru": "Работа приходит в спринт постоянно — никто её не защищает",
                      "en": "Work keeps landing mid-sprint — nobody protects the team"},
             "is_symptom": False,
             "explanation": {"ru": "Структурная причина — отсутствие границы спринта.",
                             "en": "A structural cause — no sprint boundary."}},
            {"key": "t_sx4",
             "text": {"ru": "У людей плохо с тайм-менеджментом",
                      "en": "People are bad at time management"},
             "is_symptom": True,
             "explanation": {"ru": "Перевод системной проблемы в личную — удобно, но бесполезно.",
                             "en": "Turning a systemic issue into a personal one — convenient but useless."}},
            {"key": "t_sx5",
             "text": {"ru": "Мы считаем, что «настоящая команда не жалуется»",
                      "en": "We believe 'a real team doesn't complain'"},
             "is_symptom": False,
             "explanation": {"ru": "Ментальная модель, которая маскирует сигналы о системном сбое.",
                             "en": "A mental model that masks signals of a systemic breakdown."}},
        ],
        "expert_interventions": {
            "events": {
                "text": {"ru": "Запретить работу в выходные 2 спринта подряд и смотреть на результат.",
                         "en": "Ban weekend work for 2 sprints in a row and watch what happens."},
                "effect": {"ru": "Пик перегрузки уходит, становится видна настоящая пропускная способность.",
                           "en": "The overload peak subsides and the true throughput becomes visible."},
                "horizon": "short",
            },
            "patterns": {
                "text": {"ru": "На каждом ретро анализировать, почему задачи недооценены, — и корректировать планирование.",
                         "en": "In every retro analyse why tasks were underestimated and adjust planning."},
                "effect": {"ru": "Ошибка оценки постепенно уменьшается.",
                           "en": "Estimation error gradually shrinks."},
                "horizon": "medium",
            },
            "structures": {
                "text": {"ru": "Зафиксировать границу спринта: новые задачи — только с заменой старых.",
                         "en": "Lock the sprint boundary: new work only by swapping out existing items."},
                "effect": {"ru": "Работа управляема, приоритизация — у ПО, а не у «кто первый написал».",
                           "en": "Work becomes manageable; priorities live with the PO, not with 'first one to ask'."},
                "horizon": "medium_long",
            },
            "mental_models": {
                "text": {"ru": "Открыто говорить, что «настоящая команда — это не та, которая не жалуется, а та, которая видит систему».",
                         "en": "Say out loud that 'a real team isn't one that doesn't complain — it's one that sees the system'."},
                "effect": {"ru": "Люди начинают поднимать сигналы раньше, а не после выгорания.",
                           "en": "People raise signals earlier, not after burnout."},
                "horizon": "long",
            },
        },
        "expert_summary": {
            "ru": "Переработки без прироста результата почти всегда показывают, что система «гонит», а не «учится». Пока ментальная модель «не жаловаться» защищает структурные дыры, любой новый найм и любой «крепкий менеджер» тоже сгорят.",
            "en": "Overtime without improved outcomes almost always means the system is 'pushing' instead of 'learning'. While the 'don't complain' mental model protects the structural holes, any new hire and any 'strong manager' will also burn out.",
        },
        "consequences_events_only": {
            "ru": "Каждый следующий релиз — тот же аврал, выгорание, текучка, и всё списывается на «просто тяжёлый квартал».",
            "en": "Every next release is the same crunch, burnout and churn — all explained away by 'just a tough quarter'.",
        },
        "consequences_system": {
            "ru": "Через 1–2 квартала релизы становятся предсказуемыми, переработки уходят, качество растёт.",
            "en": "Within 1–2 quarters releases become predictable, overtime fades and quality improves.",
        },
    },
]


HORIZON_LABELS = {
    "short":         {"ru": "1–2 недели",    "en": "1–2 weeks"},
    "medium":        {"ru": "1–2 месяца",    "en": "1–2 months"},
    "medium_long":   {"ru": "3–6 месяцев",   "en": "3–6 months"},
    "long":          {"ru": "6+ месяцев",    "en": "6+ months"},
}


def _loc(locale: str) -> str:
    return "en" if (locale or "").lower() == "en" else "ru"


def get_level_meta(locale: str) -> List[Dict]:
    lc = _loc(locale)
    return [
        {
            "key":  lk,
            "order": LEVEL_ORDER[lk],
            "name": LEVEL_META[lk]["name"][lc],
            "hint": LEVEL_META[lk]["hint"][lc],
            "icon": LEVEL_META[lk]["icon"],
            "weight": LEVEL_WEIGHTS[lk],
        }
        for lk in LEVEL_KEYS
    ]


def get_cases_for_locale(locale: str) -> List[Dict]:
    """Список кейсов с карточками без раскрытия правильных уровней.

    `items` возвращаем без `level` (чтобы участник сам решал),
    но с ключом `key` — по нему потом сверяем ответ с экспертным
    вариантом.
    """
    lc = _loc(locale)
    out: List[Dict] = []
    for i, c in enumerate(CASES):
        items = [{"key": it["key"], "text": it["text"][lc]} for it in c["items"]]
        superficial = [
            {"key": s["key"], "text": s["text"][lc]}
            for s in c["superficial_explanations"]
        ]
        out.append({
            "key": c["key"],
            "order": i + 1,
            "category": c["category"][lc],
            "title": c["title"][lc],
            "scenario": c["scenario"][lc],
            "items": items,
            "superficial": superficial,
        })
    return out


def get_case_debrief(case_key: str, locale: str) -> Optional[Dict]:
    lc = _loc(locale)
    for c in CASES:
        if c["key"] != case_key:
            continue
        items_expert = {it["key"]: it["level"] for it in c["items"]}
        superficial_expert = {
            s["key"]: {
                "is_symptom": s["is_symptom"],
                "explanation": s["explanation"][lc],
            }
            for s in c["superficial_explanations"]
        }
        interventions = {}
        for lk, iv in c["expert_interventions"].items():
            interventions[lk] = {
                "text":    iv["text"][lc],
                "effect":  iv["effect"][lc],
                "horizon": iv["horizon"],
                "horizon_label": HORIZON_LABELS[iv["horizon"]][lc],
            }
        return {
            "key": c["key"],
            "items_expert": items_expert,
            "superficial_expert": superficial_expert,
            "interventions_expert": interventions,
            "summary": c["expert_summary"][lc],
            "consequences_events_only": c["consequences_events_only"][lc],
            "consequences_system": c["consequences_system"][lc],
        }
    return None


def valid_case_keys() -> set:
    return {c["key"] for c in CASES}


def valid_level_keys() -> set:
    return set(LEVEL_KEYS)


def level_weight(level_key: str) -> int:
    return LEVEL_WEIGHTS.get(level_key, 0)


def compute_depth_score(placements: Dict[str, str],
                        expert_items: Dict[str, str],
                        superficial_answers: Dict[str, bool],
                        superficial_expert: Dict[str, Dict],
                        interventions: Dict[str, str]) -> Dict[str, int]:
    """Возвращает компоненты скора «глубина мышления».

    * items_correct  — верно размещённые карточки (1 балл каждая)
    * superficial_correct — верно классифицированные «поверхностные объяснения»
    * interventions_weight — сумма весов уровней, на которых участник предложил
      непустую интервенцию (events=1 … mental_models=4)
    * total — сумма трёх слагаемых
    """
    items_correct = sum(
        1 for k, lv in (placements or {}).items()
        if expert_items.get(k) == lv
    )
    superficial_correct = sum(
        1 for k, val in (superficial_answers or {}).items()
        if superficial_expert.get(k, {}).get("is_symptom") is bool(val)
    )
    interventions_weight = 0
    for lk, txt in (interventions or {}).items():
        if isinstance(txt, str) and txt.strip():
            interventions_weight += LEVEL_WEIGHTS.get(lk, 0)
    total = items_correct + superficial_correct + interventions_weight
    return {
        "items_correct": items_correct,
        "superficial_correct": superficial_correct,
        "interventions_weight": interventions_weight,
        "total": total,
    }
