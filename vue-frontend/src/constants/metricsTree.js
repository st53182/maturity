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
            {
              id: "acquisition",
              name: "Acquisition",
              nameRu: "Привлечение",
              children: [
                {
                  id: "conversion_to_signup",
                  name: "Conversion to Signup",
                  nameRu: "Конверсия в регистрацию",
                  children: [
                    {
                      id: "t2m",
                      name: "Time-to-Market (T2M)",
                      nameRu: "Время вывода фич",
                      children: [
                        {
                          id: "lead_time",
                          name: "Lead Time",
                          nameRu: "Lead Time",
                          children: [
                            {
                              id: "customer_lead_time",
                              name: "Customer Lead Time",
                              nameRu: "Время до ценности для пользователя",
                              children: [],
                            },
                            {
                              id: "cycle_time",
                              name: "Cycle Time",
                              nameRu: "Cycle Time",
                              children: [
                                { id: "wip", name: "WIP", nameRu: "WIP", children: [] },
                                { id: "blocked_time", name: "Blocked Time", nameRu: "Блокировки", children: [] },
                                { id: "flow_efficiency", name: "Flow Efficiency", nameRu: "Эффективность потока", children: [] },
                              ],
                            },
                            { id: "queue_time", name: "Queue Time", nameRu: "Очередь", children: [] },
                          ],
                        },
                        {
                          id: "deployment_frequency",
                          name: "Deployment Frequency",
                          nameRu: "Частота релизов",
                          children: [
                            { id: "throughput", name: "Throughput", nameRu: "Пропускная способность", children: [] },
                            {
                              id: "velocity",
                              name: "Velocity",
                              nameRu: "Velocity",
                              children: [
                                {
                                  id: "team_maturity",
                                  name: "Team Maturity",
                                  nameRu: "Зрелость команды",
                                  children: [
                                    { id: "process_maturity", name: "Process Maturity", nameRu: "Зрелость процессов", children: [] },
                                    {
                                      id: "engineering_practices",
                                      name: "Engineering Practices",
                                      nameRu: "Инженерные практики",
                                      children: [
                                        { id: "code_review_quality", name: "Code Review Quality", nameRu: "Качество code review", children: [] },
                                        { id: "test_coverage", name: "Test Coverage", nameRu: "Покрытие тестами", children: [] },
                                        { id: "cicd_maturity", name: "CI/CD Maturity", nameRu: "Зрелость CI/CD", children: [] },
                                      ],
                                    },
                                    { id: "team_autonomy", name: "Team Autonomy", nameRu: "Автономность команды", children: [] },
                                  ],
                                },
                              ],
                            },
                          ],
                        },
                      ],
                    },
                  ],
                },
                {
                  id: "activation",
                  name: "Activation",
                  nameRu: "Активация",
                  children: [
                    {
                      id: "ttfv",
                      name: "Time to First Value (TTFV)",
                      nameRu: "Time to First Value",
                      children: [
                        {
                          id: "activation_customer_lead_time",
                          name: "Customer Lead Time",
                          nameRu: "Customer Lead Time",
                          children: [
                            {
                              id: "activation_lead_time",
                              name: "Lead Time",
                              nameRu: "Lead Time",
                              children: [
                                {
                                  id: "activation_cycle_time",
                                  name: "Cycle Time",
                                  nameRu: "Cycle Time",
                                  children: [
                                    { id: "activation_wip", name: "WIP", nameRu: "WIP", children: [] },
                                    { id: "activation_flow_efficiency", name: "Flow Efficiency", nameRu: "Flow Efficiency", children: [] },
                                  ],
                                },
                                {
                                  id: "activation_deployment_frequency",
                                  name: "Deployment Frequency",
                                  nameRu: "Deployment Frequency",
                                  children: [
                                    { id: "activation_throughput", name: "Throughput", nameRu: "Throughput", children: [] },
                                    {
                                      id: "activation_velocity",
                                      name: "Velocity",
                                      nameRu: "Velocity",
                                      children: [{ id: "activation_team_maturity", name: "Team Maturity", nameRu: "Team Maturity", children: [] }],
                                    },
                                  ],
                                },
                              ],
                            },
                          ],
                        },
                        { id: "release_coordination", name: "Release Coordination", nameRu: "Согласование релизов", children: [] },
                      ],
                    },
                  ],
                },
                {
                  id: "retention",
                  name: "Retention",
                  nameRu: "Удержание",
                  children: [
                    {
                      id: "feature_adoption",
                      name: "Feature Adoption",
                      nameRu: "Использование фич",
                      children: [
                        {
                          id: "retention_t2m",
                          name: "Time-to-Market (T2M)",
                          nameRu: "Time-to-Market",
                          children: [
                            {
                              id: "retention_lead_time",
                              name: "Lead Time",
                              nameRu: "Lead Time",
                              children: [
                                {
                                  id: "retention_cycle_time",
                                  name: "Cycle Time",
                                  nameRu: "Cycle Time",
                                  children: [
                                    { id: "retention_wip", name: "WIP", nameRu: "WIP", children: [] },
                                    { id: "retention_blocked_time", name: "Blocked Time", nameRu: "Blocked Time", children: [] },
                                  ],
                                },
                                { id: "retention_customer_lead_time", name: "Customer Lead Time", nameRu: "Customer Lead Time", children: [] },
                              ],
                            },
                            {
                              id: "retention_deployment_frequency",
                              name: "Deployment Frequency",
                              nameRu: "Deployment Frequency",
                              children: [
                                { id: "retention_throughput", name: "Throughput", nameRu: "Throughput", children: [] },
                                {
                                  id: "retention_velocity",
                                  name: "Velocity",
                                  nameRu: "Velocity",
                                  children: [{ id: "retention_team_maturity", name: "Team Maturity", nameRu: "Team Maturity", children: [] }],
                                },
                              ],
                            },
                          ],
                        },
                        { id: "discoverability", name: "Discoverability", nameRu: "Находимость функций", children: [] },
                      ],
                    },
                    {
                      id: "retention_rate",
                      name: "Retention Rate",
                      nameRu: "Retention Rate",
                      children: [
                        { id: "ux_quality", name: "UX Quality", nameRu: "Качество UX", children: [] },
                        {
                          id: "stability",
                          name: "Stability",
                          nameRu: "Стабильность",
                          children: [
                            { id: "mttr", name: "MTTR", nameRu: "MTTR", children: [{ id: "mttr_team_maturity", name: "Team Maturity", nameRu: "Team Maturity", children: [] }] },
                            {
                              id: "change_failure_rate",
                              name: "Change Failure Rate",
                              nameRu: "Change Failure Rate",
                              children: [{ id: "cfr_engineering_practices", name: "Engineering Practices", nameRu: "Engineering Practices", children: [] }],
                            },
                          ],
                        },
                      ],
                    },
                  ],
                },
                {
                  id: "engagement",
                  name: "Engagement",
                  nameRu: "Вовлеченность",
                  children: [
                    {
                      id: "sessions_per_user",
                      name: "Sessions per User",
                      nameRu: "Сессии на пользователя",
                      children: [
                        {
                          id: "performance",
                          name: "Performance",
                          nameRu: "Производительность",
                          children: [
                            { id: "latency", name: "Latency", nameRu: "Задержка", children: [] },
                            {
                              id: "uptime",
                              name: "Uptime",
                              nameRu: "Доступность",
                              children: [
                                { id: "uptime_mttr", name: "MTTR", nameRu: "MTTR", children: [] },
                                { id: "uptime_team_maturity", name: "Team Maturity", nameRu: "Team Maturity", children: [] },
                              ],
                            },
                          ],
                        },
                      ],
                    },
                    {
                      id: "feature_quality",
                      name: "Feature Quality",
                      nameRu: "Качество фич",
                      children: [
                        {
                          id: "defect_rate",
                          name: "Defect Rate",
                          nameRu: "Доля дефектов",
                          children: [
                            { id: "rework_rate", name: "Rework Rate", nameRu: "Доля переделок", children: [] },
                            { id: "tech_debt", name: "Tech Debt", nameRu: "Техдолг", children: [{ id: "tech_debt_team_maturity", name: "Team Maturity", nameRu: "Team Maturity", children: [] }] },
                          ],
                        },
                        {
                          id: "bug_escape_rate",
                          name: "Bug Escape Rate",
                          nameRu: "Bug Escape Rate",
                          children: [{ id: "bug_engineering_practices", name: "Engineering Practices", nameRu: "Engineering Practices", children: [] }],
                        },
                      ],
                    },
                  ],
                },
              ],
            },
          ],
        },
      ],
    },
    {
      id: "costs",
      name: "Costs",
      nameRu: "Затраты",
      children: [
        {
          id: "development_costs",
          name: "Development Costs",
          nameRu: "Стоимость разработки",
          children: [
            {
              id: "productivity",
              name: "Productivity",
              nameRu: "Продуктивность",
              children: [
                { id: "cost_throughput", name: "Throughput", nameRu: "Throughput", children: [] },
                { id: "cost_velocity", name: "Velocity", nameRu: "Velocity", children: [{ id: "cost_team_maturity", name: "Team Maturity", nameRu: "Team Maturity", children: [] }] },
                {
                  id: "cost_lead_time",
                  name: "Lead Time",
                  nameRu: "Lead Time",
                  children: [
                    {
                      id: "cost_cycle_time",
                      name: "Cycle Time",
                      nameRu: "Cycle Time",
                      children: [
                        { id: "cost_wip", name: "WIP", nameRu: "WIP", children: [] },
                        { id: "cost_blocked_time", name: "Blocked Time", nameRu: "Blocked Time", children: [] },
                      ],
                    },
                  ],
                },
              ],
            },
            {
              id: "inefficiency_cost",
              name: "Inefficiency Cost",
              nameRu: "Потери эффективности",
              children: [
                { id: "long_lead_time", name: "Long Lead Time", nameRu: "Длинный Lead Time", children: [] },
                { id: "rework", name: "Rework", nameRu: "Переделки", children: [] },
                { id: "context_switching", name: "Context Switching", nameRu: "Переключение контекста (из-за WIP)", children: [] },
              ],
            },
          ],
        },
      ],
    },
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
