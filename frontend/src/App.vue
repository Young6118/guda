<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { runTask } from './api.js'
import { useAnalysisStore } from './stores/analysis'
import Chart from './components/Chart.vue'

const store = useAnalysisStore()
const drawer = ref(false)
const reportDrawer = ref(false)
const selected = ref(null)
const wordCloud = computed(() => store.analytics?.word_cloud || [])
const lineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 36, right: 18, top: 30, bottom: 28 },
  xAxis: { type: 'category', data: (store.analytics?.timeline || []).map(x => x.date) },
  yAxis: { type: 'value', minInterval: 1 },
  series: [{ type: 'line', smooth: true, data: (store.analytics?.timeline || []).map(x => x.value), areaStyle: { opacity: .14 }, itemStyle: { color: '#2f6f6d' }, lineStyle: { width: 3 } }],
}))
const platformOption = computed(() => pieOption(store.analytics?.platforms || []))
const typeOption = computed(() => pieOption(store.analytics?.item_types || []))
function pieOption(data) { return { tooltip: { trigger: 'item' }, legend: { bottom: 0, type: 'scroll' }, series: [{ type: 'pie', radius: ['38%', '70%'], data: data.map(x => ({ name: x.name, value: x.value })), label: { formatter: '{b}: {c}' } }] } }
function openReport() { reportDrawer.value = true }
function downloadReport() { const blob = new Blob([store.report?.markdown || ''], { type: 'text/markdown;charset=utf-8' }); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = `${store.report?.title || 'guda-report'}.md`; link.click(); URL.revokeObjectURL(url) }
async function rerunTask(task) { try { task.monitor_status = 'running'; await runTask(task.id); await refresh(); ElMessage.success('任务已运行完成') } catch (error) { ElMessage.error(error?.response?.data?.detail || error.message || '任务运行失败'); await refresh() } }
function openEvidence(row) { selected.value = row; drawer.value = true }
async function refresh() { await store.load(); if (store.error) ElMessage.error(store.error) }
watch(() => store.topicPackId, refresh)
onMounted(refresh)
</script>

<template>
  <el-container class="shell">
    <el-aside width="236px" class="aside">
      <div class="brand"><div class="logo">G</div><div><b>GUDA</b><span>Source Intelligence</span></div></div>
      <el-menu default-active="overview" class="menu">
        <el-menu-item index="overview">分析总览</el-menu-item>
        <el-menu-item index="evidence">证据明细</el-menu-item>
        <el-menu-item index="trends">趋势分析</el-menu-item>
        <el-menu-item index="insights">洞察卡片 <el-tag size="small" type="success">Live</el-tag></el-menu-item>
        <el-menu-item index="reports">报告 <el-tag size="small" type="success">Live</el-tag></el-menu-item>
      </el-menu>
      <a class="admin-link" href="../admin/">进入管理后台 →</a>
    </el-aside>
    <el-main class="main">
      <header class="topbar"><div><div class="eyebrow">DEMAND INTELLIGENCE</div><h1>需求情报总览</h1><p>从真实证据中看见需求、主题与趋势变化</p></div><div class="top-actions"><el-button @click="openReport" :disabled="!store.report">查看报告</el-button><el-button @click="downloadReport" :disabled="!store.report">下载 Markdown</el-button><el-button @click="refresh" :loading="store.loading">刷新</el-button></div></header>
      <el-alert v-if="store.error" :title="store.error" type="error" show-icon closable @close="store.error = ''" />
      <el-card shadow="never" class="filter-card"><el-form inline @submit.prevent="refresh"><el-form-item label="主题包"><el-select v-model="store.topicPackId" filterable style="width:260px"><el-option v-for="item in store.topicPacks" :key="item.id" :label="`${item.name} · ${item.evidence_count || 0} 条证据`" :value="item.id" /></el-select></el-form-item><el-form-item label="关键词"><el-input v-model="store.filters.q" placeholder="搜索证据、标题或平台" clearable @keyup.enter="refresh" /></el-form-item><el-form-item label="时间范围"><el-select v-model="store.filters.days" style="width:130px"><el-option :value="7" label="近 7 天" /><el-option :value="30" label="近 30 天" /><el-option :value="90" label="近 90 天" /><el-option :value="365" label="全年" /></el-select></el-form-item><el-form-item><el-button type="primary" @click="refresh">应用筛选</el-button></el-form-item></el-form></el-card>
      <div v-if="store.loading && !store.analytics" class="loading"><el-skeleton :rows="8" animated /></div>
      <template v-else-if="store.analytics">
        <el-row :gutter="16" class="quality-row" v-if="store.quality"><el-col :xs="12" :sm="6" v-for="item in [{k:'healthy_count',t:'健康来源'},{k:'warning_count',t:'需关注'},{k:'stale_count',t:'过期来源'},{k:'duplicate_rate',t:'平均重复率',suffix:'%'}]" :key="item.k"><el-card shadow="never" class="metric quality-metric"><span>{{ item.t }}</span><strong>{{ store.quality.summary[item.k] }}{{ item.suffix || '' }}</strong></el-card></el-col></el-row>
        <el-card shadow="never" class="quality-card" v-if="store.quality"><template #header><div><b>数据质量与来源健康</b><span class="card-hint">按当前主题包和时间范围统计</span></div><el-tag :type="store.quality.summary.error_count ? 'danger' : store.quality.summary.warning_count ? 'warning' : 'success'">{{ store.quality.summary.error_count ? '存在错误' : store.quality.summary.warning_count ? '部分需关注' : '整体健康' }}</el-tag></template><el-table :data="store.quality.sources" stripe size="small"><el-table-column prop="name" label="来源" min-width="180" /><el-table-column prop="platform" label="平台" width="120" /><el-table-column label="状态" width="110"><template #default="scope"><el-tag size="small" :type="scope.row.quality_status === 'healthy' ? 'success' : scope.row.quality_status === 'warning' ? 'warning' : scope.row.quality_status === 'error' ? 'danger' : 'info'">{{ scope.row.quality_status }}</el-tag></template></el-table-column><el-table-column prop="evidence_count" label="证据量" width="90" sortable /><el-table-column label="覆盖率" width="100"><template #default="scope">{{ scope.row.coverage_share }}%</template></el-table-column><el-table-column label="重复率" width="100"><template #default="scope">{{ scope.row.duplicate_rate }}%</template></el-table-column><el-table-column label="失败率" width="100"><template #default="scope">{{ scope.row.failure_rate }}%</template></el-table-column><el-table-column label="最近抓取" min-width="190"><template #default="scope">{{ scope.row.latest_fetched_at || '暂无' }}</template></el-table-column></el-table></el-card>
        <el-card shadow="never" class="quality-card" v-if="store.tasks"><template #header><div><b>采集任务监控</b><span class="card-hint">最后运行、成功率和抓取量</span></div><el-tag type="info">{{ store.tasks.summary.task_count }} 个任务</el-tag></template><el-table :data="store.tasks.tasks" stripe size="small"><el-table-column prop="name" label="任务" min-width="180" /><el-table-column prop="query" label="查询" min-width="150" show-overflow-tooltip /><el-table-column label="状态" width="110"><template #default="scope"><el-tag size="small" :type="scope.row.monitor_status === 'healthy' ? 'success' : scope.row.monitor_status === 'error' ? 'danger' : scope.row.monitor_status === 'running' ? 'warning' : 'info'">{{ scope.row.monitor_status }}</el-tag></template></el-table-column><el-table-column prop="run_count" label="运行次数" width="90" /><el-table-column label="成功率" width="90"><template #default="scope">{{ scope.row.success_rate }}%</template></el-table-column><el-table-column prop="items_fetched" label="抓取量" width="90" /><el-table-column label="最后运行" min-width="190"><template #default="scope">{{ scope.row.last_finished_at || scope.row.last_started_at || '从未运行' }}</template></el-table-column><el-table-column label="操作" width="110" fixed="right"><template #default="scope"><el-button link type="primary" :loading="scope.row.monitor_status === 'running'" @click="rerunTask(scope.row)">立即运行</el-button></template></el-table-column></el-table></el-card>
        <el-row :gutter="16"><el-col :xs="24" :lg="16"><el-card shadow="never"><template #header><b>需求热度趋势</b><span class="card-hint">按抓取日期统计</span></template><Chart :option="lineOption" height="310px" /></el-card></el-col><el-col :xs="24" :lg="8"><el-card shadow="never"><template #header><b>词云</b><span class="card-hint">高频需求词</span></template><div class="word-cloud"><span v-for="(word, index) in wordCloud" :key="word.name" :style="{ fontSize: `${14 + Math.min(word.value * 3, 24)}px`, color: ['#2f6f6d','#7b61a8','#c47c35','#356a9a'][index % 4] }">{{ word.name }}</span><em v-if="!wordCloud.length">暂无词频数据</em></div></el-card></el-col></el-row>
        <el-row :gutter="16" class="chart-row"><el-col :xs="24" :md="12"><el-card shadow="never"><template #header><b>来源平台分布</b></template><Chart :option="platformOption" height="300px" /></el-card></el-col><el-col :xs="24" :md="12"><el-card shadow="never"><template #header><b>内容类型分布</b></template><Chart :option="typeOption" height="300px" /></el-card></el-col></el-row>
        <el-row :gutter="16" class="chart-row"><el-col :xs="24" :md="12"><el-card shadow="never"><template #header><b>高频主题</b></template><el-table :data="store.analytics.topics" size="small"><el-table-column prop="name" label="主题" /><el-table-column prop="value" label="出现次数" width="100" /></el-table></el-card></el-col><el-col :xs="24" :md="12"><el-card shadow="never"><template #header><b>关联实体</b></template><el-table :data="store.analytics.entities" size="small"><el-table-column prop="name" label="实体" /><el-table-column prop="value" label="出现次数" width="100" /></el-table></el-card></el-col></el-row>
        <el-card shadow="never" class="evidence-card"><template #header><b>代表性证据</b><el-button link @click="refresh">刷新</el-button></template><el-table :data="store.evidence?.items || []" stripe @row-click="openEvidence"><el-table-column prop="title" label="标题" min-width="280" show-overflow-tooltip /><el-table-column prop="platform" label="平台" width="130" /><el-table-column prop="item_type" label="类型" width="130" /><el-table-column prop="fetched_at" label="抓取时间" width="190" /></el-table></el-card>
      </template>
    </el-main>
  </el-container>
  <el-drawer v-model="reportDrawer" :title="store.report?.title || '分析报告'" size="min(760px, 94vw)"><div class="report-toolbar"><el-button type="primary" @click="downloadReport">下载 Markdown</el-button></div><pre class="report-preview">{{ store.report?.markdown }}</pre></el-drawer>
  <el-drawer v-model="drawer" title="证据详情" size="min(560px, 92vw)"><div v-if="selected"><h3>{{ selected.title }}</h3><el-descriptions :column="1" border><el-descriptions-item label="平台">{{ selected.platform }}</el-descriptions-item><el-descriptions-item label="类型">{{ selected.item_type }}</el-descriptions-item><el-descriptions-item label="来源">{{ selected.source?.name }}</el-descriptions-item><el-descriptions-item label="时间">{{ selected.fetched_at }}</el-descriptions-item></el-descriptions><p class="detail-text">{{ selected.text || selected.snippet }}</p><el-link v-if="selected.url" :href="selected.url" target="_blank" type="primary">打开原文</el-link></div></el-drawer>
</template>
