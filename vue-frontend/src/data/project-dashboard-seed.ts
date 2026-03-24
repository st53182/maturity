import type { DashboardState } from '@/types/project-dashboard'

/** Демо-проект: платформа продукта (согласовано с контекстом GrowBoard) */
export function createProjectDashboardSeed(): DashboardState {
  return {
    project: {
      id: 'proj-growboard',
      name: 'GrowBoard — платформа развития команд',
      description: 'Единая точка входа для оценок, дорожных карт и командной динамики.',
      period: { start: '2026-01-06', end: '2026-06-30' },
      teamIds: ['team-core', 'team-pm']
    },
    teams: [
      { id: 'team-core', name: 'Core & Delivery' },
      { id: 'team-pm', name: 'Product & PM' }
    ],
    owners: [
      { id: 'u-anna', name: 'Анна В.', teamId: 'team-pm' },
      { id: 'u-boris', name: 'Борис К.', teamId: 'team-core' },
      { id: 'u-chloe', name: 'Хлоя М.', teamId: 'team-core' },
      { id: 'u-dmitry', name: 'Дмитрий С.', teamId: 'team-pm' },
      { id: 'u-elena', name: 'Елена Р.', teamId: 'team-core' }
    ],
    goals: [
      {
        id: 'g-1',
        projectId: 'proj-growboard',
        title: 'Запустить новый project dashboard в прод',
        targetDate: '2026-05-15'
      },
      {
        id: 'g-2',
        projectId: 'proj-growboard',
        title: 'Снизить время онбординга команд на инструменты',
        targetDate: '2026-06-01'
      }
    ],
    milestones: [
      { id: 'ms-alpha', projectId: 'proj-growboard', title: 'Alpha (внутренняя)', date: '2026-03-01' },
      { id: 'ms-beta', projectId: 'proj-growboard', title: 'Beta (пилотные команды)', date: '2026-04-20' },
      { id: 'ms-ga', projectId: 'proj-growboard', title: 'GA релиз', date: '2026-05-30' },
      { id: 'ms-review', projectId: 'proj-growboard', title: 'Q2 review', date: '2026-06-25' }
    ],
    initiatives: [
      { id: 'in-ux', projectId: 'proj-growboard', goalId: 'g-1', title: 'UX и навигация' },
      { id: 'in-data', projectId: 'proj-growboard', goalId: 'g-1', title: 'Данные и API дорожной карты' },
      { id: 'in-growth', projectId: 'proj-growboard', goalId: 'g-2', title: 'Онбординг и гайды' }
    ],
    epics: [
      {
        id: 'ep-dash',
        projectId: 'proj-growboard',
        initiativeId: 'in-ux',
        title: 'Project dashboard',
        ownerId: 'u-anna',
        status: 'in_progress',
        start: '2026-02-10',
        end: '2026-04-15'
      },
      {
        id: 'ep-roadmap',
        projectId: 'proj-growboard',
        initiativeId: 'in-data',
        title: 'Roadmap v2 и зависимости',
        ownerId: 'u-boris',
        status: 'in_progress',
        start: '2026-01-20',
        end: '2026-05-01'
      },
      {
        id: 'ep-auth',
        projectId: 'proj-growboard',
        initiativeId: 'in-data',
        title: 'Доступы и шаринг',
        ownerId: 'u-chloe',
        status: 'planned',
        start: '2026-03-01',
        end: '2026-04-10'
      },
      {
        id: 'ep-docs',
        projectId: 'proj-growboard',
        initiativeId: 'in-growth',
        title: 'Документация и шаблоны',
        ownerId: 'u-dmitry',
        status: 'backlog',
        start: '2026-04-01',
        end: '2026-06-15'
      },
      {
        id: 'ep-perf',
        projectId: 'proj-growboard',
        initiativeId: 'in-ux',
        title: 'Производительность фронта',
        ownerId: 'u-elena',
        status: 'blocked',
        start: '2026-02-01',
        end: '2026-03-30'
      }
    ],
    tasks: [
      {
        id: 'tk-shell',
        projectId: 'proj-growboard',
        epicId: 'ep-dash',
        title: 'Оболочка dashboard (топбар, сайдбар, drawer)',
        ownerId: 'u-anna',
        status: 'done',
        priority: 'p0',
        start: '2026-02-10',
        end: '2026-02-28',
        estimateDays: 10
      },
      {
        id: 'tk-roadmap-ui',
        projectId: 'proj-growboard',
        epicId: 'ep-dash',
        title: 'Roadmap view: шкала и группировки',
        ownerId: 'u-anna',
        status: 'in_progress',
        priority: 'p0',
        start: '2026-03-01',
        end: '2026-03-22',
        estimateDays: 12
      },
      {
        id: 'tk-graph',
        projectId: 'proj-growboard',
        epicId: 'ep-dash',
        title: 'Dependency map (граф)',
        ownerId: 'u-boris',
        status: 'in_progress',
        priority: 'p0',
        start: '2026-03-05',
        end: '2026-03-28',
        estimateDays: 14
      },
      {
        id: 'tk-filters',
        projectId: 'proj-growboard',
        epicId: 'ep-dash',
        title: 'Фильтры и сохранённые виды',
        ownerId: 'u-dmitry',
        status: 'planned',
        priority: 'p1',
        start: '2026-03-18',
        end: '2026-04-05',
        estimateDays: 8
      },
      {
        id: 'tk-derived',
        projectId: 'proj-growboard',
        epicId: 'ep-dash',
        title: 'Метрики: прогресс, блокеры, просрочки',
        ownerId: 'u-anna',
        status: 'in_progress',
        priority: 'p1',
        start: '2026-03-12',
        end: '2026-03-26',
        estimateDays: 6
      },
      {
        id: 'tk-api-map',
        projectId: 'proj-growboard',
        epicId: 'ep-roadmap',
        title: 'Маппинг Flask roadmap → доменная модель',
        ownerId: 'u-boris',
        status: 'in_progress',
        priority: 'p0',
        start: '2026-02-15',
        end: '2026-04-01',
        estimateDays: 18
      },
      {
        id: 'tk-migrate',
        projectId: 'proj-growboard',
        epicId: 'ep-roadmap',
        title: 'Миграции БД: статусы, даты, владельцы',
        ownerId: 'u-chloe',
        status: 'planned',
        priority: 'p0',
        start: '2026-03-20',
        end: '2026-04-25',
        estimateDays: 15
      },
      {
        id: 'tk-ws',
        projectId: 'proj-growboard',
        epicId: 'ep-roadmap',
        title: 'Синхронизация позиций по WebSocket',
        ownerId: 'u-chloe',
        status: 'done',
        priority: 'p1',
        start: '2026-01-20',
        end: '2026-02-20',
        estimateDays: 20
      },
      {
        id: 'tk-share',
        projectId: 'proj-growboard',
        epicId: 'ep-auth',
        title: 'Публичные ссылки и пароль',
        ownerId: 'u-chloe',
        status: 'planned',
        priority: 'p1',
        start: '2026-03-10',
        end: '2026-03-30',
        estimateDays: 10
      },
      {
        id: 'tk-roles',
        projectId: 'proj-growboard',
        epicId: 'ep-auth',
        title: 'Роли editor / viewer',
        ownerId: 'u-chloe',
        status: 'backlog',
        priority: 'p2',
        start: '2026-04-01',
        end: '2026-04-20',
        estimateDays: 12
      },
      {
        id: 'tk-guide',
        projectId: 'proj-growboard',
        epicId: 'ep-docs',
        title: 'Гайд «Первая дорожная карта»',
        ownerId: 'u-dmitry',
        status: 'backlog',
        priority: 'p2',
        start: '2026-04-10',
        end: '2026-05-10',
        estimateDays: 7
      },
      {
        id: 'tk-bundle',
        projectId: 'proj-growboard',
        epicId: 'ep-perf',
        title: 'Code-splitting тяжёлых чанков',
        ownerId: 'u-elena',
        status: 'blocked',
        priority: 'p1',
        start: '2026-02-05',
        end: '2026-03-10',
        estimateDays: 8
      },
      {
        id: 'tk-lazy',
        projectId: 'proj-growboard',
        epicId: 'ep-perf',
        title: 'Lazy-load графа и таблицы',
        ownerId: 'u-elena',
        status: 'planned',
        priority: 'p2',
        start: '2026-03-15',
        end: '2026-04-01',
        estimateDays: 5
      },
      {
        id: 'tk-a11y',
        projectId: 'proj-growboard',
        epicId: 'ep-dash',
        title: 'Клавиатурная навигация dashboard',
        ownerId: 'u-anna',
        status: 'planned',
        priority: 'p2',
        start: '2026-04-01',
        end: '2026-04-12',
        estimateDays: 5
      },
      {
        id: 'tk-unassigned',
        projectId: 'proj-growboard',
        epicId: 'ep-docs',
        title: 'Видео-тур по инструменту',
        ownerId: undefined,
        status: 'planned',
        priority: 'p3',
        start: '2026-05-01',
        end: '2026-05-20',
        estimateDays: 4
      },
      {
        id: 'tk-overdue',
        projectId: 'proj-growboard',
        epicId: 'ep-dash',
        title: 'Интеграционные тесты e2e',
        ownerId: 'u-boris',
        status: 'in_progress',
        priority: 'p1',
        start: '2026-02-01',
        end: '2026-03-01',
        estimateDays: 14
      }
    ],
    dependencies: [
      {
        id: 'd1',
        projectId: 'proj-growboard',
        fromId: 'tk-shell',
        toId: 'tk-roadmap-ui',
        type: 'blocks'
      },
      {
        id: 'd2',
        projectId: 'proj-growboard',
        fromId: 'tk-roadmap-ui',
        toId: 'tk-graph',
        type: 'blocks'
      },
      {
        id: 'd3',
        projectId: 'proj-growboard',
        fromId: 'tk-graph',
        toId: 'tk-filters',
        type: 'blocks'
      },
      {
        id: 'd4',
        projectId: 'proj-growboard',
        fromId: 'tk-api-map',
        toId: 'tk-migrate',
        type: 'blocks'
      },
      {
        id: 'd5',
        projectId: 'proj-growboard',
        fromId: 'tk-migrate',
        toId: 'tk-share',
        type: 'depends_on'
      },
      {
        id: 'd6',
        projectId: 'proj-growboard',
        fromId: 'tk-bundle',
        toId: 'tk-lazy',
        type: 'blocks'
      },
      {
        id: 'd7',
        projectId: 'proj-growboard',
        fromId: 'ep-roadmap',
        toId: 'tk-api-map',
        type: 'related_to'
      },
      {
        id: 'd8',
        projectId: 'proj-growboard',
        fromId: 'tk-derived',
        toId: 'tk-filters',
        type: 'related_to'
      },
      {
        id: 'd9',
        projectId: 'proj-growboard',
        fromId: 'tk-ws',
        toId: 'tk-api-map',
        type: 'precedes'
      }
    ],
    risks: [
      {
        id: 'r1',
        projectId: 'proj-growboard',
        title: 'Задержка миграций БД на проде',
        severity: 'high',
        linkedItemIds: ['tk-migrate', 'ep-roadmap'],
        mitigation: 'Фича-флаг и поэтапный rollout'
      },
      {
        id: 'r2',
        projectId: 'proj-growboard',
        title: 'Перегрузка графа при >200 узлах',
        severity: 'medium',
        linkedItemIds: ['tk-graph', 'tk-lazy'],
        mitigation: 'Упрощённый режим и виртуализация'
      }
    ],
    comments: [
      {
        id: 'c1',
        itemId: 'tk-roadmap-ui',
        authorId: 'u-dmitry',
        body: 'Нужны пресеты группировки: команда / владелец / тип.',
        createdAt: '2026-03-20T09:00:00Z'
      },
      {
        id: 'c2',
        itemId: 'tk-graph',
        authorId: 'u-anna',
        body: 'Подсветка критического пути обязательна для демо stakeholders.',
        createdAt: '2026-03-21T14:30:00Z'
      }
    ],
    activity: [
      {
        id: 'a1',
        itemId: 'tk-shell',
        at: '2026-02-27T16:00:00Z',
        actorId: 'u-anna',
        action: 'status',
        detail: 'in_progress → done'
      },
      {
        id: 'a2',
        itemId: 'tk-graph',
        at: '2026-03-22T11:00:00Z',
        actorId: 'u-boris',
        action: 'field',
        detail: 'Добавлена оценка 14d'
      },
      {
        id: 'a3',
        itemId: 'ep-perf',
        at: '2026-03-10T08:00:00Z',
        actorId: 'u-elena',
        action: 'status',
        detail: 'blocked: ждём профилирование'
      }
    ]
  }
}
