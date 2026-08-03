import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { ElAlert, ElButton, ElCard, ElCol, ElContainer, ElAside, ElDescriptions, ElDescriptionsItem, ElDrawer, ElForm, ElFormItem, ElInput, ElLink, ElMain, ElMenu, ElMenuItem, ElOption, ElSelect, ElRow, ElSkeleton, ElTable, ElTableColumn, ElTag, ElMessage } from 'element-plus'
import 'element-plus/dist/index.css'
import './styles.css'
import App from './App.vue'

const app = createApp(App)
app.use(createPinia())
for (const component of [ElAlert, ElButton, ElCard, ElCol, ElContainer, ElAside, ElDescriptions, ElDescriptionsItem, ElDrawer, ElForm, ElFormItem, ElInput, ElLink, ElMain, ElMenu, ElMenuItem, ElOption, ElSelect, ElRow, ElSkeleton, ElTable, ElTableColumn, ElTag]) app.component(component.name, component)
app.config.globalProperties.$message = ElMessage
app.mount('#app')
