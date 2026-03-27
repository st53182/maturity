export const METRICS_TREE = {
  id: "profit",
  name: "PROFIT",
  nameRu: "Прибыль",
  children: [
    {
      id: "revenue",
      name: "Revenue",
      nameRu: "Выручка",
      children: [
        {
          id: "users",
          name: "Users",
          nameRu: "Пользователи",
          children: [
            { id: "acquisition", name: "Acquisition", nameRu: "Привлечение", children: [
              { id: "traffic_volume", name: "Traffic Volume", nameRu: "Объем трафика", children: [] },
              { id: "conversion_to_signup", name: "Conversion to Signup", nameRu: "Конверсия в регистрацию", children: [] },
              { id: "cac", name: "CAC", nameRu: "Стоимость привлечения клиента", children: [] },
              { id: "marketing_efficiency", name: "Marketing Efficiency", nameRu: "Эффективность маркетинга", children: [] },
            ]},
            { id: "activation", name: "Activation", nameRu: "Активация", children: [
              { id: "activation_rate", name: "Activation Rate", nameRu: "Доля активированных пользователей", children: [] },
              { id: "ttfv", name: "Time to First Value", nameRu: "Время до первой ценности", children: [
                { id: "customer_lead_time", name: "Customer Lead Time", nameRu: "Время доставки ценности пользователю", children: [
                  { id: "lead_time", name: "Lead Time", nameRu: "Время от идеи до релиза", children: [
                    { id: "cycle_time", name: "Cycle Time", nameRu: "Время выполнения задачи", children: [
                      { id: "wip", name: "WIP", nameRu: "Незавершенная работа", children: [] },
                      { id: "blocked_time", name: "Blocked Time", nameRu: "Время блокировок", children: [] },
                      { id: "flow_efficiency", name: "Flow Efficiency", nameRu: "Эффективность потока", children: [] },
                    ]},
                    { id: "queue_time", name: "Queue Time", nameRu: "Время ожидания", children: [] },
                  ]},
                  { id: "deployment_frequency", name: "Deployment Frequency", nameRu: "Частота релизов", children: [
                    { id: "throughput", name: "Throughput", nameRu: "Пропускная способность команды", children: [] },
                    { id: "velocity", name: "Velocity", nameRu: "Скорость команды", children: [
                      { id: "team_maturity", name: "Team Maturity", nameRu: "Зрелость команды", children: [
                        { id: "engineering_maturity", name: "Engineering Maturity", nameRu: "Зрелость инженерии", children: [] },
                        { id: "process_maturity", name: "Process Maturity", nameRu: "Зрелость процессов", children: [] },
                        { id: "team_autonomy", name: "Team Autonomy", nameRu: "Автономность команды", children: [] },
                      ]},
                    ]},
                  ]},
                ]},
              ]},
              { id: "onboarding_completion", name: "Onboarding Completion", nameRu: "Завершение онбординга", children: [] },
              { id: "first_key_action_rate", name: "First Key Action Rate", nameRu: "Доля первого ключевого действия", children: [] },
              { id: "setup_success_rate", name: "Setup Success Rate", nameRu: "Успешность настройки", children: [] },
            ]},
            { id: "engagement", name: "Engagement", nameRu: "Вовлеченность", children: [] },
            { id: "retention", name: "Retention", nameRu: "Удержание", children: [] },
            { id: "virality", name: "Virality", nameRu: "Вирусность", children: [] },
          ],
        },
        { id: "arpu", name: "ARPU", nameRu: "Доход на пользователя", children: [] },
      ],
    },
    { id: "costs", name: "Costs", nameRu: "Затраты", children: [
      { id: "marketing_costs", name: "Marketing Costs", nameRu: "Маркетинговые расходы", children: [] },
      { id: "infrastructure_costs", name: "Infrastructure Costs", nameRu: "Инфраструктура", children: [] },
      { id: "development_costs", name: "Development Costs", nameRu: "Разработка", children: [] },
      { id: "support_costs", name: "Support Costs", nameRu: "Поддержка", children: [] },
    ]},
    { id: "organization", name: "Organization", nameRu: "Организация", children: [
      { id: "organization_team_maturity", name: "Team Maturity", nameRu: "Зрелость команды", children: [] },
      { id: "delivery_performance", name: "Delivery Performance", nameRu: "Эффективность доставки", children: [] },
    ]},
  ],
};

function flattenNode(node, level, out) {
  out.push({
    id: node.id,
    name: node.name,
    nameRu: node.nameRu,
    level,
  });
  for (const child of node.children || []) {
    flattenNode(child, level + 1, out);
  }
}

export function flattenMetricsTree(root = METRICS_TREE) {
  const out = [];
  flattenNode(root, 0, out);
  return out;
}
