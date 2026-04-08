import { createApp } from 'vue';
import './styles/new-tool-shell-skin.css';
import './styles/revolut-refresh.css';
import App from './App.vue';
import router from './router';
import { createPinia } from "pinia";
import i18n from './i18n';
import { setupAxiosInterceptors } from './api/setupAxiosAuth';

const app = createApp(App);
const pinia = createPinia();
app.use(pinia);
app.use(router);
app.use(i18n);
setupAxiosInterceptors(router);

app.mount('#app');
