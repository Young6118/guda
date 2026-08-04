import { defineStore } from 'pinia'
import { getAnalytics, getEvidence, getInsights, getQuality, getReport, getTaskDetail, getTasks, getTopicPacks, runTask } from '../api.js'

export const useAnalysisStore = defineStore('analysis', {
  state: () => ({
    topicPacks: [],
    topicPackId: '',
    analytics: null,
    insights: null,
    report: null,
    quality: null,
    tasks: null,
    evidence: null,
    loading: false,
    error: '',
    filters: { q: '', days: 30 },
  }),
  actions: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        if (!this.topicPacks.length) {
          this.topicPacks = (await getTopicPacks()).data
          this.topicPackId ||= this.topicPacks[0]?.id || ''
        }
        const params = { ...this.filters, topic_pack_id: this.topicPackId || undefined }
        const [analytics, insights, report, quality, tasks, evidence] = await Promise.all([
          getAnalytics(params),
          getInsights(params),
          getReport(params),
          getQuality(params),
          getTasks({ topic_pack_id: this.topicPackId || undefined }),
          getEvidence({ q: this.filters.q || undefined, page: 1, page_size: 10 }),
        ])
        this.analytics = analytics.data
        this.insights = insights.data
        this.report = report.data
        this.quality = quality.data
        this.tasks = tasks.data
        this.evidence = evidence.data
      } catch (error) {
        this.error = error?.response?.data?.detail || error.message || '加载失败'
      } finally {
        this.loading = false
      }
    },
    async selectTopicPack(id) {
      this.topicPackId = id
      await this.load()
    },
  },
})
