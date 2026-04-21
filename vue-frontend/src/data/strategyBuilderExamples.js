export function getStrategyExampleRu(scope = 'company') {
  const base = {
    industry: 'Финансовый сервис для розничных клиентов',
    vision: 'К 2028 году — первый выбор для ежедневных финансовых операций у 5+ млн активных пользователей в регионе.',
    mission: 'Мы помогаем людям быстрее принимать уверенные финансовые решения за счёт простых продуктов и честной аналитики.',
    purpose: 'Верим, что простые и прозрачные финансовые инструменты снимают тревогу и возвращают людям контроль над будущим.',
    values: ['Прозрачность', 'Скорость', 'Забота о клиенте', 'Смелые ставки', 'Дисциплина поставки'],
    strategy: {
      horizon: '2026–2028',
      pillars: [
        { name: 'Продукт «day-to-day»', description: 'Убираем трение в 10 самых частых клиентских сценариях за год.' },
        { name: 'Данные как фичи', description: 'Встроенная аналитика и advice-движок в каждом продукте.' },
        { name: 'Единая платформа', description: 'Консолидируем 3 legacy-системы, сокращаем TCO на 30%.' },
        { name: 'Сильная команда', description: 'Найм senior-профилей и осмысленная ротация на ключевых ролях.' },
      ],
      bets: [
        'Запустить новый онбординг под iOS/Android с сокращением шагов на 40%.',
        'Встроить AI-ассистента в приложение для двух самых частых сценариев.',
        'Выйти в 2 новых сегмента (самозанятые, молодая семья).',
        'Оптимизировать unit-экономику — снизить CAC на 15%.',
      ],
      metrics: [
        'MAU активных клиентов',
        'Retention 90/180 дней',
        'NPS',
        'Unit-маржа на клиента',
        'Доля операций через self-service',
      ],
    },
    okrs: [
      {
        objective: 'Ускорить путь клиента в ключевых сценариях',
        key_results: [
          'P90 времени онбординга < 3 мин к концу квартала',
          'Доля клиентов, завершивших онбординг, ≥ 80%',
          'Снижение количества обращений в поддержку по онбордингу на 30%',
        ],
      },
      {
        objective: 'Встроить advice-движок в 2 продукта',
        key_results: [
          '≥ 40% клиентов видят минимум 1 персональный совет в неделю',
          'CTR по рекомендациям ≥ 12%',
          'Рост cross-sell из рекомендаций на 1.5п.п.',
        ],
      },
    ],
  };

  if (scope === 'department') {
    return {
      ...base,
      industry: 'Департамент клиентского сервиса',
      vision: 'Департамент, где 80% клиентских вопросов решаются с первого касания без эскалаций.',
      mission: 'Мы обеспечиваем ощущение заботы и быстрых ответов для клиентов всех продуктов.',
      values: ['Первое касание', 'Эмпатия', 'Скорость', 'Знания шарим', 'Измеримый результат'],
    };
  }
  if (scope === 'team') {
    return {
      ...base,
      industry: 'Продуктовая команда «онбординг»',
      vision: 'Новые клиенты доходят до первого полезного действия за 2 минуты — без поддержки.',
      mission: 'Мы проектируем и поставляем онбординг-поток так, чтобы клиент получал ценность в первое же использование.',
      values: ['Пользователь в центре', 'Данные, не мнения', 'Маленькие шаги', 'Открытость', 'Дисциплина'],
      strategy: {
        ...base.strategy,
        horizon: 'следующие 6 месяцев',
        pillars: [
          { name: 'Сокращаем шаги онбординга', description: 'Убираем 30% шагов без потери conversion.' },
          { name: 'Data-driven retention', description: 'Каждый эксперимент проходит A/B-тест.' },
          { name: 'Кросс-функциональная командная работа', description: 'Дизайн, бэкенд, аналитика в одном ритме.' },
        ],
      },
    };
  }
  return base;
}

export function getStrategyExampleEn(scope = 'company') {
  const base = {
    industry: 'Retail financial services',
    vision: 'By 2028 — the default choice for everyday financial operations for 5M+ active customers in the region.',
    mission: 'We help people make confident financial decisions faster with simple products and honest analytics.',
    purpose: 'We believe clear, simple financial tools remove anxiety and give people back a sense of control over their future.',
    values: ['Transparency', 'Speed', 'Customer obsession', 'Bold bets', 'Delivery discipline'],
    strategy: {
      horizon: '2026–2028',
      pillars: [
        { name: 'Day-to-day product', description: 'Remove friction in the 10 most frequent customer journeys this year.' },
        { name: 'Data as features', description: 'Embedded analytics and an advice engine inside every product.' },
        { name: 'One platform', description: 'Consolidate 3 legacy systems, lower TCO by 30%.' },
        { name: 'Strong team', description: 'Hire senior profiles and rotate key roles intentionally.' },
      ],
      bets: [
        'Launch a new iOS / Android onboarding with 40% fewer steps.',
        'Embed an AI assistant in the app for the two most common scenarios.',
        'Enter 2 new segments (self-employed, young family).',
        'Improve unit economics — reduce CAC by 15%.',
      ],
      metrics: [
        'Active monthly customers (MAU)',
        '90 / 180-day retention',
        'NPS',
        'Per-customer unit margin',
        'Share of self-service transactions',
      ],
    },
    okrs: [
      {
        objective: 'Speed up the customer path in key flows',
        key_results: [
          'P90 onboarding time < 3 min by end of quarter',
          '≥ 80% of customers finish onboarding',
          '30% fewer onboarding-related support tickets',
        ],
      },
      {
        objective: 'Embed advice engine in 2 products',
        key_results: [
          '≥ 40% of customers see at least 1 personalized tip weekly',
          'Recommendation CTR ≥ 12%',
          'Cross-sell from recommendations +1.5 pp',
        ],
      },
    ],
  };

  if (scope === 'department') {
    return {
      ...base,
      industry: 'Customer service department',
      vision: 'A department where 80% of customer issues are resolved first-touch with no escalation.',
      mission: 'We deliver a feeling of care and fast answers to customers across all our products.',
      values: ['First touch', 'Empathy', 'Speed', 'Share knowledge', 'Measurable outcome'],
    };
  }
  if (scope === 'team') {
    return {
      ...base,
      industry: 'Onboarding product team',
      vision: 'New customers reach their first useful action in under 2 minutes — without support.',
      mission: 'We design and ship an onboarding flow so that the customer gets value on the very first use.',
      values: ['User-first', 'Data, not opinions', 'Small steps', 'Openness', 'Discipline'],
      strategy: {
        ...base.strategy,
        horizon: 'next 6 months',
        pillars: [
          { name: 'Fewer onboarding steps', description: 'Remove 30% of steps without losing conversion.' },
          { name: 'Data-driven retention', description: 'Every experiment runs an A/B test.' },
          { name: 'Cross-functional teamwork', description: 'Design, backend, analytics on one rhythm.' },
        ],
      },
    };
  }
  return base;
}
