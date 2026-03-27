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
                  id: "traffic_volume",
                  name: "Traffic Volume",
                  nameRu: "Объем трафика",
                  children: [
                    { id: "paid_traffic", name: "Paid Traffic", nameRu: "Платный трафик", children: [] },
                    { id: "organic_traffic", name: "Organic Traffic", nameRu: "Органический трафик", children: [] },
                    { id: "referral_traffic", name: "Referral Traffic", nameRu: "Реферальный трафик", children: [] },
                    { id: "direct_traffic", name: "Direct Traffic", nameRu: "Прямой трафик", children: [] },
                    { id: "viral_coefficient", name: "Viral Coefficient", nameRu: "Вирусный коэффициент", children: [] },
                  ],
                },
                {
                  id: "conversion_to_signup",
                  name: "Conversion to Signup",
                  nameRu: "Конверсия в регистрацию",
                  children: [
                    { id: "ctr", name: "CTR", nameRu: "Кликабельность", children: [] },
                    { id: "landing_page_conversion", name: "Landing Page Conversion", nameRu: "Конверсия лендинга", children: [] },
                    { id: "ux_clarity", name: "UX Clarity", nameRu: "Понятность интерфейса", children: [] },
                    { id: "trust_signals", name: "Trust Signals", nameRu: "Сигналы доверия", children: [] },
                    {
                      id: "page_load_time",
                      name: "Page Load Time",
                      nameRu: "Время загрузки страницы",
                      children: [
                        { id: "latency", name: "Latency", nameRu: "Задержка", children: [] },
                        {
                          id: "backend_performance",
                          name: "Backend Performance",
                          nameRu: "Производительность бэкенда",
                          children: [
                            {
                              id: "uptime",
                              name: "Uptime",
                              nameRu: "Доступность",
                              children: [
                                { id: "mttr", name: "MTTR", nameRu: "Время восстановления", children: [] },
                                { id: "incident_frequency", name: "Incident Frequency", nameRu: "Частота инцидентов", children: [] },
                              ],
                            },
                            { id: "system_throughput", name: "System Throughput", nameRu: "Пропускная способность системы", children: [] },
                          ],
                        },
                      ],
                    },
                  ],
                },
                {
                  id: "cac",
                  name: "CAC",
                  nameRu: "Стоимость привлечения клиента",
                  children: [
                    { id: "cost_per_click", name: "Cost per Click", nameRu: "Стоимость клика", children: [] },
                    { id: "cost_per_install", name: "Cost per Install", nameRu: "Стоимость установки", children: [] },
                    { id: "channel_efficiency", name: "Channel Efficiency", nameRu: "Эффективность каналов", children: [] },
                  ],
                },
                {
                  id: "marketing_efficiency",
                  name: "Marketing Efficiency",
                  nameRu: "Эффективность маркетинга",
                  children: [
                    { id: "marketing_roi", name: "Marketing ROI", nameRu: "Рентабельность маркетинга", children: [] },
                    { id: "ltv_cac", name: "LTV/CAC", nameRu: "Соотношение LTV к CAC", children: [] },
                  ],
                },
              ],
            },
            {
              id: "activation",
              name: "Activation",
              nameRu: "Активация",
              children: [
                { id: "activation_rate", name: "Activation Rate", nameRu: "Доля активированных пользователей", children: [] },
                {
                  id: "time_to_first_value",
                  name: "Time to First Value",
                  nameRu: "Время до первой ценности",
                  children: [
                    {
                      id: "customer_lead_time",
                      name: "Customer Lead Time",
                      nameRu: "Время доставки ценности пользователю",
                      children: [
                        {
                          id: "lead_time",
                          name: "Lead Time",
                          nameRu: "Время от идеи до релиза",
                          children: [
                            {
                              id: "cycle_time",
                              name: "Cycle Time",
                              nameRu: "Время выполнения задачи",
                              children: [
                                { id: "wip", name: "WIP", nameRu: "Незавершенная работа", children: [] },
                                { id: "blocked_time", name: "Blocked Time", nameRu: "Время блокировок", children: [] },
                                { id: "flow_efficiency", name: "Flow Efficiency", nameRu: "Эффективность потока", children: [] },
                              ],
                            },
                            { id: "queue_time", name: "Queue Time", nameRu: "Время ожидания", children: [] },
                          ],
                        },
                        {
                          id: "deployment_frequency",
                          name: "Deployment Frequency",
                          nameRu: "Частота релизов",
                          children: [
                            { id: "throughput", name: "Throughput", nameRu: "Пропускная способность команды", children: [] },
                            {
                              id: "velocity",
                              name: "Velocity",
                              nameRu: "Скорость команды",
                              children: [
                                {
                                  id: "team_maturity",
                                  name: "Team Maturity",
                                  nameRu: "Зрелость команды",
                                  children: [
                                    { id: "engineering_maturity", name: "Engineering Maturity", nameRu: "Зрелость инженерии", children: [] },
                                    { id: "process_maturity", name: "Process Maturity", nameRu: "Зрелость процессов", children: [] },
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
                { id: "onboarding_completion", name: "Onboarding Completion", nameRu: "Завершение онбординга", children: [] },
                { id: "first_key_action_rate", name: "First Key Action Rate", nameRu: "Доля первого ключевого действия", children: [] },
                { id: "setup_success_rate", name: "Setup Success Rate", nameRu: "Успешность настройки", children: [] },
              ],
            },
            {
              id: "engagement",
              name: "Engagement",
              nameRu: "Вовлеченность",
              children: [
                { id: "dau_mau", name: "DAU / MAU", nameRu: "Дневная/месячная аудитория", children: [] },
                { id: "stickiness", name: "Stickiness", nameRu: "Липкость", children: [] },
                { id: "sessions_per_user", name: "Sessions per User", nameRu: "Сессий на пользователя", children: [] },
                { id: "session_duration", name: "Session Duration", nameRu: "Длительность сессии", children: [] },
                { id: "core_action_frequency", name: "Core Action Frequency", nameRu: "Частота ключевого действия", children: [] },
                {
                  id: "feature_adoption_rate",
                  name: "Feature Adoption Rate",
                  nameRu: "Использование фич",
                  children: [
                    { id: "discoverability", name: "Discoverability", nameRu: "Обнаруживаемость", children: [] },
                    {
                      id: "time_to_market",
                      name: "Time-to-Market",
                      nameRu: "Скорость вывода фич",
                      children: [
                        { id: "t2m_lead_time", name: "Lead Time", nameRu: "Lead Time", children: [] },
                        {
                          id: "t2m_deployment_frequency",
                          name: "Deployment Frequency",
                          nameRu: "Частота релизов",
                          children: [
                            { id: "t2m_throughput", name: "Throughput", nameRu: "Throughput", children: [] },
                            {
                              id: "t2m_velocity",
                              name: "Velocity",
                              nameRu: "Velocity",
                              children: [{ id: "t2m_team_maturity", name: "Team Maturity", nameRu: "Зрелость команды", children: [] }],
                            },
                          ],
                        },
                      ],
                    },
                  ],
                },
                { id: "notification_ctr", name: "Notification CTR", nameRu: "Кликабельность уведомлений", children: [] },
              ],
            },
            {
              id: "retention",
              name: "Retention",
              nameRu: "Удержание",
              children: [
                { id: "retention_d1_d7_d30", name: "Retention D1/D7/D30", nameRu: "Удержание по дням", children: [] },
                { id: "cohort_retention", name: "Cohort Retention", nameRu: "Когортное удержание", children: [] },
                { id: "churn_rate", name: "Churn Rate", nameRu: "Отток", children: [] },
                { id: "reactivation_rate", name: "Reactivation Rate", nameRu: "Реактивация", children: [] },
                {
                  id: "user_lifetime",
                  name: "User Lifetime",
                  nameRu: "Жизненный цикл пользователя",
                  children: [
                    { id: "ux_quality", name: "UX Quality", nameRu: "Качество UX", children: [] },
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
                            { id: "rework_rate", name: "Rework Rate", nameRu: "Переделки", children: [] },
                            { id: "tech_debt", name: "Tech Debt", nameRu: "Технический долг", children: [] },
                          ],
                        },
                        {
                          id: "bug_escape_rate",
                          name: "Bug Escape Rate",
                          nameRu: "Продакшн-баги",
                          children: [
                            { id: "code_review_time", name: "Code Review Time", nameRu: "Время ревью", children: [] },
                            { id: "test_coverage", name: "Test Coverage", nameRu: "Покрытие тестами", children: [] },
                          ],
                        },
                      ],
                    },
                    {
                      id: "stability",
                      name: "Stability",
                      nameRu: "Стабильность",
                      children: [
                        { id: "stability_uptime", name: "Uptime", nameRu: "Доступность", children: [] },
                        { id: "change_failure_rate", name: "Change Failure Rate", nameRu: "Доля неудачных изменений", children: [] },
                        { id: "stability_mttr", name: "MTTR", nameRu: "Время восстановления", children: [] },
                      ],
                    },
                  ],
                },
              ],
            },
            {
              id: "virality",
              name: "Virality",
              nameRu: "Вирусность",
              children: [
                { id: "invite_rate", name: "Invite Rate", nameRu: "Доля приглашений", children: [] },
                { id: "share_rate", name: "Share Rate", nameRu: "Доля шаринга", children: [] },
                { id: "k_factor", name: "K-factor", nameRu: "Коэффициент вирусности", children: [] },
              ],
            },
          ],
        },
        {
          id: "arpu",
          name: "ARPU",
          nameRu: "Доход на пользователя",
          children: [
            {
              id: "conversion_to_paid",
              name: "Conversion to Paid",
              nameRu: "Конверсия в оплату",
              children: [
                { id: "paywall_conversion", name: "Paywall Conversion", nameRu: "Конверсия paywall", children: [] },
                { id: "trial_conversion", name: "Trial Conversion", nameRu: "Конверсия триала", children: [] },
                { id: "checkout_conversion", name: "Checkout Conversion", nameRu: "Конверсия оплаты", children: [] },
                {
                  id: "payment_success_rate",
                  name: "Payment Success Rate",
                  nameRu: "Успешность платежа",
                  children: [
                    {
                      id: "payment_errors",
                      name: "Payment Errors",
                      nameRu: "Ошибки платежа",
                      children: [
                        {
                          id: "payment_defect_rate",
                          name: "Defect Rate",
                          nameRu: "Дефекты",
                          children: [{ id: "payment_tech_debt", name: "Tech Debt", nameRu: "Техдолг", children: [] }],
                        },
                      ],
                    },
                  ],
                },
              ],
            },
            { id: "arppu", name: "ARPPU", nameRu: "Доход на платящего пользователя", children: [] },
            { id: "average_check", name: "Average Check", nameRu: "Средний чек", children: [] },
            { id: "purchase_frequency", name: "Purchase Frequency", nameRu: "Частота покупок", children: [] },
            { id: "expansion_revenue", name: "Expansion Revenue", nameRu: "Дополнительный доход", children: [] },
            { id: "upsell_rate", name: "Upsell Rate", nameRu: "Апсейл", children: [] },
            { id: "cross_sell_rate", name: "Cross-sell Rate", nameRu: "Кросс-сейл", children: [] },
            { id: "discount_rate", name: "Discount Rate", nameRu: "Скидки", children: [] },
            { id: "pricing_power", name: "Pricing Power", nameRu: "Ценовая сила", children: [] },
            {
              id: "ltv",
              name: "LTV",
              nameRu: "Пожизненная ценность",
              children: [
                { id: "ltv_arpu", name: "ARPU", nameRu: "ARPU", children: [] },
                { id: "ltv_retention", name: "Retention", nameRu: "Удержание", children: [] },
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
          id: "marketing_costs",
          name: "Marketing Costs",
          nameRu: "Маркетинговые расходы",
          children: [
            { id: "costs_cac", name: "CAC", nameRu: "CAC", children: [] },
            { id: "channel_spend", name: "Channel Spend", nameRu: "Расходы по каналам", children: [] },
          ],
        },
        {
          id: "infrastructure_costs",
          name: "Infrastructure Costs",
          nameRu: "Инфраструктура",
          children: [
            { id: "compute_cost", name: "Compute Cost", nameRu: "Вычисления", children: [] },
            { id: "storage_cost", name: "Storage Cost", nameRu: "Хранение", children: [] },
            { id: "network_cost", name: "Network Cost", nameRu: "Сеть", children: [] },
            {
              id: "infrastructure_efficiency",
              name: "Efficiency",
              nameRu: "Эффективность",
              children: [
                { id: "resource_utilization", name: "Resource Utilization", nameRu: "Использование ресурсов", children: [] },
                { id: "optimization_level", name: "Optimization Level", nameRu: "Уровень оптимизации", children: [] },
              ],
            },
          ],
        },
        {
          id: "development_costs",
          name: "Development Costs",
          nameRu: "Разработка",
          children: [
            { id: "team_size", name: "Team Size", nameRu: "Размер команды", children: [] },
            { id: "cost_per_engineer", name: "Cost per Engineer", nameRu: "Стоимость разработчика", children: [] },
            {
              id: "productivity",
              name: "Productivity",
              nameRu: "Продуктивность",
              children: [
                { id: "productivity_throughput", name: "Throughput", nameRu: "Throughput", children: [] },
                { id: "productivity_velocity", name: "Velocity", nameRu: "Velocity", children: [] },
                { id: "productivity_lead_time", name: "Lead Time", nameRu: "Lead Time", children: [] },
              ],
            },
          ],
        },
        {
          id: "support_costs",
          name: "Support Costs",
          nameRu: "Поддержка",
          children: [
            { id: "ticket_volume", name: "Ticket Volume", nameRu: "Количество тикетов", children: [] },
            { id: "cost_per_ticket", name: "Cost per Ticket", nameRu: "Стоимость тикета", children: [] },
            {
              id: "resolution_time",
              name: "Resolution Time",
              nameRu: "Время решения",
              children: [{ id: "support_mttr", name: "MTTR", nameRu: "MTTR", children: [] }],
            },
          ],
        },
      ],
    },
    {
      id: "organization",
      name: "Organization",
      nameRu: "Организация",
      children: [
        {
          id: "organization_team_maturity",
          name: "Team Maturity",
          nameRu: "Зрелость команды",
          children: [
            {
              id: "organization_engineering_maturity",
              name: "Engineering Maturity",
              nameRu: "Зрелость разработки",
              children: [
                { id: "organization_test_coverage", name: "Test Coverage", nameRu: "Покрытие тестами", children: [] },
                { id: "cicd_level", name: "CI/CD Level", nameRu: "Уровень CI/CD", children: [] },
                { id: "code_quality", name: "Code Quality", nameRu: "Качество кода", children: [] },
              ],
            },
            {
              id: "organization_process_maturity",
              name: "Process Maturity",
              nameRu: "Зрелость процессов",
              children: [
                { id: "agile_adoption", name: "Agile Adoption", nameRu: "Применение Agile", children: [] },
                { id: "planning_accuracy", name: "Planning Accuracy", nameRu: "Точность планирования", children: [] },
                { id: "predictability", name: "Predictability", nameRu: "Предсказуемость", children: [] },
              ],
            },
            {
              id: "team_health",
              name: "Team Health",
              nameRu: "Состояние команды",
              children: [
                { id: "enps", name: "eNPS", nameRu: "Удовлетворенность команды", children: [] },
                { id: "burnout", name: "Burnout", nameRu: "Выгорание", children: [] },
                { id: "turnover_rate", name: "Turnover Rate", nameRu: "Текучесть", children: [] },
              ],
            },
          ],
        },
        {
          id: "delivery_performance",
          name: "Delivery Performance",
          nameRu: "Эффективность доставки",
          children: [
            { id: "delivery_lead_time", name: "Lead Time", nameRu: "Lead Time", children: [] },
            { id: "delivery_cycle_time", name: "Cycle Time", nameRu: "Cycle Time", children: [] },
            { id: "delivery_deployment_frequency", name: "Deployment Frequency", nameRu: "Частота релизов", children: [] },
            { id: "delivery_change_failure_rate", name: "Change Failure Rate", nameRu: "Ошибки изменений", children: [] },
            { id: "delivery_mttr", name: "MTTR", nameRu: "MTTR", children: [] },
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
