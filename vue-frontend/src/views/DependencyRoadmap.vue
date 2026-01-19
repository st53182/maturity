<template>
  <div class="roadmap-container">
    <div class="roadmap-header">
      <h1>{{ roadmapName || 'Дорожная карта зависимостей' }}</h1>
      <div class="header-actions">
        <button @click="showShareModal = true" class="share-btn">🔗 Поделиться</button>
        <button @click="showItemModal = true" class="add-btn">➕ Добавить элемент</button>
        <button @click="showImageUpload = true" class="upload-btn">📷 Загрузить изображение</button>
      </div>
    </div>

    <div class="roadmap-toolbar">
      <div class="toolbar-group">
        <label>Фильтр:</label>
        <select v-model="selectedFilterItem" @change="applyFilter">
          <option value="">Все элементы</option>
          <option v-for="item in items" :key="item.id" :value="item.id">
            {{ item.title }}
          </option>
        </select>
      </div>
      <button @click="clearFilter" v-if="selectedFilterItem" class="clear-filter-btn">Очистить фильтр</button>
    </div>

    <div class="roadmap-canvas-wrapper">
      <div id="roadmap-graph-container" ref="graphContainer"></div>
    </div>

    <!-- Модальное окно создания/редактирования элемента -->
    <div v-if="showItemModal" class="modal-overlay" @click.self="closeItemModal">
      <div class="modal-content">
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
          <button @click="saveItem" class="save-btn">💾 Сохранить</button>
          <button @click="closeItemModal" class="cancel-btn">Отмена</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно настройки доступа -->
    <div v-if="showShareModal" class="modal-overlay" @click.self="showShareModal = false">
      <div class="modal-content">
        <h2>Поделиться дорожной картой</h2>
        <div class="modern-form">
          <div class="input-wrapper">
            <span class="input-icon">🔒</span>
            <input v-model="sharePassword" type="password" class="modern-input" :class="{ 'has-value': sharePassword }" placeholder="Оставьте пустым для доступа без пароля" />
            <label class="floating-label">Пароль (опционально)</label>
          </div>
        </div>
        <div v-if="shareLink" class="share-link">
          <p>Ссылка для доступа:</p>
          <input :value="shareLink" readonly class="link-input" />
          <button @click="copyLink" class="copy-btn">📋 Копировать</button>
        </div>
        <div class="modal-actions">
          <button @click="createShareLink" class="save-btn">🔗 Создать ссылку</button>
          <button @click="showShareModal = false" class="cancel-btn">Закрыть</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно загрузки изображения -->
    <div v-if="showImageUpload" class="modal-overlay" @click.self="showImageUpload = false">
      <div class="modal-content">
        <h2>Загрузить изображение</h2>
        <p>Загрузите изображение дорожной карты или бэклога. AI автоматически распознает эпики и истории.</p>
        <input type="file" @change="handleImageUpload" accept="image/*" class="file-input" />
        <div v-if="uploading" class="upload-status">Обработка изображения...</div>
        <div class="modal-actions">
          <button @click="showImageUpload = false" class="cancel-btn">Закрыть</button>
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
      savePositionTimeout: null
    };
  },
    async mounted() {
    // Получаем ID из роута
    this.roadmapId = this.$route.params.id ? parseInt(this.$route.params.id) : null;
    const accessToken = this.$route.params.token;

    if (accessToken) {
      // Доступ по ссылке
      await this.loadRoadmapByToken(accessToken);
    } else if (this.roadmapId) {
      // Обычный доступ
      await this.loadRoadmap();
    }

    // Загружаем команды (только если авторизован)
    const token = localStorage.getItem("token");
    if (token) {
      await this.loadTeams();
    }

    // Инициализируем граф после загрузки данных
    this.$nextTick(() => {
      this.initGraph();
    });

    // Подключаемся к WebSocket
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
        } else {
          const { data } = await axios.post(`/api/roadmap/shared/${accessToken}/access`, {});
          this.roadmapId = data.id;
          this.roadmapName = data.name;
          this.items = data.items || [];
          this.dependencies = data.dependencies || [];
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
      this.graph.setConnectable(true);
      this.graph.setMultigraph(false);
      this.graph.setAllowDanglingEdges(false);

      // Настраиваем стили
      const style = this.graph.getStylesheet().getDefaultVertexStyle();
      style[mxConstants.STYLE_SHAPE] = mxConstants.SHAPE_RECTANGLE;
      style[mxConstants.STYLE_ROUNDED] = true;
      style[mxConstants.STYLE_FILLCOLOR] = '#E3F2FD';
      style[mxConstants.STYLE_STROKECOLOR] = '#1976D2';
      style[mxConstants.STYLE_FONTCOLOR] = '#000000';

      // Обработчики событий
      this.graph.addListener(mxEvent.CELL_CONNECTED, (sender, evt) => {
        const source = evt.getProperty('source');
        const target = evt.getProperty('target');
        
        if (source && target && source.id && target.id) {
          this.createDependency(parseInt(source.id), parseInt(target.id));
        }
      });

      this.graph.addListener(mxEvent.CELL_MOVED, (sender, evt) => {
        const cell = evt.getProperty('cell');
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

        // Создаем вершины для элементов
        const vertexMap = {};
        this.items.forEach(item => {
          const style = item.type === 'epic' 
            ? 'fillColor=#FFE0B2;strokeColor=#F57C00;rounded=1;' 
            : 'fillColor=#E3F2FD;strokeColor=#1976D2;rounded=1;';
          
          const vertex = this.graph.insertVertex(
            this.graph.getDefaultParent(),
            String(item.id),
            `${item.type === 'epic' ? '📦' : '📋'} ${item.title}`,
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
              this.graph.getDefaultParent(),
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
    async createDependency(fromItemId, toItemId) {
      // Показываем диалог выбора типа зависимости
      const types = ['blocks', 'depends_on', 'related_to', 'requires', 'precedes', 'follows'];
      const typeLabels = {
        'blocks': 'Блокирует',
        'depends_on': 'Зависит от',
        'related_to': 'Связан с',
        'requires': 'Требует',
        'precedes': 'Предшествует',
        'follows': 'Следует за'
      };
      
      const selectedType = prompt(`Выберите тип зависимости:\n${types.map((t, i) => `${i + 1}. ${typeLabels[t]}`).join('\n')}\nВведите номер (1-6):`);
      
      if (!selectedType) return;
      
      const typeIndex = parseInt(selectedType) - 1;
      if (typeIndex < 0 || typeIndex >= types.length) return;
      
      try {
        const token = localStorage.getItem("token");
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        
        await axios.post(`/api/roadmap/${this.roadmapId}/dependency`, {
          from_item_id: fromItemId,
          to_item_id: toItemId,
          dependency_type: types[typeIndex]
        }, { headers });

        await this.loadRoadmap();
      } catch (error) {
        console.error("Ошибка создания зависимости:", error);
        alert("Ошибка создания зависимости. Убедитесь, что у вас есть права на редактирование.");
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
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.roadmap-header {
  padding: 20px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.roadmap-header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.share-btn, .add-btn, .upload-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.share-btn {
  background: #4CAF50;
  color: white;
}

.add-btn {
  background: #2196F3;
  color: white;
}

.upload-btn {
  background: #FF9800;
  color: white;
}

.roadmap-toolbar {
  padding: 12px 20px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  gap: 16px;
  align-items: center;
}

.toolbar-group {
  display: flex;
  gap: 8px;
  align-items: center;
}

.roadmap-canvas-wrapper {
  flex: 1;
  overflow: hidden;
  position: relative;
}

#roadmap-graph-container {
  width: 100%;
  height: 100%;
  background: #fafafa;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 32px;
  border-radius: 12px;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.save-btn, .cancel-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.save-btn {
  background: #4CAF50;
  color: white;
}

.cancel-btn {
  background: #f5f5f5;
  color: #333;
}

.share-link {
  margin-top: 20px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
}

.link-input {
  width: 100%;
  padding: 8px;
  margin-top: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.copy-btn {
  margin-top: 8px;
  padding: 8px 16px;
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.file-input {
  margin-top: 16px;
  padding: 8px;
  width: 100%;
}

.upload-status {
  margin-top: 16px;
  padding: 12px;
  background: #E3F2FD;
  border-radius: 8px;
  text-align: center;
}

/* Modern form styles (из предыдущих компонентов) */
.modern-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  z-index: 2;
  pointer-events: none;
}

.textarea-wrapper .input-icon {
  top: 24px;
  transform: none;
}

.modern-input {
  width: 100%;
  padding: 20px 18px 8px 52px;
  border: 2px solid #e5e7eb;
  border-radius: 14px;
  font-size: 15px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: linear-gradient(to bottom, #ffffff 0%, #fafbfc 100%);
  box-sizing: border-box;
  color: #111827;
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
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 14 14'%3E%3Cpath fill='%236b7280' d='M7 10L2 5h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 18px center;
}

.floating-label {
  position: absolute;
  left: 52px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 15px;
  color: #9ca3af;
  font-weight: 500;
  pointer-events: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
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
  border-color: #3b82f6;
  background: linear-gradient(to bottom, #ffffff 0%, #f0f7ff 100%);
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1), 0 4px 12px rgba(59, 130, 246, 0.15);
}

.modern-input:focus + .floating-label,
.modern-input.has-value + .floating-label {
  top: 12px;
  left: 52px;
  font-size: 12px;
  color: #3b82f6;
  font-weight: 600;
  transform: none;
}
</style>
