/** Full form examples for «Project management map» — language-specific. */

export function getProjectCardExampleRu() {
  return {
    projectName: 'Запуск нового филиала',
    tasks: [
      { name: 'Согласовать аренду с юристами', status: 'progress', deadline: '15.04', who: 'PM' },
      { name: 'Заказ оборудования у поставщика', status: 'risk', deadline: '22.04', who: 'Ops' },
      { name: 'Обучение персонала', status: 'waiting', deadline: '01.05', who: 'HR' },
    ],
    prioritiesMust: ['Открыть точку к дате X', 'Пройти проверку безопасности'],
    prioritiesShould: ['Запустить маркетинг в соцсетях'],
    prioritiesNice: ['Брендированная вывеска премиум-класса'],
    dependenciesText:
      'Зависим от юридического отдела по договору аренды и от IT — выделение сети и учётных записей. ' +
      'Внешний подрядчик по охране должен подтвердить график до начала монтажа. Поставка оборудования привязана к таможне — задержка на 1–2 недели возможна.',
    bottlenecks: [
      { title: 'Согласования в торговом центре', desc: 'Долгие согласования изменений планировки; без них нельзя начать отделку.' },
      { title: 'Кадровый гэп', desc: 'Не хватает обученных сменных руководителей на старте.' },
    ],
    roles: [
      { name: 'Руководитель проекта', tasksCount: 6, overloadRisk: 'medium' },
      { name: 'Операционный менеджер', tasksCount: 4, overloadRisk: 'normal' },
      { name: 'Юрист', tasksCount: 2, overloadRisk: 'high' },
    ],
    decisions: [
      {
        question: 'Нанимать подрядчика на отделку пакетом или по этапам?',
        context: 'Пакет дешевле, но жёсткий срок; по этапам — гибче, но дороже на 12%.',
      },
    ],
  };
}

export function getProjectCardExampleEn() {
  return {
    projectName: 'New branch opening',
    tasks: [
      { name: 'Legal review of lease', status: 'progress', deadline: '15 Apr', who: 'PM' },
      { name: 'Order equipment from vendor', status: 'risk', deadline: '22 Apr', who: 'Ops' },
      { name: 'Staff training', status: 'waiting', deadline: '1 May', who: 'HR' },
    ],
    prioritiesMust: ['Open on time for launch date X', 'Pass safety inspection'],
    prioritiesShould: ['Run social media campaign'],
    prioritiesNice: ['Premium branded signage'],
    dependenciesText:
      'We depend on Legal for the lease and on IT for network accounts and access. ' +
      'The security vendor must confirm schedules before fit-out starts. Equipment delivery is tied to customs — a 1–2 week slip is possible.',
    bottlenecks: [
      { title: 'Mall approvals', desc: 'Slow approvals for layout changes; fit-out cannot start without them.' },
      { title: 'Shift lead gap', desc: 'Not enough trained shift leads for opening week.' },
    ],
    roles: [
      { name: 'Project lead', tasksCount: 6, overloadRisk: 'medium' },
      { name: 'Operations manager', tasksCount: 4, overloadRisk: 'normal' },
      { name: 'Legal counsel', tasksCount: 2, overloadRisk: 'high' },
    ],
    decisions: [
      {
        question: 'Hire one fit-out contractor vs phased vendors?',
        context: 'Single package is cheaper but rigid on dates; phased is flexible but ~12% more expensive.',
      },
    ],
  };
}
