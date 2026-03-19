import { createApp } from 'vue';
import './styles/new-tool-shell-skin.css';
import './styles/revolut-refresh.css';
import App from './App.vue';
import router from './router';
import { createPinia } from "pinia";
import i18n from './i18n';

const app = createApp(App);
app.use(router);
app.use(createPinia()); // Подключаем Pinia
app.use(i18n);

app.mount('#app');
