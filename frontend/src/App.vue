<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useAnalysisStore } from './stores/analysis'
import Chart from './components/Chart.vue'

const store = useAnalysisStore()
const drawer = ref(false)
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
        <el-menu-item index="insights">洞察卡片 <el-tag size="small" type="info">Soon</el-tag></el-menu-item>
        <el-menu-item index="reports">报告 <el-tag size="small" type="info">Soon</el-tag></el-menu-item>
      </el-menu>
      <a class="admin-link" href="../admin/">进入管理后台 →</a>
    </el-aside>
    <el-main class="main">
      <header class="topbar"><div><div class="eyebrow">DEMAND INTELLIGENCE</div><h1>需求情报总览</h1><p>从真实证据中看见需求、主题与趋势变化</p></div><el-button @click="refresh" :loading="store.loading">刷新</el-button></header>
      <el-alert v-if="store.error" :title="store.error" type="error" show-icon closable @close="store.error = ''" />
      <el-card shadow="never" class="filter-card"><el-form inline @submit.prevent="refresh"><el-form-item label="主题包"><el-select v-model="store.topicPackId" filterable style="width:260px"><el-option v-for="item in store.topicPacks" :key="item.id" :label="`${item.name} · ${item.evidence_count || 0} 条证据`" :value="item.id" /></el-select></el-form-item><el-form-item label="关键词"><el-input v-model="store.filters.q" placeholder="搜索证据、标题或平台" clearable @keyup.enter="refresh" /></el-form-item><el-form-item label="时间范围"><el-select v-model="store.filters.days" style="width:130px"><el-option :value="7" label="近 7 天" /><el-option :value="30" label="近 30 天" /><el-option :value="90" label="近 90 天" /><el-option :value="365" label="全年" /></el-select></el-form-item><el-form-item><el-button type="primary" @click="refresh">应用筛选</el-button></el-form-item></el-form></el-card>
      <div v-if="store.loading && !store.analytics" class="loading"><el-skeleton :rows="8" animated /></div>
      <template v-else-if="store.analytics">
        <el-row :gutter="16" class="metrics"><el-col v-for="item in [{k:'evidence_count',t:'证据总量'},{k:'source_count',t:'来源数'},{k:'platform_count',t:'平台数'},{k:'topic_count',t:'主题数'}]" :key="item.k" :xs="12" :sm="6"><el-card shadow="never" class="metric"><span>{{ item.t }}</span><strong>{{ store.analytics.summary[item.k] }}</strong></el-card></el-col></el-row>
        <el-row v-if="store.insights?.insights?.length" :gutter="16" class="insights-row"><el-col v-for="insight in store.insights.insights" :key="`${insight.type}-${insight.title}`" :xs="24" :md="12" :lg="8"><el-card shadow="never" class="insight-card"><div class="insight-head"><el-tag :type="insight.severity === 'positive' ? 'success' : insight.severity === 'warning' ? 'warning' : 'info'" size="small">{{ insight.type === 'trend' ? '趋势' : insight.type === 'keyword' ? '关键词' : insight.type === 'platform' ? '来源' : '主题' }}</el-tag><span class="card-hint">{{ store.insights.summary.period_days }} 天</span></div><h3>{{ insight.title }}</h3><p>{{ insight.summary }}</p></el-card></el-col></el-row>
        <el-row :gutter="16"><el-col :xs="24" :lg="16"><el-card shadow="never"><template #header><b>需求热度趋势</b><span class="card-hint">按抓取日期统计</span></template><Chart :option="lineOption" height="310px" /></el-card></el-col><el-col :xs="24" :lg="8"><el-card shadow="never"><template #header><b>词云</b><span class="card-hint">高频需求词</span></template><div class="word-cloud"><span v-for="(word, index) in wordCloud" :key="word.name" :style="{ fontSize: `${14 + Math.min(word.value * 3, 24)}px`, color: ['#2f6f6d','#7b61a8','#c47c35','#356a9a'][index % 4] }">{{ word.name }}</span><em v-if="!wordCloud.length">暂无词频数据</em></div></el-card></el-col></el-row>
        <el-row :gutter="16" class="chart-row"><el-col :xs="24" :md="12"><el-card shadow="never"><template #header><b>来源平台分布</b></template><Chart :option="platformOption" height="300px" /></el-card></el-col><el-col :xs="24" :md="12"><el-card shadow="never"><template #header><b>内容类型分布</b></template><Chart :option="typeOption" height="300px" /></el-card></el-col></el-row>
        <el-row :gutter="16" class="chart-row"><el-col :xs="24" :md="12"><el-card shadow="never"><template #header><b>高频主题</b></template><el-table :data="store.analytics.topics" size="small"><el-table-column prop="name" label="主题" /><el-table-column prop="value" label="出现次数" width="100" /></el-table></el-card></el-col><el-col :xs="24" :md="12"><el-card shadow="never"><template #header><b>关联实体</b></template><el-table :data="store.analytics.entities" size="small"><el-table-column prop="name" label="实体" /><el-table-column prop="value" label="出现次数" width="100" /></el-table></el-card></el-col></el-row>
        <el-card shadow="never" class="evidence-card"><template #header><b>代表性证据</b><el-button link @click="refresh">刷新</el-button></template><el-table :data="store.evidence?.items || []" stripe @row-click="openEvidence"><el-table-column prop="title" label="标题" min-width="280" show-overflow-tooltip /><el-table-column prop="platform" label="平台" width="130" /><el-table-column prop="item_type" label="类型" width="130" /><el-table-column prop="fetched_at" label="抓取时间" width="190" /></el-table></el-card>
      </template>
    </el-main>
  </el-container>
  <el-drawer v-model="drawer" title="证据详情" size="min(560px, 92vw)"><div v-if="selected"><h3>{{ selected.title }}</h3><el-descriptions :column="1" border><el-descriptions-item label="平台">{{ selected.platform }}</el-descriptions-item><el-descriptions-item label="类型">{{ selected.item_type }}</el-descriptions-item><el-descriptions-item label="来源">{{ selected.source?.name }}</el-descriptions-item><el-descriptions-item label="时间">{{ selected.fetched_at }}</el-descriptions-item></el-descriptions><p class="detail-text">{{ selected.text || selected.snippet }}</p><el-link v-if="selected.url" :href="selected.url" target="_blank" type="primary">打开原文</el-link></div></el-drawer>
</template>
