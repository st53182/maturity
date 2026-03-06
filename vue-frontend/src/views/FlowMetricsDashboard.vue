<template>
  <div class="flow-dashboard" :style="{ background: C.bg, color: C.text }">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
    <div class="flow-inner">
      <div class="flow-meta">Jira Flow Analytics</div>
      <h1 class="flow-title">Lead Time & Flow Efficiency</h1>
      <p class="flow-desc">51 ключевая бизнес-задача · вручную отобраны из 254 в выгрузке</p>

      <div class="flow-tabs">
        <button
          v-for="t in tabs"
          :key="t.id"
          type="button"
          :class="['tab-btn', { active: tab === t.id }]"
          :style="tab === t.id ? { background: C.accent, color: '#fff' } : {}"
          @click="tab = t.id"
        >
          {{ t.label }}
        </button>
      </div>

      <!-- OVERVIEW -->
      <template v-if="tab === 'overview'">
        <div class="metrics-row">
          <div v-for="m in overviewMetrics" :key="m.label" class="metric-card" :style="{ borderColor: C.border }">
            <div class="metric-label">{{ m.label }}</div>
            <div class="metric-value" :style="{ color: m.color }">{{ m.value }}</div>
            <div v-if="m.sub" class="metric-sub">{{ m.sub }}</div>
          </div>
        </div>
        <div class="grid-2">
          <section class="section-card" :style="{ borderColor: C.border }">
            <h2 class="section-title">Распределение Lead Time</h2>
            <p class="section-sub">51 бизнес-задача</p>
            <div class="chart-wrap chart-hist">
              <Bar v-if="histChartData" :data="histChartData" :options="histChartOptions" />
            </div>
            <p class="chart-note">Основная масса задач: 60-90 дней (18 задач)</p>
          </section>
          <section class="section-card" :style="{ borderColor: C.border }">
            <h2 class="section-title">Lead Time по направлениям</h2>
            <p class="section-sub">Медиана в днях · (кол-во задач)</p>
            <div class="cat-bars">
              <div v-for="(c, i) in catStats" :key="i" class="cat-row">
                <span class="cat-name">{{ c.name }}</span>
                <div class="cat-bar-bg">
                  <div class="cat-bar-fill" :style="{ width: (c.lt / maxCatLt) * 100 + '%', background: catColors[c.name] || C.dim }" />
                </div>
                <span class="cat-val">{{ c.lt }}д</span>
                <span class="cat-count">({{ c.count }})</span>
              </div>
            </div>
            <p class="chart-note">КРИФ — самый быстрый поток (28д). 9-ФЗ и регуляторика — самый медленный (89д).</p>
          </section>
        </div>
      </template>

      <!-- TOP 5 -->
      <template v-if="tab === 'top5'">
        <div class="top5-list">
          <section v-for="(t, i) in top5" :key="i" class="section-card top5-card" :style="{ borderColor: C.border }">
            <div class="top5-head">
              <div class="top5-num" :style="{ background: C.accent + '15', color: C.accent }">{{ i + 1 }}</div>
              <div class="top5-body">
                <div class="top5-name">{{ t.name }}</div>
                <div class="top5-stats">
                  <div>
                    <span class="stat-label">Lead Time</span>
                    <div class="stat-val" :style="{ color: C.accent }">{{ t.lt }}д</div>
                  </div>
                  <div>
                    <span class="stat-label">Flow Efficiency</span>
                    <div class="stat-val" :style="{ color: parseFloat(t.fe) > 50 ? C.green : C.amber }">{{ t.fe }}</div>
                  </div>
                  <div>
                    <span class="stat-label">Направление</span>
                    <span class="cat-tag" :style="{ background: catColors[t.cat] || C.dim }">{{ t.cat }}</span>
                  </div>
                </div>
                <p class="top5-why">{{ t.why }}</p>
              </div>
            </div>
          </section>
        </div>
      </template>

      <!-- ALL 51 -->
      <template v-if="tab === 'all'">
        <section class="section-card" :style="{ borderColor: C.border }">
          <h2 class="section-title">51 бизнес-задача по Lead Time</h2>
          <p class="section-sub">Цвет = направление · полупрозрачные = нет данных о статусах</p>
          <div class="chart-wrap chart-all">
            <Bar v-if="allTasksChartData" :data="allTasksChartData" :options="allTasksChartOptions" />
          </div>
          <div class="legend-row">
            <span v-for="name in legendCats" :key="name" class="legend-item">
              <span class="legend-dot" :style="{ background: catColors[name] }" />
              {{ name === 'Прод' ? 'Продукты и сервисы' : name === 'ПУ' ? 'Пакеты услуг' : name }}
            </span>
          </div>
        </section>
      </template>

      <!-- BOTTLENECKS -->
      <template v-if="tab === 'bottlenecks'">
        <div class="grid-2">
          <section class="section-card" :style="{ borderColor: C.border }">
            <h2 class="section-title">Работа vs Ожидание</h2>
            <p class="section-sub">41 задача с отслеженными статусами</p>
            <div class="value-wait-bar">
              <div class="vw-work" :style="{ width: valuePct + '%', background: C.accent }">{{ valuePct }}% работа</div>
              <div class="vw-wait" :style="{ background: C.orange }">{{ 100 - valuePct }}% ожидание</div>
            </div>
            <p class="vw-desc">
              <span :style="{ color: C.accent }">● Работа ({{ totalValue.toFixed(0) }}д)</span> — IN ANALYSIS, DEVELOPMENT, CODE REVIEW, TESTING, REGRESS<br />
              <span :style="{ color: C.orange }">● Ожидание ({{ totalWait.toFixed(0) }}д)</span> — NEW, BACKLOG, TO DO, READY TO DEV, DEV DONE, TESTING DONE, ПРИЕМКА, ПОДГ. СБОРКИ, READY TO REL., HOLD
            </p>
          </section>
          <section class="section-card" :style="{ borderColor: C.border }">
            <h2 class="section-title">Где теряется время</h2>
            <div class="bottleneck-list">
              <div v-for="(b, i) in bottleneckTop5" :key="i" class="bn-item">
                <div class="bn-num" :style="{ background: b.color + '15', color: b.color }">{{ i + 1 }}</div>
                <div>
                  <div class="bn-name">{{ b.name }} <span class="bn-days">· {{ b.days }}д avg</span> <span class="bn-type" :style="{ background: b.type === 'value' ? C.accent + '20' : C.orange + '20', color: b.type === 'value' ? C.accent : C.orange }">{{ b.type === 'value' ? 'работа' : 'ожидание' }}</span></div>
                  <div class="bn-desc">{{ b.desc }}</div>
                </div>
              </div>
            </div>
          </section>
        </div>
        <section class="section-card" :style="{ borderColor: C.border }">
          <h2 class="section-title">Среднее время по статусам</h2>
          <p class="section-sub">41 бизнес-задача с отслеженными статусами · дни</p>
          <div class="chart-wrap chart-status">
            <Bar v-if="statusChartData" :data="statusChartData" :options="statusChartOptions" />
          </div>
        </section>
      </template>

      <footer class="flow-footer" :style="{ borderColor: C.border }">
        <span>Lead Time = SUM − DONE (финальный статус исключён) · Flow Efficiency = работа / Lead Time</span>
        <span>41 из 51 задачи с данными о времени в статусах</span>
      </footer>
    </div>
  </div>
</template>

<script>
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Bar } from 'vue-chartjs';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const C = {
  bg: '#0a0e17', card: '#111827', border: '#1e293b',
  accent: '#3b82f6', green: '#10b981', amber: '#f59e0b', red: '#ef4444', orange: '#f97316',
  text: '#e2e8f0', muted: '#94a3b8', dim: '#64748b'
};

const histData = [
  { range: '<14д', count: 3 }, { range: '14-30д', count: 12 }, { range: '30-60д', count: 6 },
  { range: '60-90д', count: 18 }, { range: '90-120д', count: 9 }, { range: '120+д', count: 3 }
];

const catStats = [
  { name: 'КРИФ', count: 12, lt: 27.9 }, { name: 'Продукты и сервисы', count: 20, lt: 53.1 },
  { name: 'IBSO', count: 6, lt: 72.8 }, { name: 'OMNI', count: 6, lt: 80.0 },
  { name: '9-ФЗ / Регуляторика', count: 3, lt: 89.2 }, { name: 'МП / Бета / ПУ', count: 4, lt: 90.8 }
];

const statusData = [
  { name: 'DEVELOPMENT', avg: 20.0, type: 'value' }, { name: 'IN ANALYSIS', avg: 15.5, type: 'value' },
  { name: 'DEV DONE', avg: 6.0, type: 'wait' }, { name: 'HOLD', avg: 5.5, type: 'wait' },
  { name: 'READY TO DEV', avg: 5.1, type: 'wait' }, { name: 'NEW', avg: 4.8, type: 'wait' },
  { name: 'ПРИЕМКА', avg: 2.8, type: 'wait' }, { name: 'READY TO REL.', avg: 1.5, type: 'wait' },
  { name: 'BACKLOG', avg: 1.3, type: 'wait' }, { name: 'ПОДГ. СБОРКИ', avg: 1.1, type: 'wait' },
  { name: 'TESTING DONE', avg: 1.0, type: 'wait' }, { name: 'TO DO', avg: 0.6, type: 'wait' },
  { name: 'CODE REVIEW', avg: 0.4, type: 'value' }, { name: 'REGRESS', avg: 0.3, type: 'value' }
];

const top5 = [
  { name: '983147 Frontend Исполнение требований 9-ФЗ (MVP 0)', lt: 153.1, fe: '21%', cat: '9-ФЗ', why: 'Регуляторные требования — обязательно к выполнению. Самый длинный Lead Time из ключевых задач.' },
  { name: '[OMNI] Доставка карт через Сравни.ру (ОМНИ КФК Доставка)', lt: 81.0, fe: '96%', cat: 'OMNI', why: 'Новый канал привлечения клиентов через маркетплейс. Высокая FE — работа шла без простоев.' },
  { name: 'Бета 979444 КРЕДИТНЫЕ КАНИКУЛЫ ДЛЯ НОВОГО ФЛАГМАНА И КК С ПРИВЕТСТВЕННОЙ СТАВКОЙ ПРИ КЛИПЕ', lt: 89.8, fe: '19%', cat: 'Бета', why: 'Продуктовая фича кредитных карт. Низкая FE — 80% времени задача ждала в очередях.' },
  { name: '981482. Сравни полная сделка — анализ и разработка Криф, ФТ', lt: 25.9, fe: '50%', cat: 'КРИФ', why: 'Интеграция со Сравни.ру — канал дистрибуции. Один из лучших показателей Lead Time.' },
  { name: 'МП 985106. Направление клиентам push/SMS при блокировке платежных карт по фроду в онлайн режиме', lt: 91.7, fe: '33%', cat: 'МП', why: 'Клиентский сервис и безопасность. Треть времени — работа, остальное — ожидание.' }
];

const allTasks = [
  { name: '983147 Frontend 9-ФЗ (MVP 0)', lt: 153.1, fe: 21.0, cat: '9-ФЗ', hd: true },
  { name: '978939. Справочник статусов криф', lt: 122.8, fe: null, cat: 'КРИФ', hd: false },
  { name: 'Моментальные карты в ПУ в офисах', lt: 120.1, fe: 97.5, cat: 'ПУ', hd: true },
  { name: 'Патч обновления анкеты с ИНН', lt: 111.0, fe: 87.2, cat: 'Прод', hd: true },
  { name: 'Период охлаждения при закрытии ДК', lt: 110.8, fe: null, cat: 'Прод', hd: false },
  { name: '[OMNI] Автоактивация МИДЛ', lt: 107.7, fe: 97.6, cat: 'OMNI', hd: true },
  { name: '987008. Анализ и разработка Ритейл', lt: 103.7, fe: 7.7, cat: 'Прод', hd: true },
  { name: '987717. Доработка Ритейл', lt: 103.7, fe: 44.9, cat: 'Прод', hd: true },
  { name: 'Выплата процентов в единую дату', lt: 98.1, fe: 20.5, cat: 'Прод', hd: true },
  { name: '[OMNI] Доп карты к цифровым КК', lt: 92.0, fe: 100.0, cat: 'OMNI', hd: true },
  { name: 'МП 985106 Push/SMS при фроде', lt: 91.7, fe: 33.2, cat: 'МП', hd: true },
  { name: 'Ограничение возраста заказ ДК', lt: 91.3, fe: null, cat: 'Прод', hd: false },
  { name: 'Бета 979444 Кредитные каникулы', lt: 89.8, fe: 18.8, cat: 'Бета', hd: true },
  { name: '985604. Доработки Ритейл 9ФЗ', lt: 89.2, fe: 66.3, cat: '9-ФЗ', hd: true },
  { name: 'Every Lounge', lt: 88.9, fe: 100.0, cat: 'Прод', hd: true },
  { name: 'Изменение тарифов 01.10.2025', lt: 88.2, fe: 11.7, cat: 'Прод', hd: true },
  { name: 'IBSO Стань клиентом Уралсиб', lt: 88.1, fe: 63.7, cat: 'IBSO', hd: true },
  { name: 'Ограничение счетов несовершен.', lt: 86.6, fe: 10.8, cat: 'IBSO', hd: true },
  { name: '[OMNI] Доставка через Сравни.ру', lt: 81.0, fe: 96.2, cat: 'OMNI', hd: true },
  { name: '[OMNI] Стань клиентом Уралсиб', lt: 78.9, fe: 85.0, cat: 'OMNI', hd: true },
  { name: 'Доставка ДК/ЗПК нерезиденты IBSO', lt: 74.9, fe: 38.4, cat: 'IBSO', hd: true },
  { name: 'Заказ Момент. карт в ПУ на сайте', lt: 74.9, fe: 74.7, cat: 'ПУ', hd: true },
  { name: 'Запрет расходных операций IBSO', lt: 70.8, fe: 43.6, cat: 'IBSO', hd: true },
  { name: '975530. Доработка IBSO-Retail', lt: 70.1, fe: 32.8, cat: 'IBSO', hd: true },
  { name: 'ЗП Документ с кодом 91 IBSO', lt: 67.7, fe: 29.5, cat: 'IBSO', hd: true },
  { name: 'Добавление печатных форм', lt: 66.2, fe: 100.0, cat: 'Прод', hd: true },
  { name: '986595. Разработка Криф', lt: 65.2, fe: 66.0, cat: 'КРИФ', hd: true },
  { name: '[OMNI] Единое окно оператора ч.2', lt: 65.1, fe: 68.8, cat: 'OMNI', hd: true },
  { name: '987894. Разработка Криф', lt: 64.0, fe: 56.0, cat: 'КРИФ', hd: true },
  { name: 'ЕФС Согласие на обработку ПДн', lt: 63.2, fe: 100.0, cat: 'Прод', hd: true },
  { name: 'Бета 985280 9-ФЗ', lt: 53.8, fe: null, cat: '9-ФЗ', hd: false },
  { name: '987810. Разработка Криф', lt: 43.2, fe: 5.6, cat: 'КРИФ', hd: true },
  { name: '985872. Разработка Ритейл', lt: 43.1, fe: 62.3, cat: 'Прод', hd: true },
  { name: '988009. Разработка Криф', lt: 40.9, fe: 83.1, cat: 'КРИФ', hd: true },
  { name: 'Привязка мом. карты к депозиту', lt: 39.1, fe: null, cat: 'Прод', hd: false },
  { name: '[OMNI] Цифровое подписание ДК', lt: 37.8, fe: null, cat: 'OMNI', hd: false },
  { name: '988663. Разработка Криф Бета', lt: 29.9, fe: 5.0, cat: 'КРИФ', hd: true },
  { name: '987115. Семафор отключения СМС', lt: 26.5, fe: null, cat: 'Прод', hd: false },
  { name: '981482. Сравни полная сделка', lt: 25.9, fe: 49.7, cat: 'КРИФ', hd: true },
  { name: 'Корректировка учета кешбэк ФЛ', lt: 24.3, fe: 38.2, cat: 'Прод', hd: true },
  { name: '985451. Реализация Ритейл', lt: 21.0, fe: 67.2, cat: 'Прод', hd: true },
  { name: '988652 Новая ПП clip_credit_card', lt: 20.9, fe: 10.5, cat: 'Прод', hd: true },
  { name: 'Разработка и тестирование Криф', lt: 19.4, fe: 29.8, cat: 'КРИФ', hd: true },
  { name: '988621. Разработка Криф', lt: 15.9, fe: null, cat: 'КРИФ', hd: false },
  { name: '986056. Доработка ПФ Криф', lt: 14.9, fe: null, cat: 'КРИФ', hd: false },
  { name: '988384. Реализация Криф', lt: 14.8, fe: 11.9, cat: 'КРИФ', hd: true },
  { name: '987502. Разработка Криф', lt: 14.3, fe: 12.6, cat: 'КРИФ', hd: true },
  { name: '985442. Дебетовые карты IR', lt: 14.2, fe: 20.9, cat: 'Прод', hd: true },
  { name: '987057. Доработка и вывод', lt: 10.9, fe: 54.0, cat: 'Прод', hd: true },
  { name: '973955 Внедрение чат-бота', lt: 4.9, fe: 59.1, cat: 'Прод', hd: true },
  { name: '981516. Анализ 1 и 2 этап', lt: 2.9, fe: null, cat: 'Прод', hd: false }
];

const catColors = {
  'КРИФ': '#8b5cf6', '9-ФЗ': '#ec4899', 'OMNI': '#06b6d4', 'IBSO': '#f97316',
  'Бета': '#a855f7', 'ПУ': '#14b8a6', 'МП': '#eab308', 'Прод': '#3b82f6',
  '9-ФЗ / Регуляторика': '#ec4899', 'Продукты и сервисы': '#3b82f6', 'МП / Бета / ПУ': '#eab308'
};

const bottleneckTop5 = [
  { name: 'DEVELOPMENT', days: 20.0, desc: 'Самый долгий этап. Возможно, задачи слишком крупные для одного спринта.', color: C.red, type: 'value' },
  { name: 'IN ANALYSIS', days: 15.5, desc: 'Анализ занимает полмесяца. Декомпозиция задач может сократить.', color: C.red, type: 'value' },
  { name: 'DEV DONE', days: 6.0, desc: 'Очередь между разработкой и тестированием.', color: C.amber, type: 'wait' },
  { name: 'HOLD', days: 5.5, desc: 'Задачи заблокированы или ждут внешних зависимостей.', color: C.amber, type: 'wait' },
  { name: 'READY TO DEV', days: 5.1, desc: 'Проанализированные задачи ждут разработчика.', color: C.amber, type: 'wait' }
];

export default {
  name: 'FlowMetricsDashboard',
  components: { Bar },
  data() {
    return {
      C,
      tab: 'overview',
      tabs: [
        { id: 'overview', label: 'Обзор' },
        { id: 'top5', label: 'Топ-5 задач' },
        { id: 'all', label: 'Все 51 задача' },
        { id: 'bottlenecks', label: 'Узкие места' }
      ],
      catColors,
      histData,
      catStats,
      statusData,
      top5,
      allTasks,
      bottleneckTop5,
      legendCats: ['КРИФ', 'OMNI', 'IBSO', '9-ФЗ', 'Прод', 'Бета', 'МП', 'ПУ']
    };
  },
  computed: {
    maxCatLt() {
      return Math.max(...catStats.map(x => x.lt));
    },
    totalValue() {
      return statusData.filter(s => s.type === 'value').reduce((a, b) => a + b.avg, 0);
    },
    totalWait() {
      return statusData.filter(s => s.type === 'wait').reduce((a, b) => a + b.avg, 0);
    },
    totalAll() {
      return this.totalValue + this.totalWait;
    },
    valuePct() {
      return Math.round((this.totalValue / this.totalAll) * 100);
    },
    overviewMetrics() {
      return [
        { label: 'Lead Time (P50)', value: '66д', sub: 'медиана, 51 бизнес-задача', color: C.accent },
        { label: 'Lead Time (P85)', value: '101д', sub: '85-й перцентиль', color: C.amber },
        { label: 'Flow Efficiency', value: '50%', sub: 'медиана, 41 задача с данными', color: C.green },
        { label: 'С данными / Всего', value: '41/51', sub: 'у 10 задач статусы не велись', color: C.text }
      ];
    },
    histChartData() {
      const colors = [C.green, C.green, C.accent, C.amber, C.red, C.red];
      return {
        labels: histData.map(d => d.range),
        datasets: [{
          label: 'Задач',
          data: histData.map(d => d.count),
          backgroundColor: histData.map((_, i) => colors[i] || C.accent),
          borderRadius: 4
        }]
      };
    },
    histChartOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: C.dim, font: { size: 12 } } },
          y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: C.dim, font: { size: 12 } } }
        }
      };
    },
    allTasksChartData() {
      const colors = allTasks.map(t => {
        const c = catColors[t.cat] || C.dim;
        return t.hd ? c + 'd9' : c + '59';
      });
      return {
        labels: allTasks.map(d => d.name.length > 35 ? d.name.slice(0, 34) + '…' : d.name),
        datasets: [{
          label: 'Lead Time (дн)',
          data: allTasks.map(d => d.lt),
          backgroundColor: colors,
          borderRadius: 5,
          barThickness: 16
        }]
      };
    },
    allTasksChartOptions() {
      return {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: C.dim, font: { size: 11 } } },
          y: { grid: { display: false }, ticks: { color: C.muted, font: { size: 10 }, maxRotation: 0 } }
        }
      };
    },
    statusChartData() {
      return {
        labels: statusData.map(d => d.name),
        datasets: [{
          label: 'Дней',
          data: statusData.map(d => d.avg),
          backgroundColor: statusData.map(s => s.type === 'value' ? C.accent : C.orange),
          borderRadius: 5,
          barThickness: 18
        }]
      };
    },
    statusChartOptions() {
      return {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: C.dim, font: { size: 11 } } },
          y: { grid: { display: false }, ticks: { color: C.muted, font: { size: 12 } } }
        }
      };
    }
  }
};
</script>

<style scoped>
.flow-dashboard {
  min-height: 100vh;
  font-family: 'Inter', -apple-system, sans-serif;
  padding: 24px 20px;
}
.flow-inner { max-width: 1100px; margin: 0 auto; }
.flow-meta { font-size: 11px; color: var(--dim, #64748b); letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 6px; }
.flow-title { font-size: 26px; font-weight: 700; margin: 0 0 4px; letter-spacing: -0.03em; }
.flow-desc { color: #64748b; font-size: 13px; margin: 0 0 20px; }
.flow-tabs { display: flex; gap: 4px; margin-bottom: 24px; border-bottom: 1px solid #1e293b; padding-bottom: 1px; }
.tab-btn { border: none; padding: 8px 16px; border-radius: 8px 8px 0 0; cursor: pointer; font-size: 14px; font-weight: 400; transition: all 0.2s; color: #94a3b8; background: transparent; }
.tab-btn.active { font-weight: 600; }
.metrics-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }
.metric-card { background: #111827; border: 1px solid; border-radius: 12px; padding: 18px 22px; position: relative; overflow: hidden; }
.metric-label { font-size: 12px; color: #64748b; margin-bottom: 4px; letter-spacing: 0.06em; text-transform: uppercase; }
.metric-value { font-size: 32px; font-weight: 700; font-family: 'JetBrains Mono', monospace; line-height: 1.1; }
.metric-sub { font-size: 12px; color: #64748b; margin-top: 5px; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.section-card { background: #111827; border: 1px solid; border-radius: 12px; padding: 20px; }
.section-title { font-size: 16px; font-weight: 600; margin: 0 0 4px; }
.section-sub { font-size: 12px; color: #64748b; margin: 0 0 14px; }
.chart-wrap { height: 220px; }
.chart-hist { height: 220px; }
.chart-all { height: 1450px; }
.chart-status { height: 340px; }
.chart-note { font-size: 12px; color: #64748b; margin-top: 6px; }
.cat-bars { display: flex; flex-direction: column; gap: 8px; }
.cat-row { display: flex; align-items: center; gap: 10px; }
.cat-name { width: 130px; font-size: 12px; color: #94a3b8; flex-shrink: 0; }
.cat-bar-bg { flex: 1; height: 22px; background: rgba(255,255,255,0.03); border-radius: 3px; overflow: hidden; }
.cat-bar-fill { height: 100%; border-radius: 3px; opacity: 0.75; }
.cat-val { width: 42px; text-align: right; font-size: 13px; font-family: 'JetBrains Mono', monospace; font-weight: 600; }
.cat-count { width: 28px; text-align: right; font-size: 11px; color: #64748b; }
.top5-list { display: flex; flex-direction: column; gap: 16px; }
.top5-card { }
.top5-head { display: flex; gap: 16px; align-items: flex-start; }
.top5-num { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 700; flex-shrink: 0; }
.top5-body { flex: 1; }
.top5-name { font-size: 15px; font-weight: 600; line-height: 1.4; margin-bottom: 8px; }
.top5-stats { display: flex; gap: 20px; margin-bottom: 8px; }
.stat-label { font-size: 12px; color: #64748b; display: block; }
.stat-val { font-size: 20px; font-weight: 700; font-family: 'JetBrains Mono', monospace; margin-top: 2px; }
.cat-tag { font-size: 12px; padding: 3px 8px; border-radius: 4px; color: #fff; }
.top5-why { font-size: 13px; color: #94a3b8; line-height: 1.5; margin: 0; }
.legend-row { display: flex; gap: 14px; flex-wrap: wrap; margin-top: 12px; }
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 11px; color: #94a3b8; }
.legend-dot { width: 10px; height: 10px; border-radius: 2px; }
.value-wait-bar { display: flex; height: 36px; border-radius: 6px; overflow: hidden; margin-bottom: 14px; }
.vw-work, .vw-wait { display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600; color: #fff; }
.vw-desc { font-size: 13px; color: #94a3b8; line-height: 1.6; margin: 0; }
.bottleneck-list { display: flex; flex-direction: column; gap: 12px; }
.bn-item { display: flex; gap: 10px; align-items: flex-start; }
.bn-num { width: 24px; height: 24px; border-radius: 5px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; }
.bn-name { font-size: 13px; font-weight: 600; }
.bn-days { color: #64748b; font-weight: 400; }
.bn-type { font-size: 10px; margin-left: 6px; padding: 1px 5px; border-radius: 3px; }
.bn-desc { font-size: 12px; color: #94a3b8; margin-top: 2px; }
.flow-footer { margin-top: 28px; padding-top: 14px; border-top: 1px solid; display: flex; justify-content: space-between; font-size: 11px; color: #64748b; flex-wrap: wrap; gap: 8px; }
@media (max-width: 900px) {
  .metrics-row { grid-template-columns: repeat(2, 1fr); }
  .grid-2 { grid-template-columns: 1fr; }
}
</style>
