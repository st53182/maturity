<template>
  <div class="roadmap-container">
    <header class="roadmap-top">
      <div class="roadmap-top__lead">
        <router-link v-if="!isSharedView" to="/roadmap" class="roadmap-back">Все карты</router-link>
        <div class="roadmap-title-block">
          <h1 class="roadmap-title">{{ roadmapName || 'Дорожная карта' }}</h1>
          <p class="roadmap-subtitle">
            <span v-if="isSharedView">Просмотр по ссылке</span>
            <span v-else>
              {{ items.length }} {{ itemsLabel }} · {{ dependencies.length }} {{ depsLabel }}
            </span>
          </p>
        </div>
      </div>
      <div v-if="!isSharedView" class="roadmap-actions" role="toolbar" aria-label="Действия с картой">
        <button type="button" class="rm-btn rm-btn--primary" @click="openNewItemModal">Добавить элемент</button>
        <button type="button" class="rm-btn rm-btn--secondary" @click="showShareModal = true">Поделиться</button>
        <button type="button" class="rm-btn rm-btn--secondary" @click="showSettingsModal = true">Сетка кварталов</button>
        <button type="button" class="rm-btn rm-btn--quiet" @click="showImageUpload = true">Импорт по фото</button>
      </div>
    </header>

    <div class="roadmap-toolbar">
      <div class="toolbar-inner">
        <div class="toolbar-group">
          <label class="toolbar-label" for="roadmap-filter">Фокус на элементе</label>
          <select id="roadmap-filter" v-model="selectedFilterItem" class="toolbar-select" @change="applyFilter">
            <option :value="null">Все элементы</option>
            <option v-for="item in items" :key="item.id" :value="item.id">
              {{ item.title }}
            </option>
          </select>
        </div>
        <button
          v-if="selectedFilterItem"
          type="button"
          class="rm-btn rm-btn--quiet rm-btn--sm"
          @click="clearFilter"
        >
          Сбросить
        </button>
      </div>
      <p class="toolbar-hint">
        Перетаскивайте карточки. Чтобы задать зависимость, потяните соединитель от одной фигуры к другой и выберите тип связи.
      </p>
    </div>

    <div class="roadmap-canvas-wrapper">
      <div id="roadmap-graph-container" ref="graphContainer" class="roadmap-graph-host"></div>
    </div>

    <!-- Выбор типа зависимости (вместо prompt) -->
    <div v-if="showDependencyTypeModal" class="modal-overlay" @click.self="cancelDependencyType">
      <div class="modal-content modal-content--deps">
        <button type="button" class="modal-close-top" @click="cancelDependencyType" aria-label="Закрыть">✕</button>
        <h2>Тип зависимости</h2>
        <p class="modal-lead">
          От <strong>{{ pendingLabelFrom }}</strong> к <strong>{{ pendingLabelTo }}</strong>
        </p>
        <ul class="dep-type-list">
          <li v-for="opt in dependencyTypeOptions" :key="opt.value">
            <button type="button" class="dep-type-btn" @click="confirmDependencyType(opt.value)">
              {{ opt.label }}
            </button>
          </li>
        </ul>
        <div class="modal-actions modal-actions--start">
          <button type="button" class="rm-btn rm-btn--quiet" @click="cancelDependencyType">Отмена</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно создания/редактирования элемента -->
    <div v-if="showItemModal" class="modal-overlay" @click.self="closeItemModal">
      <div class="modal-content">
        <button class="modal-close-top" @click="closeItemModal" aria-label="Close">✕</button>
        <h2>{{ editingItem ? 'Редактировать элемент' : 'Создать элемент' }}</h2>
        <div class="modern-form">
          <div class="input-wrapper">
            <span class="input-icon">📋</span>
            <select v-model="itemForm.type" class="modern-input modern-select" :class="{ 'has-value': itemForm.type }">
              <option value=""></option>
              <option value="epic">Эпик</option>
              <option value="story">История</option>
            </select>
            <label class="floating-label">Тип</label>
          </div>

          <div class="input-wrapper">
            <span class="input-icon">📝</span>
            <input v-model="itemForm.title" class="modern-input" :class="{ 'has-value': itemForm.title }" />
            <label class="floating-label">Название</label>
          </div>

          <div class="input-wrapper textarea-wrapper">
            <span class="input-icon">📄</span>
            <textarea v-model="itemForm.description" class="modern-input modern-textarea" :class="{ 'has-value': itemForm.description }"></textarea>
            <label class="floating-label">Описание</label>
          </div>

          <div class="input-wrapper">
            <span class="input-icon">🏢</span>
            <select v-model="itemForm.team_id" class="modern-input modern-select" :class="{ 'has-value': itemForm.team_id }">
              <option value=""></option>
              <option v-for="team in teams" :key="team.id" :value="team.id">{{ team.name }}</option>
            </select>
            <label class="floating-label">Команда</label>
          </div>
        </div>

        <div class="modal-actions">
          <button type="button" class="rm-btn rm-btn--primary" @click="saveItem">Сохранить</button>
          <button type="button" class="rm-btn rm-btn--quiet" @click="closeItemModal">Отмена</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно настройки доступа -->
    <div v-if="showShareModal" class="modal-overlay" @click.self="showShareModal = false">
      <div class="modal-content">
        <button class="modal-close-top" @click="showShareModal = false" aria-label="Close">✕</button>
        <h2>Поделиться дорожной картой</h2>
        <div class="modern-form">
          <div class="input-wrapper">
            <span class="input-icon">🔒</span>
            <input v-model="sharePassword" type="password" class="modern-input" :class="{ 'has-value': sharePassword }" placeholder="Оставьте пустым для доступа без пароля" />
            <label class="floating-label">Пароль (опционально)</label>
          </div>
        </div>
        <div v-if="shareLink" class="share-link">
          <p class="share-link__title">Ссылка для доступа</p>
          <input :value="shareLink" readonly class="link-input" />
          <button type="button" class="rm-btn rm-btn--secondary rm-btn--sm" @click="copyLink">Копировать</button>
        </div>
        <div class="modal-actions">
          <button type="button" class="rm-btn rm-btn--primary" @click="createShareLink">Создать ссылку</button>
          <button type="button" class="rm-btn rm-btn--quiet" @click="showShareModal = false">Закрыть</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно загрузки изображения -->
    <div v-if="showImageUpload" class="modal-overlay" @click.self="showImageUpload = false">
      <div class="modal-content">
        <button class="modal-close-top" @click="showImageUpload = false" aria-label="Close">✕</button>
        <h2>Загрузить изображение</h2>
        <p>Загрузите изображение дорожной карты или бэклога. AI автоматически распознает эпики и истории.</p>
        <input type="file" @change="handleImageUpload" accept="image/*" class="file-input" />
        <div v-if="uploading" class="upload-status">Обработка изображения...</div>
        <div class="modal-actions">
          <button @click="showImageUpload = false" class="cancel-btn">Закрыть</button>
        </div>
      </div>
    </div>

    <!-- Сетка кварталов на холсте -->
    <div v-if="showSettingsModal" class="modal-overlay" @click.self="showSettingsModal = false">
      <div class="modal-content">
        <button type="button" class="modal-close-top" @click="showSettingsModal = false" aria-label="Закрыть">✕</button>
        <h2>Сетка кварталов</h2>
        <p class="modal-lead muted">
          На доске появятся четыре квартала подряд, начиная с указанного, и колонки спринтов внутри каждого.
        </p>
        <div class="settings-fields">
          <div class="settings-field">
            <label for="rm-quarter-start">Начало (формат год-Q)</label>
            <input id="rm-quarter-start" v-model="quarterStart" type="text" class="settings-input" placeholder="2024-Q1" autocomplete="off" />
          </div>
          <div class="settings-field">
            <label for="rm-sprints">Спринтов в квартале</label>
            <input id="rm-sprints" v-model.number="sprintsPerQuarter" type="number" min="1" max="12" class="settings-input" />
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="rm-btn rm-btn--primary" @click="saveSettings">Сохранить</button>
          <button type="button" class="rm-btn rm-btn--quiet" @click="showSettingsModal = false">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { io } from "socket.io-client";

export default {
  name: "DependencyRoadmap",
  data() {
    return {
      roadmapId: null,
      roadmapName: "",
      items: [],
      dependencies: [],
      teams: [],
      graph: null,
      graphContainer: null,
      selectedFilterItem: null,
      showItemModal: false,
      showShareModal: false,
      showImageUpload: false,
      showSettingsModal: false,
      editingItem: null,
      itemForm: {
        type: "",
        title: "",
        description: "",
        team_id: null
      },
      sharePassword: "",
      shareLink: "",
      socket: null,
      uploading: false,
      savePositionTimeout: null,
      quarterStart: "",
      sprintsPerQuarter: 6,
      showDependencyTypeModal: false,
      pendingConnection: null,
      dependencyTypeOptions: [
        { value: "blocks", label: "Блокирует" },
        { value: "depends_on", label: "Зависит от" },
        { value: "related_to", label: "Связан с" },
        { value: "requires", label: "Требует" },
        { value: "precedes", label: "Предшествует" },
        { value: "follows", label: "Следует за" }
      ]
    };
  },
  computed: {
    isSharedView() {
      return Boolean(this.$route.params.token);
    },
    itemsLabel() {
      return this.pluralRu(this.items.length, ["элемент", "элемента", "элементов"]);
    },
    depsLabel() {
      return this.pluralRu(this.dependencies.length, ["связь", "связи", "связей"]);
    },
    pendingLabelFrom() {
      const id = this.pendingConnection?.fromId;
      const item = this.items.find((i) => i.id === id);
      return item?.title || "…";
    },
    pendingLabelTo() {
      const id = this.pendingConnection?.toId;
      const item = this.items.find((i) => i.id === id);
      return item?.title || "…";
    }
  },
  async mounted() {
    this.roadmapId = this.$route.params.id ? parseInt(this.$route.params.id, 10) : null;
    const accessToken = this.$route.params.token;

    if (accessToken) {
      await this.loadRoadmapByToken(accessToken);
    } else if (this.roadmapId) {
      await this.loadRoadmap();
    }

    const token = localStorage.getItem("token");
    if (token) {
      await this.loadTeams();
    }

    this.$nextTick(() => {
      this.initGraph();
    });

    if (this.roadmapId) {
      this.connectWebSocket();
    }
  },
  beforeUnmount() {
    if (this.savePositionTimeout) {
      clearTimeout(this.savePositionTimeout);
    }
    if (this.socket) {
      this.socket.disconnect();
    }
  },
  methods: {
    async loadRoadmap() {
      try {
        const token = localStorage.getItem("token");
        const { data } = await axios.get(`/api/roadmap/${this.roadmapId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        this.roadmapName = data.name;
        this.items = data.items || [];
        this.dependencies = data.dependencies || [];
        this.quarterStart = data.quarter_start || "";
        this.sprintsPerQuarter = data.sprints_per_quarter || 6;
        this.renderGraph();
      } catch (error) {
        console.error("Ошибка загрузки карты:", error);
        alert("Ошибка загрузки дорожной карты");
      }
    },
    async loadRoadmapByToken(accessToken) {
      try {
        // Сначала проверяем, нужен ли пароль
        const { data: roadmapInfo } = await axios.get(`/api/roadmap/shared/${accessToken}`);
        
        if (roadmapInfo.has_password) {
          const password = prompt("Введите пароль для доступа к дорожной карте:");
          if (!password) {
            this.$router.push("/");
            return;
          }
          
          const { data } = await axios.post(`/api/roadmap/shared/${accessToken}/access`, {
            password
          });
          this.roadmapId = data.id;
          this.roadmapName = data.name;
          this.items = data.items || [];
          this.dependencies = data.dependencies || [];
          this.quarterStart = data.quarter_start || "";
          this.sprintsPerQuarter = data.sprints_per_quarter || 6;
        } else {
          const { data } = await axios.post(`/api/roadmap/shared/${accessToken}/access`, {});
          this.roadmapId = data.id;
          this.roadmapName = data.name;
          this.items = data.items || [];
          this.dependencies = data.dependencies || [];
          this.quarterStart = data.quarter_start || "";
          this.sprintsPerQuarter = data.sprints_per_quarter || 6;
        }
        
        this.renderGraph();
      } catch (error) {
        console.error("Ошибка загрузки карты:", error);
        alert("Ошибка доступа к дорожной карте");
        this.$router.push("/");
      }
    },
    async loadTeams() {
      try {
        const token = localStorage.getItem("token");
        const { data } = await axios.get("/user_teams", {
          headers: { Authorization: `Bearer ${token}` }
        });
        this.teams = data || [];
      } catch (error) {
        console.error("Ошибка загрузки команд:", error);
      }
    },
    async initGraph() {
      // Загружаем mxGraph динамически
      try {
        // Используем CDN для mxGraph
        if (typeof window.mxGraph === 'undefined') {
          await this.loadMxGraph();
        }
        this.setupGraph();
      } catch (error) {
        console.error("Ошибка загрузки mxGraph:", error);
        alert("Ошибка загрузки библиотеки визуализации");
      }
    },
    loadMxGraph() {
      return new Promise((resolve, reject) => {
        if (typeof window.mxGraph !== 'undefined') {
          resolve();
          return;
        }
        
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/mxgraph@4.2.2/javascript/mxClient.min.js';
        script.onload = () => {
          // Ждем, пока mxGraph станет доступен
          const checkInterval = setInterval(() => {
            if (typeof window.mxGraph !== 'undefined') {
              clearInterval(checkInterval);
              resolve();
            }
          }, 100);
          
          setTimeout(() => {
            clearInterval(checkInterval);
            if (typeof window.mxGraph === 'undefined') {
              reject(new Error('mxGraph не загрузился'));
            }
          }, 5000);
        };
        script.onerror = () => reject(new Error('Ошибка загрузки mxGraph'));
        document.head.appendChild(script);
      });
    },
    setupGraph() {
      // Настройка mxGraph
      this.graphContainer = this.$refs.graphContainer;
      if (!this.graphContainer || typeof window.mxGraph === 'undefined') {
        return;
      }

      const { mxGraph, mxConstants, mxEvent } = window;

      // Создаем граф
      this.graph = new mxGraph(this.graphContainer);
      const readOnly = Boolean(this.$route.params.token);
      this.graph.setConnectable(!readOnly);
      this.graph.setMultigraph(false);
      this.graph.setAllowDanglingEdges(false);
      if (readOnly) {
        this.graph.setCellsMovable(false);
        this.graph.setCellsResizable(false);
        this.graph.setCellsBendable(false);
      }

      // Настраиваем стили
      const style = this.graph.getStylesheet().getDefaultVertexStyle();
      style[mxConstants.STYLE_SHAPE] = mxConstants.SHAPE_RECTANGLE;
      style[mxConstants.STYLE_ROUNDED] = true;
      style[mxConstants.STYLE_FILLCOLOR] = '#E3F2FD';
      style[mxConstants.STYLE_STROKECOLOR] = '#1976D2';
      style[mxConstants.STYLE_FONTCOLOR] = '#000000';

      // Обработчики событий
      this.graph.addListener(mxEvent.CELL_CONNECTED, (sender, evt) => {
        const edge = evt.getProperty("edge");
        const source = evt.getProperty("source");
        const target = evt.getProperty("target");

        if (!edge || !source || !target || source.id == null || target.id == null) return;
        const fromId = parseInt(source.id, 10);
        const toId = parseInt(target.id, 10);
        if (Number.isNaN(fromId) || Number.isNaN(toId)) return;

        const existingDep = this.dependencies.find(
          (d) => d.from_item_id === fromId && d.to_item_id === toId
        );
        if (existingDep) return;

        this.pendingConnection = { edge, fromId, toId };
        this.showDependencyTypeModal = true;
      });

      this.graph.addListener(mxEvent.CELL_MOVED, (sender, evt) => {
        const cell = evt.getProperty('cell');
        if (!cell) return;
        
        const geometry = cell.getGeometry();
        if (geometry && cell.vertex && cell.id) {
          this.updateItemPosition(parseInt(cell.id), geometry.x, geometry.y);
        }
      });

      // Рендерим граф после настройки
      if (this.items.length > 0) {
        this.$nextTick(() => {
          this.renderGraph();
        });
      }
    },
    renderGraph() {
      if (!this.graph || !this.graphContainer || typeof window.mxGraph === 'undefined') return;

      const model = this.graph.getModel();
      model.beginUpdate();
      try {
        // Очищаем граф
        const cells = this.graph.getChildCells();
        if (cells && cells.length > 0) {
          this.graph.removeCells(cells);
        }

      const parent = this.graph.getDefaultParent();

        // Рисуем кварталы и спринты, если настроены
        if (this.quarterStart && this.sprintsPerQuarter > 0) {
          this.renderQuartersAndSprints(parent);
        }

        // Создаем вершины для элементов
        const vertexMap = {};
        this.items.forEach(item => {
          const style = item.type === 'epic' 
            ? 'fillColor=#FFF4E6;strokeColor=#C2410C;rounded=1;fontColor=#0d1733;' 
            : 'fillColor=#EEF4FF;strokeColor=#2754c7;rounded=1;fontColor=#0d1733;';
          const prefix = item.type === 'epic' ? 'Эпик' : 'История';
          const vertex = this.graph.insertVertex(
            parent,
            String(item.id),
            `${prefix}: ${item.title}`,
            item.position_x || 100,
            item.position_y || 100,
            200,
            80,
            style
          );
          vertexMap[item.id] = vertex;
        });

        // Создаем ребра для зависимостей
        this.dependencies.forEach(dep => {
          const source = vertexMap[dep.from_item_id];
          const target = vertexMap[dep.to_item_id];
          if (source && target) {
            this.graph.insertEdge(
              parent,
              String(dep.id),
              this.getDependencyLabel(dep.dependency_type),
              source,
              target,
              'strokeColor=#424242;endArrow=classic;'
            );
          }
        });
      } finally {
        model.endUpdate();
      }
    },
    renderQuartersAndSprints(parent) {
      if (!this.quarterStart || !this.sprintsPerQuarter) return;

      const quarterWidth = 800;
      const sprintWidth = quarterWidth / this.sprintsPerQuarter;
      const rowHeight = 150;
      const startY = 50;
      const startX = 50;

      // Парсим квартал (формат: "2024-Q1")
      const match = this.quarterStart.match(/(\d{4})-Q(\d)/);
      if (!match) return;

      const year = parseInt(match[1]);
      const startQuarter = parseInt(match[2]);

      // Рисуем 4 квартала
      for (let q = 0; q < 4; q++) {
        const quarterNum = ((startQuarter - 1 + q) % 4) + 1;
        const currentYear = year + Math.floor((startQuarter - 1 + q) / 4);
        const quarterX = startX + q * (quarterWidth + 50);
        
        // Фон квартала
        this.graph.insertVertex(
          parent,
          `quarter-${q}`,
          `Q${quarterNum} ${currentYear}`,
          quarterX,
          startY,
          quarterWidth,
          rowHeight * 2,
          `fillColor=#F5F5F5;strokeColor=#CCCCCC;strokeWidth=2;rounded=1;fontSize=16;fontStyle=1;`
        );

        // Рисуем спринты внутри квартала
        for (let s = 0; s < this.sprintsPerQuarter; s++) {
          const sprintX = quarterX + s * sprintWidth;
          this.graph.insertVertex(
            parent,
            `sprint-${q}-${s}`,
            `Sprint ${s + 1}`,
            sprintX,
            startY + rowHeight,
            sprintWidth - 10,
            rowHeight - 20,
            `fillColor=#FFFFFF;strokeColor=#E0E0E0;strokeWidth=1;rounded=1;fontSize=12;`
          );
        }
      }
    },
    getDependencyLabel(type) {
      const labels = {
        'blocks': 'Блокирует',
        'depends_on': 'Зависит от',
        'related_to': 'Связан с',
        'requires': 'Требует',
        'precedes': 'Предшествует',
        'follows': 'Следует за'
      };
      return labels[type] || type;
    },
    async saveItem() {
      try {
        const token = localStorage.getItem("token");
        if (!token) {
          alert("Требуется авторизация для создания элементов");
          return;
        }
        
        const data = {
          type: this.itemForm.type,
          title: this.itemForm.title,
          description: this.itemForm.description,
          team_id: this.itemForm.team_id || null
        };

        if (this.editingItem) {
          await axios.put(`/api/roadmap/${this.roadmapId}/item/${this.editingItem.id}`, data, {
            headers: { Authorization: `Bearer ${token}` }
          });
        } else {
          const response = await axios.post(`/api/roadmap/${this.roadmapId}/item`, data, {
            headers: { Authorization: `Bearer ${token}` }
          });
          this.items.push(response.data);
        }

        await this.loadRoadmap();
        this.closeItemModal();
      } catch (error) {
        console.error("Ошибка сохранения элемента:", error);
        alert("Ошибка сохранения элемента. Убедитесь, что у вас есть права на редактирование.");
      }
    },
    closeItemModal() {
      this.showItemModal = false;
      this.editingItem = null;
      this.itemForm = { type: "", title: "", description: "", team_id: null };
    },
    async updateItemPosition(itemId, x, y) {
      // Обновляем локально для быстрого отклика
      const item = this.items.find(i => i.id === itemId);
      if (item) {
        item.position_x = x;
        item.position_y = y;
      }

      // Отправляем через WebSocket (broadcast другим пользователям)
      if (this.socket && this.socket.connected) {
        this.socket.emit('item_move', {
          roadmap_id: this.roadmapId,
          item_id: itemId,
          position_x: x,
          position_y: y
        });
      }

      // Сохраняем в БД (debounce для уменьшения нагрузки)
      if (this.savePositionTimeout) {
        clearTimeout(this.savePositionTimeout);
      }
      
      this.savePositionTimeout = setTimeout(async () => {
        try {
          const token = localStorage.getItem("token");
          if (token) {
            await axios.put(`/api/roadmap/${this.roadmapId}/item/${itemId}`, {
              position_x: x,
              position_y: y
            }, {
              headers: { Authorization: `Bearer ${token}` }
            });
          }
        } catch (error) {
          console.error("Ошибка сохранения позиции:", error);
        }
      }, 500);
    },
    pluralRu(n, forms) {
      const nAbs = Math.abs(n) % 100;
      const n1 = nAbs % 10;
      if (nAbs > 10 && nAbs < 20) return forms[2];
      if (n1 > 1 && n1 < 5) return forms[1];
      if (n1 === 1) return forms[0];
      return forms[2];
    },
    openNewItemModal() {
      this.showItemModal = true;
    },
    cancelDependencyType() {
      if (this.pendingConnection?.edge && this.graph) {
        try {
          this.graph.removeCells([this.pendingConnection.edge]);
        } catch (e) {
          console.warn("Не удалось убрать ребро графа", e);
        }
      }
      this.pendingConnection = null;
      this.showDependencyTypeModal = false;
    },
    async confirmDependencyType(dependencyType) {
      if (!this.pendingConnection) return;
      const { edge, fromId, toId } = this.pendingConnection;
      this.pendingConnection = null;
      this.showDependencyTypeModal = false;
      try {
        await this.createDependency(fromId, toId, dependencyType);
      } catch (err) {
        console.error("Ошибка создания зависимости:", err);
        alert("Не удалось создать зависимость. Проверьте права доступа.");
        if (edge && this.graph) {
          try {
            this.graph.removeCells([edge]);
          } catch (e) {
            console.warn(e);
          }
        }
      }
    },
    async createDependency(fromItemId, toItemId, dependencyType) {
      const token = localStorage.getItem("token");
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      await axios.post(
        `/api/roadmap/${this.roadmapId}/dependency`,
        {
          from_item_id: fromItemId,
          to_item_id: toItemId,
          dependency_type: dependencyType
        },
        { headers }
      );

      await this.loadRoadmap();
    },
    async saveSettings() {
      try {
        const token = localStorage.getItem("token");
        if (!token) {
          alert("Требуется авторизация");
          return;
        }
        
        await axios.put(`/api/roadmap/${this.roadmapId}`, {
          quarter_start: this.quarterStart,
          sprints_per_quarter: this.sprintsPerQuarter
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        this.showSettingsModal = false;
        this.renderGraph(); // Перерисовываем граф с новыми настройками
      } catch (error) {
        console.error("Ошибка сохранения настроек:", error);
        alert("Ошибка сохранения настроек");
      }
    },
    async createShareLink() {
      try {
        const token = localStorage.getItem("token");
        const { data } = await axios.post(`/api/roadmap/${this.roadmapId}/share`, {
          password: this.sharePassword || null
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        this.shareLink = window.location.origin + data.share_url;
      } catch (error) {
        console.error("Ошибка создания ссылки:", error);
        alert("Ошибка создания ссылки");
      }
    },
    copyLink() {
      navigator.clipboard.writeText(this.shareLink);
      alert("Ссылка скопирована!");
    },
    async handleImageUpload(event) {
      const file = event.target.files[0];
      if (!file) return;

      this.uploading = true;
      try {
        const token = localStorage.getItem("token");
        const formData = new FormData();
        formData.append('image', file);

        const { data } = await axios.post(`/api/roadmap/${this.roadmapId}/upload-image`, formData, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        });

        await this.loadRoadmap();
        alert(`Создано элементов: ${data.items.length}`);
        this.showImageUpload = false;
      } catch (error) {
        console.error("Ошибка загрузки изображения:", error);
        alert("Ошибка обработки изображения");
      } finally {
        this.uploading = false;
      }
    },
    applyFilter() {
      if (!this.selectedFilterItem) {
        this.renderGraph();
        return;
      }

      // Находим все связанные элементы через BFS
      const visited = new Set();
      const queue = [parseInt(this.selectedFilterItem)];
      const relatedItems = new Set([parseInt(this.selectedFilterItem)]);

      while (queue.length > 0) {
        const currentId = queue.shift();
        if (visited.has(currentId)) continue;
        visited.add(currentId);

        // Находим все зависимости, связанные с текущим элементом
        this.dependencies.forEach(dep => {
          if (dep.from_item_id === currentId && !relatedItems.has(dep.to_item_id)) {
            relatedItems.add(dep.to_item_id);
            queue.push(dep.to_item_id);
          }
          if (dep.to_item_id === currentId && !relatedItems.has(dep.from_item_id)) {
            relatedItems.add(dep.from_item_id);
            queue.push(dep.from_item_id);
          }
        });
      }

      // Подсвечиваем связанные элементы
      this.renderGraph();
      // TODO: Добавить визуальное выделение связанных элементов
    },
    clearFilter() {
      this.selectedFilterItem = null;
      this.renderGraph();
    },
    connectWebSocket() {
      const token = localStorage.getItem("token");
      const accessToken = this.$route.params.token;
      
      if (!this.roadmapId) return;
      
      const auth = {
        roadmap_id: this.roadmapId
      };
      
      if (accessToken) {
        auth.access_token = accessToken;
        // Пароль уже был проверен при загрузке карты
      } else if (token) {
        auth.token = token;
      } else {
        return; // Нет способа авторизации
      }

      this.socket = io(window.location.origin, {
        auth,
        transports: ['websocket', 'polling']
      });

      this.socket.on('connect', () => {
        console.log('WebSocket connected');
      });

      this.socket.on('item_create', (data) => {
        this.items.push(data);
        this.renderGraph();
      });

      this.socket.on('item_update', (data) => {
        const index = this.items.findIndex(i => i.id === data.id);
        if (index !== -1) {
          this.items[index] = data;
          this.renderGraph();
        }
      });

      this.socket.on('item_delete', (data) => {
        this.items = this.items.filter(i => i.id !== data.id);
        this.renderGraph();
      });

      this.socket.on('item_move', (data) => {
        const item = this.items.find(i => i.id === data.item_id);
        if (item) {
          item.position_x = data.position_x;
          item.position_y = data.position_y;
          this.renderGraph();
        }
      });

      this.socket.on('dependency_create', (data) => {
        this.dependencies.push(data);
        this.renderGraph();
      });

      this.socket.on('dependency_delete', (data) => {
        this.dependencies = this.dependencies.filter(d => d.id !== data.id);
        this.renderGraph();
      });
    }
  }
};
</script>

<style scoped>
.roadmap-container {
  width: 100%;
  max-width: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: calc(100vh - 5.5rem);
  max-height: calc(100dvh - 4.5rem);
  background: var(--vl-surface-soft, #f6f9ff);
  border-radius: 14px;
  border: 1px solid var(--vl-border, #d8e0f0);
  overflow: hidden;
  box-sizing: border-box;
}

.roadmap-top {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem 1.25rem;
  padding: 1.1rem 1.25rem;
  background: var(--vl-surface, #fff);
  border-bottom: 1px solid var(--vl-border, #d8e0f0);
}

.roadmap-top__lead {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-width: 0;
}

.roadmap-back {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--vl-muted, #5d6b8a);
  text-decoration: none;
  align-self: flex-start;
}

.roadmap-back:hover {
  color: var(--vl-primary-end, #2754c7);
  text-decoration: underline;
}

.roadmap-title {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--vl-text, #0d1733);
  letter-spacing: -0.02em;
  line-height: 1.25;
}

.roadmap-subtitle {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--vl-muted, #5d6b8a);
}

.roadmap-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  justify-content: flex-end;
}

.rm-btn {
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.55rem 1rem;
  line-height: 1.25;
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease, border-color 0.15s ease;
}

.rm-btn--sm {
  padding: 0.4rem 0.75rem;
  font-size: 0.8125rem;
}

.rm-btn--primary {
  color: #fff;
  background: linear-gradient(135deg, var(--vl-primary-start, #142b66), var(--vl-primary-end, #2754c7));
  box-shadow: 0 2px 10px rgba(20, 43, 102, 0.22);
}

.rm-btn--primary:hover {
  background: linear-gradient(135deg, var(--vl-primary-hover-start, #102457), var(--vl-primary-hover-end, #1f46ae));
  box-shadow: 0 4px 14px rgba(20, 43, 102, 0.28);
}

.rm-btn--secondary {
  color: var(--vl-text, #0d1733);
  background: var(--vl-surface, #fff);
  border: 1px solid var(--vl-border, #d8e0f0);
  box-shadow: 0 1px 2px rgba(10, 20, 45, 0.06);
}

.rm-btn--secondary:hover {
  border-color: rgba(39, 84, 199, 0.35);
  background: var(--vl-surface-soft, #f6f9ff);
}

.rm-btn--quiet {
  color: var(--vl-muted, #5d6b8a);
  background: transparent;
  border: 1px solid transparent;
}

.rm-btn--quiet:hover {
  color: var(--vl-text, #0d1733);
  background: rgba(10, 20, 45, 0.06);
  border-color: rgba(10, 20, 45, 0.08);
}

.roadmap-toolbar {
  flex-shrink: 0;
  padding: 0.75rem 1.25rem 0.9rem;
  background: var(--vl-surface, #fff);
  border-bottom: 1px solid var(--vl-border, #d8e0f0);
}

.toolbar-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.75rem 1rem;
}

.toolbar-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-width: 12rem;
  flex: 1 1 200px;
}

.toolbar-label {
  font-size: 0.6875rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--vl-muted, #5d6b8a);
}

.toolbar-select {
  width: 100%;
  max-width: 22rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  color: var(--vl-text, #0d1733);
  border: 1px solid var(--vl-border, #d8e0f0);
  border-radius: 10px;
  background: var(--vl-surface, #fff);
  box-sizing: border-box;
}

.toolbar-select:focus {
  outline: none;
  border-color: rgba(39, 84, 199, 0.45);
  box-shadow: 0 0 0 3px rgba(39, 84, 199, 0.12);
}

.toolbar-hint {
  margin: 0.65rem 0 0;
  font-size: 0.8125rem;
  line-height: 1.45;
  color: var(--vl-muted, #5d6b8a);
}

.roadmap-canvas-wrapper {
  flex: 1;
  min-height: 0;
  position: relative;
  padding: 0.65rem;
  box-sizing: border-box;
}

.roadmap-graph-host {
  width: 100%;
  height: 100%;
  min-height: 360px;
  border-radius: 12px;
  border: 1px solid var(--vl-border, #d8e0f0);
  background-color: #fbfcff;
  background-image: radial-gradient(circle at 1px 1px, rgba(13, 23, 51, 0.07) 1px, transparent 0);
  background-size: 18px 18px;
  overflow: hidden;
  box-sizing: border-box;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(10, 20, 45, 0.45);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
  padding: 1rem;
  box-sizing: border-box;
}

.modal-content {
  background: var(--vl-surface, #fff);
  padding: 1.75rem 1.5rem 1.5rem;
  border-radius: 14px;
  max-width: 600px;
  width: 100%;
  max-height: min(90vh, 720px);
  overflow-y: auto;
  position: relative;
  border: 1px solid var(--vl-border, #d8e0f0);
  box-shadow: 0 24px 70px rgba(10, 20, 45, 0.2);
  box-sizing: border-box;
}

.modal-content h2 {
  margin: 0 0 0.35rem;
  font-size: 1.2rem;
  color: var(--vl-text, #0d1733);
}

.modal-lead {
  margin: 0 0 1rem;
  font-size: 0.875rem;
  line-height: 1.45;
  color: var(--vl-text, #0d1733);
}

.modal-lead.muted,
.muted {
  color: var(--vl-muted, #5d6b8a);
}

.modal-content--deps {
  max-width: 400px;
}

.modal-close-top {
  position: absolute;
  top: 10px;
  right: 10px;
}

.dep-type-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.dep-type-btn {
  width: 100%;
  text-align: left;
  padding: 0.65rem 0.85rem;
  border-radius: 10px;
  border: 1px solid var(--vl-border, #d8e0f0);
  background: var(--vl-surface-soft, #f6f9ff);
  color: var(--vl-text, #0d1733);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.dep-type-btn:hover {
  background: #fff;
  border-color: rgba(39, 84, 199, 0.35);
}

.modal-actions {
  margin-top: 1.25rem;
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.modal-actions--start {
  justify-content: flex-start;
}

.settings-fields {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.settings-field label {
  display: block;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--vl-muted, #5d6b8a);
  margin-bottom: 0.35rem;
}

.settings-input {
  width: 100%;
  padding: 0.6rem 0.75rem;
  font-size: 0.9375rem;
  border: 1px solid var(--vl-border, #d8e0f0);
  border-radius: 10px;
  box-sizing: border-box;
  color: var(--vl-text, #0d1733);
}

.settings-input:focus {
  outline: none;
  border-color: rgba(39, 84, 199, 0.45);
  box-shadow: 0 0 0 3px rgba(39, 84, 199, 0.1);
}

.share-link {
  margin-top: 1.25rem;
  padding: 1rem;
  background: var(--vl-surface-soft, #f6f9ff);
  border-radius: 12px;
  border: 1px solid var(--vl-border, #d8e0f0);
}

.share-link__title {
  margin: 0 0 0.5rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--vl-muted, #5d6b8a);
}

.link-input {
  width: 100%;
  padding: 0.5rem 0.65rem;
  margin-bottom: 0.5rem;
  border: 1px solid var(--vl-border, #d8e0f0);
  border-radius: 8px;
  font-size: 0.8125rem;
  box-sizing: border-box;
  font-family: ui-monospace, monospace;
}

.file-input {
  margin-top: 1rem;
  padding: 0.5rem 0;
  width: 100%;
  font-size: 0.875rem;
}

.upload-status {
  margin-top: 1rem;
  padding: 0.75rem;
  background: var(--vl-surface-soft, #f6f9ff);
  border-radius: 10px;
  text-align: center;
  font-size: 0.875rem;
  color: var(--vl-muted, #5d6b8a);
}

.modern-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 18px;
  z-index: 2;
  pointer-events: none;
  opacity: 0.75;
}

.textarea-wrapper .input-icon {
  top: 24px;
  transform: none;
}

.modern-input {
  width: 100%;
  padding: 20px 18px 8px 52px;
  border: 2px solid var(--vl-border, #d8e0f0);
  border-radius: 12px;
  font-size: 15px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  background: var(--vl-surface, #fff);
  box-sizing: border-box;
  color: var(--vl-text, #0d1733);
  line-height: 1.5;
}

.modern-textarea {
  padding-top: 32px;
  min-height: 100px;
  resize: vertical;
}

.modern-select {
  padding-right: 52px;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 14 14'%3E%3Cpath fill='%235d6b8a' d='M7 10L2 5h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 18px center;
}

.floating-label {
  position: absolute;
  left: 52px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 15px;
  color: var(--vl-muted, #5d6b8a);
  font-weight: 500;
  pointer-events: none;
  transition: all 0.25s ease;
  z-index: 1;
}

.textarea-wrapper .floating-label {
  top: 32px;
  transform: none;
}

.modern-input:focus,
.modern-input.has-value {
  padding-top: 20px;
  padding-bottom: 8px;
  border-color: rgba(39, 84, 199, 0.45);
  box-shadow: 0 0 0 3px rgba(39, 84, 199, 0.1);
}

.modern-input:focus + .floating-label,
.modern-input.has-value + .floating-label {
  top: 12px;
  left: 52px;
  font-size: 12px;
  color: var(--vl-primary-end, #2754c7);
  font-weight: 600;
  transform: none;
}

@media (max-width: 640px) {
  .roadmap-container {
    height: auto;
    max-height: none;
    min-height: 70vh;
  }

  .roadmap-canvas-wrapper {
    min-height: 50vh;
  }
}
</style>
