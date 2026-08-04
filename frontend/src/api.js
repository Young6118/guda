import axios from 'axios'

const match = window.location.pathname.match(/^(.*\/app)(?:\/.*)?$/)
const basePath = match ? match[1].replace(/\/app$/, '') : ''

export const api = axios.create({ baseURL: `${basePath}/api/` })
export const getTopicPacks = () => api.get('topic-packs')
export const getAnalytics = (params) => api.get('app/analytics', { params })
export const getInsights = (params) => api.get('app/insights', { params })
export const getReport = (params) => api.get('app/report', { params })
export const getQuality = (params) => api.get('app/quality', { params })
export const getTasks = (params) => api.get('app/tasks', { params })
export const getTaskDetail = (id) => api.get(`app/tasks/${encodeURIComponent(id)}`)
export const runTask = (id) => api.post(`app/tasks/${encodeURIComponent(id)}/run`)
export const getEvidence = (params) => api.get('evidence-items', { params })
export const getEvidenceDetail = (id) => api.get(`evidence-items/${encodeURIComponent(id)}`)
