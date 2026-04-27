/**
 * Контентный пакет тренинга «Матрица стейкхолдеров».
 * Здесь живут персоны, кейсы, события, стартовые формулировки стратегий
 * и шаблоны реакций. Все строки — RU / EN.
 *
 * Намеренно НЕ кладём это в i18n.json, потому что это длинные сценарные тексты,
 * а не интерфейсные подписи: их удобнее редактировать единым документом.
 */

export const PERSONAS = {
  ru: {
    cto: {
      emoji: '👨‍💻', name: 'Артём Лебедев', role: 'CTO',
      motivation: 'Архитектура должна выдержать рост в 5 раз и не утянуть нас в техдолг.',
      quote: '«Если интеграции не выдержат, никакой маркетинг не спасёт релиз».',
    },
    cfo: {
      emoji: '💼', name: 'Марина Соловьёва', role: 'CFO',
      motivation: 'Любая инициатива должна окупаться за 18 месяцев и не ломать бюджет.',
      quote: '«Покажите unit-economics — иначе я не подпишу фондирование».',
    },
    hr: {
      emoji: '🤝', name: 'Анна Зимина', role: 'HR Director',
      motivation: 'Команда не должна выгореть, а ключевые люди — не уйти на конкурента.',
      quote: '«Я переживаю не за проект, а за людей, которые его тянут».',
    },
    po: {
      emoji: '🎯', name: 'Дмитрий Карпов', role: 'Product Owner',
      motivation: 'Я отвечаю за бэклог и понимаю, что у нас одна попытка попасть в рынок.',
      quote: '«Дайте мне фокус, я уберу всё лишнее из спринта».',
    },
    developer: {
      emoji: '🛠️', name: 'Илья Громов', role: 'Senior Developer',
      motivation: 'Хочу делать продукт, которым не стыдно, и не тушить пожары по ночам.',
      quote: '«Просто скажите, какие требования финальные, и не меняйте за неделю».',
    },
    marketing: {
      emoji: '📣', name: 'Юля Ковалёва', role: 'Marketing Lead',
      motivation: 'Кампания запуска уже куплена — нам нельзя сдвигать дату.',
      quote: '«Если перенесёте на месяц — мы потеряем половину медиа-бюджета».',
    },
    sponsor: {
      emoji: '🌟', name: 'Сергей Мальцев', role: 'Спонсор / член правления',
      motivation: 'Меня спросят на правлении, что мы получили за этот год вложений.',
      quote: '«Мне нужны 3 цифры, которые покажут, что мы не зря это начали».',
    },
    ciso: {
      emoji: '🛡️', name: 'Алексей Хоробрых', role: 'CISO',
      motivation: 'Инцидент с данными в первые месяцы — потеря лицензии.',
      quote: '«Без оценки рисков и DPIA мы это не выпустим — точка».',
    },
    pm: {
      emoji: '📋', name: 'Ольга Петрова', role: 'Руководитель проекта',
      motivation: 'Я держу сроки, риски и зависимости — без меня всё рассыпается.',
      quote: '«Кто-нибудь видел план? Я уже не понимаю, кто принимает решения».',
    },
    customer: {
      emoji: '🏢', name: 'Виктор Зайцев', role: 'Бизнес-заказчик',
      motivation: 'Я плачу за результат и хочу видеть его в цифрах продаж.',
      quote: '«Я заказал продукт, который продаёт, а не красивые отчёты».',
    },
    end_user: {
      emoji: '🙋', name: 'Лена Волкова', role: 'Пользователь',
      motivation: 'Я просто хочу решить свою задачу за минуту, а не разбираться в системе.',
      quote: '«Если я не пойму, как зарегистрироваться, я уйду к конкурентам».',
    },
    compliance: {
      emoji: '⚖️', name: 'Татьяна Шепель', role: 'Compliance Officer',
      motivation: '152-ФЗ, ЦБ и ПДн на мне — отвечаю головой.',
      quote: '«Маркетинг сначала покажите мне — потом запускайте».',
    },
  },
  en: {
    cto: {
      emoji: '👨‍💻', name: 'Artem Lebedev', role: 'CTO',
      motivation: 'The architecture must scale 5x and not bury us in tech debt.',
      quote: '"If integrations don\'t hold, no marketing will save the launch."',
    },
    cfo: {
      emoji: '💼', name: 'Marina Solovieva', role: 'CFO',
      motivation: 'Anything we ship must pay back in 18 months and not break the budget.',
      quote: '"Show me unit economics — otherwise I won\'t sign off funding."',
    },
    hr: {
      emoji: '🤝', name: 'Anna Zimina', role: 'HR Director',
      motivation: "I don't want the team to burn out or lose key people to competitors.",
      quote: '"I\'m worried about the people pulling this, not just the project."',
    },
    po: {
      emoji: '🎯', name: 'Dmitry Karpov', role: 'Product Owner',
      motivation: 'I own the backlog and we have one shot at the market.',
      quote: '"Give me focus and I\'ll cut every non-essential thing out of this sprint."',
    },
    developer: {
      emoji: '🛠️', name: 'Ilya Gromov', role: 'Senior Developer',
      motivation: 'I want to ship something I\'m proud of and not fight fires at 2 a.m.',
      quote: '"Just tell me what the requirements really are — and stop changing them weekly."',
    },
    marketing: {
      emoji: '📣', name: 'Julia Kovaleva', role: 'Marketing Lead',
      motivation: 'The launch campaign is already booked — we can\'t slip the date.',
      quote: '"Move it by a month and we lose half of the media budget."',
    },
    sponsor: {
      emoji: '🌟', name: 'Sergey Maltsev', role: 'Sponsor / Board',
      motivation: 'The board will ask me what this year of investment actually returned.',
      quote: '"I need three numbers that prove this wasn\'t a waste."',
    },
    ciso: {
      emoji: '🛡️', name: 'Alex Khorobrykh', role: 'CISO',
      motivation: 'A data incident in the first months kills the license.',
      quote: '"Without a risk assessment and DPIA — no, we don\'t ship."',
    },
    pm: {
      emoji: '📋', name: 'Olga Petrova', role: 'Project Manager',
      motivation: 'I hold the timeline, risks and dependencies together.',
      quote: '"Has anyone seen the plan? I no longer know who decides what."',
    },
    customer: {
      emoji: '🏢', name: 'Victor Zaitsev', role: 'Business sponsor',
      motivation: 'I paid for results and I want to see them in revenue.',
      quote: '"I ordered a product that sells, not beautiful reports."',
    },
    end_user: {
      emoji: '🙋', name: 'Lena Volkova', role: 'User',
      motivation: 'I just want to do my task in under a minute.',
      quote: '"If I can\'t figure out how to sign up, I\'m gone."',
    },
    compliance: {
      emoji: '⚖️', name: 'Tatiana Shepel', role: 'Compliance Officer',
      motivation: 'Privacy law, the regulator, and PII are my neck on the line.',
      quote: '"Marketing copy comes through me first, then to launch."',
    },
  },
};

export const CASES = {
  ru: [
    {
      key: 'digital_bank', emoji: '🏦',
      title: 'Цифровой банк для нового сегмента',
      lead: 'Крупный банк запускает онлайн-сервис для малого бизнеса. Релиз через 4 месяца, бюджет ограничен, у конкурентов уже есть похожее предложение.',
      goal: 'Привлечь 50 000 клиентов МСБ за полгода и удержать половину к концу года.',
      flavor: 'Интеграции с процессингом, KYC, PCI-DSS, мобильное приложение и поддержка 24/7.',
    },
    {
      key: 'retail_crm', emoji: '🧰',
      title: 'CRM для розничной сети',
      lead: 'Сеть из 800 магазинов меняет старую CRM на новую — единое окно для продавцов, программа лояльности и аналитика.',
      goal: 'Поднять средний чек на 8 % и сократить отток лояльной базы.',
      flavor: 'Интеграция с кассами, ERP, маркетинговой платформой; обучение 12 000 продавцов.',
    },
    {
      key: 'citizen_portal', emoji: '🏛️',
      title: 'Сервис госуслуг для самозанятых',
      lead: 'Государственная организация запускает портал для самозанятых: подача документов, налоги, статус и поддержка.',
      goal: 'Перевести 300 000 пользователей с офлайн-каналов в онлайн за год.',
      flavor: 'ЕСИА, защита персональных данных, очень разная цифровая грамотность пользователей.',
    },
  ],
  en: [
    {
      key: 'digital_bank', emoji: '🏦',
      title: 'A digital bank for a new segment',
      lead: 'A large bank launches an online service for SMBs. 4 months to release, limited budget, competitors already shipped something similar.',
      goal: 'Acquire 50,000 SMB customers in 6 months and retain half by year-end.',
      flavor: 'Processing integrations, KYC, PCI-DSS, mobile app and 24/7 support.',
    },
    {
      key: 'retail_crm', emoji: '🧰',
      title: 'CRM for a retail chain',
      lead: 'A chain of 800 stores swaps its old CRM for a new one: a single screen for sellers, loyalty and analytics.',
      goal: 'Lift average ticket by 8 % and reduce loyalty churn.',
      flavor: 'POS, ERP and marketing platform integrations; training 12,000 sellers.',
    },
    {
      key: 'citizen_portal', emoji: '🏛️',
      title: 'Government service for self-employed',
      lead: 'A state organization launches a portal for the self-employed: filings, taxes, status and support.',
      goal: 'Move 300,000 users from offline channels to online in a year.',
      flavor: 'National identity, strict PII, vastly different digital literacy among users.',
    },
  ],
};

export const EVENTS = {
  ru: [
    {
      key: 'delays', emoji: '⏱️',
      title: 'Сдвиг релиза',
      lead: 'Внешний поставщик задержал интеграцию на 6 недель. Команда теряет окно перед маркетинговой кампанией.',
      impacts: [
        { rid: 'pm', nudge: 'attention', note: 'PM становится центром коммуникации со стейкхолдерами.' },
        { rid: 'marketing', nudge: 'up', note: 'Маркетинг внезапно стал критичным: им сдвигать кампанию.' },
        { rid: 'sponsor', nudge: 'up', note: 'Спонсор хочет понимать, что это значит для года.' },
      ],
    },
    {
      key: 'resistance', emoji: '⚡',
      title: 'Сопротивление сотрудников',
      lead: 'Линейные сотрудники саботируют новый процесс: «и так всё работало». В чатах паника и слухи.',
      impacts: [
        { rid: 'hr', nudge: 'up', note: 'HR теперь нужен на регулярной основе, не «по запросу».' },
        { rid: 'end_user', nudge: 'up', note: 'Пользователей нельзя оставить без объяснений.' },
        { rid: 'pm', nudge: 'attention', note: 'PM координирует обучение, а не только сроки.' },
      ],
    },
    {
      key: 'budget_up', emoji: '💰',
      title: 'Бюджет вырос на 30 %',
      lead: 'Технические сюрпризы и инфра потянули смету. Финансы пересматривают план и могут заморозить часть фич.',
      impacts: [
        { rid: 'cfo', nudge: 'up', note: 'CFO теперь должен быть «в комнате» при каждом решении.' },
        { rid: 'sponsor', nudge: 'up', note: 'Спонсору нужно объяснять рост перед правлением.' },
        { rid: 'po', nudge: 'attention', note: 'PO режет скоуп и переоценивает приоритеты.' },
      ],
    },
    {
      key: 'tech_issues', emoji: '🔧',
      title: 'Сбои в проде',
      lead: 'Через неделю после релиза — два инцидента с данными и падение в час пик. Регулятор задаёт вопросы.',
      impacts: [
        { rid: 'cto', nudge: 'up', note: 'CTO лично разбирает инцидент и архитектуру.' },
        { rid: 'ciso', nudge: 'up', note: 'CISO просит срочную перепроверку контуров безопасности.' },
        { rid: 'compliance', nudge: 'up', note: 'Compliance готовит отчёт регулятору.' },
      ],
    },
  ],
  en: [
    {
      key: 'delays', emoji: '⏱️',
      title: 'Release slip',
      lead: 'A vendor missed an integration deadline by 6 weeks. The team loses the pre-campaign window.',
      impacts: [
        { rid: 'pm', nudge: 'attention', note: 'PM becomes the comms hub for stakeholders.' },
        { rid: 'marketing', nudge: 'up', note: 'Marketing is suddenly critical — they replan the campaign.' },
        { rid: 'sponsor', nudge: 'up', note: 'Sponsor wants to know what this means for the year.' },
      ],
    },
    {
      key: 'resistance', emoji: '⚡',
      title: 'Employee resistance',
      lead: 'Frontline staff resist the new process: "everything worked before". Chat groups buzz with rumours.',
      impacts: [
        { rid: 'hr', nudge: 'up', note: 'HR is now needed on a regular basis, not "on request".' },
        { rid: 'end_user', nudge: 'up', note: 'Users cannot be left without explanation.' },
        { rid: 'pm', nudge: 'attention', note: 'PM coordinates training and not only timelines.' },
      ],
    },
    {
      key: 'budget_up', emoji: '💰',
      title: 'Budget jumped 30 %',
      lead: 'Tech surprises pulled the bill up. Finance reviews the plan and may freeze a chunk of features.',
      impacts: [
        { rid: 'cfo', nudge: 'up', note: 'CFO must now be in the room for every decision.' },
        { rid: 'sponsor', nudge: 'up', note: 'Sponsor must defend the growth at the board.' },
        { rid: 'po', nudge: 'attention', note: 'PO cuts scope and rebalances priorities.' },
      ],
    },
    {
      key: 'tech_issues', emoji: '🔧',
      title: 'Production incidents',
      lead: 'A week post-launch — two data incidents and an outage at peak. The regulator is asking.',
      impacts: [
        { rid: 'cto', nudge: 'up', note: 'CTO personally owns the incident and architecture.' },
        { rid: 'ciso', nudge: 'up', note: 'CISO asks for an emergency security review.' },
        { rid: 'compliance', nudge: 'up', note: 'Compliance prepares the report to the regulator.' },
      ],
    },
  ],
};

export const STRATEGY_STARTERS = {
  ru: {
    hh: [
      'Раз в неделю — короткое 1:1 на 20 минут с обновлением и 2-мя главными вопросами.',
      'Парный демо-обзор: они смотрят живой прогресс, мы — слышим тревоги до того, как они станут проблемой.',
      'Сделать совместное соглашение о том, что считается «успехом» к концу квартала.',
    ],
    hl: [
      'Дайджест на 1 экран раз в 2 недели — только риски, цифры и решения, без воды.',
      'Триггер-нотификация только когда нужно их решение, а не «для информации».',
      'Заранее договориться, в каких 3 ситуациях вы дёргаете их лично.',
    ],
    lh: [
      'Сделать их частью пилота: пусть тестируют первыми и приносят кейсы.',
      'Открытый канал и быстрые ответы на их вопросы — у них энергия, её жалко терять.',
      'Дать им роль амбассадоров изменений в своих командах.',
    ],
    ll: [
      'Раз в месяц — короткий апдейт «что нового, нужны ли вы нам».',
      'Не звать на встречи, но делиться записью / one-pager при ключевых поворотах.',
      'Поставить триггер: при изменении квадранта роли — пересмотреть стратегию.',
    ],
  },
  en: {
    hh: [
      'A 20-minute 1:1 every week with an update and two key questions.',
      'A paired demo review: they see real progress, we hear concerns before they become problems.',
      'A joint definition of "success by end of quarter".',
    ],
    hl: [
      'A one-screen digest every two weeks — risks, numbers and decisions only.',
      'Trigger alerts only when their decision is needed, not "FYI".',
      'Pre-agree the three cases when you ping them personally.',
    ],
    lh: [
      'Make them part of the pilot: first to test, first to bring stories back.',
      'Open channel and fast replies — they bring energy, do not lose it.',
      'Offer them an "ambassador for change" role in their teams.',
    ],
    ll: [
      'A monthly short update: "anything new, do we need you".',
      'Skip the meetings, share a recording or one-pager at key turns.',
      'Set a trigger: if their quadrant changes, revisit the strategy.',
    ],
  },
};

const REACTIONS_TEMPLATES = {
  ru: {
    close: '«Отлично, что меня видят на этом уровне — но не забывайте: мне нужны решения, не просто статусы».',
    satisfied: '«Я не лезу каждый день, но дайте мне знать заранее, когда нужно моё решение — не за час до».',
    informed: '«Регулярного апдейта мне хватит, но не превращайте это в спам — лучше один экран раз в две недели».',
    minimal: '«Не тратьте моё время — я подключусь, если что-то реально пойдёт не так».',
  },
  en: {
    close: '"Glad you see me at this level — just remember, I need decisions, not just status updates."',
    satisfied: '"I won\'t poke around daily, but tell me in advance when you need my call — not an hour before."',
    informed: '"A regular update is enough, but don\'t spam me — one screen every two weeks works."',
    minimal: '"Don\'t waste my time — I\'ll show up only if something actually goes wrong."',
  },
};

const ROLE_REACTIONS = {
  ru: {
    cfo: {
      close: '«Раз вы вытащили меня в эту зону — приходите с цифрами, а не с эмоциями».',
      minimal: '«Серьёзно? Деньги идут — а меня не зовут? Готовьтесь к сюрпризу с бюджетом».',
    },
    cto: {
      close: '«Я готов держать темп, если архитектурные решения проходят через меня вовремя».',
      minimal: '«Окей. Я узнаю про продакшен из новостей — отличная стратегия».',
    },
    ciso: {
      close: '«Отлично — но дайте мне доступ к решениям, иначе security превратится в ритуал».',
      minimal: '«Если меня нет в обсуждении — следующий аудит будет очень долгим».',
    },
    sponsor: {
      close: '«Хорошо, что я в курсе — но не превращайте меня в дежурного по проекту».',
      minimal: '«Я узнаю про продукт из квартального отчёта? Тогда не удивляйтесь решениям правления».',
    },
    end_user: {
      close: '«Класс, что вы со мной разговариваете — но не задавайте 50 вопросов в опросе, я устаю».',
      minimal: '«Сделали без меня. Я разберусь — или не разберусь, и пойду к другим».',
    },
    customer: {
      close: '«Хорошо, что внимание ко мне есть. Только не путайте интерес с микроменеджментом».',
      minimal: '«Тогда не удивляйтесь, что приёмка пройдёт со скрипом».',
    },
    compliance: {
      close: '«Принимаю — но включайте меня в подготовку, а не в финальную проверку».',
      minimal: '«Запустите без меня — потом будем долго писать пояснения регулятору».',
    },
    marketing: {
      close: '«Отлично — мы синхронизируемся по сообщениям и срокам».',
      minimal: '«Кампания живёт своей жизнью? Хорошо, пусть так и звучит на правлении».',
    },
    hr: {
      close: '«Спасибо. Я заранее увижу, кого мы перегружаем».',
      minimal: '«Без меня — значит, выгорание заметим только постфактум».',
    },
    po: {
      close: '«Тогда я смогу нормально вести продукт и не отвлекаться на политику».',
      minimal: '«Если PO в зоне минимальных усилий — у вас не продукт, а портфель проектов».',
    },
    pm: {
      close: '«Хорошо. Тогда я держу зависимости и риски в одном месте».',
      minimal: '«Окей, без PM — но потом не спрашивайте, кто координирует все эти команды».',
    },
    developer: {
      close: '«Главное — не превращайте моё участие в десятые митинги в неделю».',
      minimal: '«Без меня в обсуждениях — потом не спрашивайте, почему всё дольше».',
    },
  },
  en: {
    cfo: {
      close: '"Now that you pulled me here — come with numbers, not emotions."',
      minimal: '"Really? Money flows but I\'m not in the room? Expect a budget surprise."',
    },
    cto: {
      close: '"I can hold the pace if architecture decisions go through me on time."',
      minimal: '"Cool. I learn about production from the news. Great plan."',
    },
    ciso: {
      close: '"Fine — give me access to decisions, otherwise security turns into a ritual."',
      minimal: '"Skip me, and the next audit will be a very long week."',
    },
    sponsor: {
      close: '"Good to be in the loop — just don\'t turn me into a duty officer for the project."',
      minimal: '"I learn about it from the quarterly report? Don\'t be surprised by the board\'s decisions."',
    },
    end_user: {
      close: '"Nice that you talk to me — just don\'t send me a 50-question survey."',
      minimal: '"Built without me. I\'ll figure it out — or won\'t, and go elsewhere."',
    },
    customer: {
      close: '"Glad I get attention. Just don\'t confuse interest with micromanagement."',
      minimal: '"Then don\'t be surprised when acceptance is rough."',
    },
    compliance: {
      close: '"Acknowledged — but include me in prep, not just final check."',
      minimal: '"Launch without me — then expect long letters to the regulator."',
    },
    marketing: {
      close: '"Great — we sync on messaging and timing."',
      minimal: '"So the campaign lives its own life? Fine, that\'s the version the board hears."',
    },
    hr: {
      close: '"Thanks. I will see who we overload — in advance."',
      minimal: '"Without me — burnout is noticed after the fact."',
    },
    po: {
      close: '"Then I can lead the product and not the politics."',
      minimal: '"If PO is in \\"minimal effort\\" — you don\'t have a product, you have a project portfolio."',
    },
    pm: {
      close: '"Good. Then I keep dependencies and risks in one place."',
      minimal: '"OK, no PM — but don\'t ask later who coordinates all these teams."',
    },
    developer: {
      close: '"Just don\'t turn my involvement into ten meetings a week."',
      minimal: '"Skip me in discussions — then don\'t ask why it takes longer."',
    },
  },
};

/**
 * Возвращает массив { rid, persona, bucket, quote } для всех расставленных ролей.
 */
export function buildReactions(placements, locale, personas) {
  const lc = locale === 'en' ? 'en' : 'ru';
  const out = [];
  Object.keys(placements || {}).forEach((rid) => {
    const p = placements[rid];
    if (!p) return;
    const infl = parseInt(p.infl, 10);
    const inter = parseInt(p.int, 10);
    if (Number.isNaN(infl) || Number.isNaN(inter)) return;
    const bucket = bucketFor(infl, inter);
    const persona = (personas[lc] && personas[lc][rid]) || null;
    if (!persona) return;
    const role = (ROLE_REACTIONS[lc] || {})[rid] || {};
    const quote = role[bucket] || REACTIONS_TEMPLATES[lc][bucket] || '';
    out.push({ rid, persona, bucket, quote });
  });
  return out;
}

function bucketFor(infl, inter) {
  if (infl === 0 && inter === 0) return 'minimal';
  if (infl === 0 && (inter === 1 || inter === 2)) return 'informed';
  if (infl === 2 && inter === 2) return 'close';
  return 'satisfied';
}

/** Подсчёт ролей по бакетам — для индикатора покрытия. */
export function bucketCounts(placements) {
  const counts = { minimal: 0, informed: 0, satisfied: 0, close: 0, _unplaced: 0 };
  Object.keys(placements || {}).forEach((rid) => {
    const p = placements[rid];
    if (!p) { counts._unplaced += 1; return; }
    const infl = parseInt(p.infl, 10);
    const inter = parseInt(p.int, 10);
    if (Number.isNaN(infl) || Number.isNaN(inter)) { counts._unplaced += 1; return; }
    counts[bucketFor(infl, inter)] += 1;
  });
  return counts;
}

/** Простая «оценка покрытия»: больше «satisfied / close» — выше, минимальные — снижают. */
export function coverageScore(placements) {
  const c = bucketCounts(placements);
  const total = c.minimal + c.informed + c.satisfied + c.close;
  if (!total) return 0;
  const positive = c.close * 2 + c.satisfied * 1.5 + c.informed * 0.6 + c.minimal * 0.2;
  return Math.round((positive / (total * 2)) * 100);
}

/** Сравнивает раунд 1 и раунд 2 — кто двинулся куда. */
export function diffRounds(r1, r2, personas, locale) {
  const lc = locale === 'en' ? 'en' : 'ru';
  const out = [];
  const ids = new Set([...Object.keys(r1 || {}), ...Object.keys(r2 || {})]);
  ids.forEach((rid) => {
    const a = r1 && r1[rid];
    const b = r2 && r2[rid];
    if (!a && !b) return;
    const persona = (personas[lc] && personas[lc][rid]) || { name: rid, emoji: '👤', role: rid };
    if (!a && b) {
      out.push({ rid, persona, kind: 'placed', from: null, to: b });
      return;
    }
    if (a && !b) {
      out.push({ rid, persona, kind: 'removed', from: a, to: null });
      return;
    }
    if (a.infl !== b.infl || a.int !== b.int) {
      const dInfl = b.infl - a.infl;
      const dInt = b.int - a.int;
      const kind = (dInfl > 0 || dInt > 0) ? 'up' : (dInfl < 0 || dInt < 0) ? 'down' : 'side';
      out.push({ rid, persona, kind, from: a, to: b });
    }
  });
  return out;
}
