import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import ElementPlus from 'element-plus' // 引入库
import 'element-plus/dist/index.css' // 引入样式

const app = createApp(App)
app.use(ElementPlus) // 使用库
app.mount('#app')