import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import Vue from 'vue'
import App from './App.vue'
import VueSocketIO from 'vue-socket.io'
import SocketIO from 'socket.io-client'


const app = createApp(App);
app.use(router);
app.mount('#app');

Vue.use(new VueSocketIO({
  debug: true,
  connection: SocketIO(),
}))

new Vue({
  render: h => h(App),
}).$mount('#app')