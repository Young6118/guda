import axios from 'axios'

const match = window.location.pathname.match(/^(.*\/app)(?:\/.*)?$/)
const basePath = match ? match[1].replace(/\/app$/, '') : ''

export const api = axios.create({ baseURL: `${basePath}/api/` })
export const getTopicPacks = () => api.get('topic-packs')
export const getAnalytics = (params) => api.get('app/analytics', { params })
export const getInsights = (params) => api.get('app/insights', { params })
export const getEvidence = (params) => api.get('evidence-items', { params })
export const getEvidenceDetail = (id) => api.get(`evidence-items/${encodeURIComponent(id)}`)
