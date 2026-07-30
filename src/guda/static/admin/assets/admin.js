const adminIndex = (() => {
  const adminMatch = window.location.pathname.match(/^(.*\/admin)(?:\/.*)?$/);
  const appBase = adminMatch ? adminMatch[1].replace(/\/admin$/, '') : '';
  return { apiBase: `${appBase}/api/` };
})();

const $ = (sel, root = document) => root.querySelector(sel);
const on = (sel, event, handler) => { const el = $(sel); if (el) el.addEventListener(event, handler); };
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state = { view: 'overview', lang: localStorage.getItem('guda.lang') || 'zh', theme: localStorage.getItem('guda.theme') || 'light', pages: {} };

const dict = {
  zh: {
    brandSubtitle: '来源情报', adminConsole: '管理控制台', refresh: '刷新', themeLight: '浅色', themeDark: '深色', langToggle: 'EN',
    overview: '总览', sources: '数据源', catalog: '来源目录', ratePolicies: '频率策略', evidence: '证据', companies: '公司',
    connectorCoverage: '连接器覆盖', policies: '策略', coolingDown: '冷却中', filter: '筛选', search: '搜索', reset: '重置', save: '保存', clear: '清除',
    noData: '暂无数据', loading: '加载中', page: '页', total: '总数', prev: '上一页', next: '下一页',
    name: '名称', platform: '平台', type: '类型', health: '健康', provider: '供应商', id: 'ID', status: '状态', priority: '优先级', path: '路径', notes: '备注',
    minSec: '最小间隔', cooldownSec: '冷却秒数', burst: '突发', enabled: '启用', cooldownUntil: '冷却至', lastError: '最近错误', actions: '操作',
    title: '标题', itemType: '类型', source: '来源', fetchedAt: '抓取时间', company: '公司', creditCode: '统一信用代码', industry: '行业', region: '地区', registration: '状态'
  },
  en: {
    brandSubtitle: 'Source Intelligence', adminConsole: 'Admin Console', refresh: 'Refresh', themeLight: 'Light', themeDark: 'Dark', langToggle: '中文',
    overview: 'Overview', sources: 'Sources', catalog: 'Catalog', ratePolicies: 'Rate Policies', evidence: 'Evidence', companies: 'Companies',
    connectorCoverage: 'Connector Coverage', policies: 'Policies', coolingDown: 'Cooling Down', filter: 'Filter', search: 'Search', reset: 'Reset', save: 'Save', clear: 'Clear',
    noData: 'No data', loading: 'Loading', page: 'Page', total: 'Total', prev: 'Previous', next: 'Next',
    name: 'Name', platform: 'Platform', type: 'Type', health: 'Health', provider: 'Provider', id: 'ID', status: 'Status', priority: 'Priority', path: 'Path', notes: 'Notes',
    minSec: 'Min sec', cooldownSec: 'Cooldown sec', burst: 'Burst', enabled: 'Enabled', cooldownUntil: 'Cooldown until', lastError: 'Last error', actions: 'Actions',
    title: 'Title', itemType: 'Type', source: 'Source', fetchedAt: 'Fetched at', company: 'Company', creditCode: 'Credit code', industry: 'Industry', region: 'Region', registration: 'Status'
  }
};
const t = (key) => dict[state.lang][key] || key;

async function api(path, opts) {
  const res = await fetch(new URL(path, window.location.origin + adminIndex.apiBase), opts);
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

function showStatus(msg, type = '') {
  const el = $('#status');
  el.textContent = msg;
  el.className = `status ${type}`;
  el.classList.remove('hidden');
  setTimeout(() => el.classList.add('hidden'), 5000);
}
function badge(value) {
  const v = String(value || 'unknown');
  let cls = '';
  if (['implemented','ok','active'].includes(v)) cls = 'ok';
  if (v.includes('gated') || v.includes('planned') || v.includes('cool') || v === 'unknown') cls = 'warn';
  if (['error','failed'].includes(v)) cls = 'danger';
  return `<span class="badge ${cls}">${esc(v)}</span>`;
}
function pageState(key) {
  state.pages[key] ||= { page: 1, pageSize: 20, q: '', sort: '', direction: 'asc', data: { items: [], total: 0, page: 1, page_size: 20 } };
  return state.pages[key];
}
function qs(params) {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== '') sp.set(k, v); });
  return sp.toString();
}
function renderTable({ key, columns, rows, total, page, pageSize, actions = '' }) {
  const body = rows.map(row => `<tr>${columns.map(col => `<td>${col.render ? col.render(row) : esc(row[col.key])}</td>`).join('')}</tr>`).join('') || `<tr><td colspan="${columns.length}"><span class="muted">${t('noData')}</span></td></tr>`;
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  return `
    <div class="table-wrap"><table class="table"><thead><tr>${columns.map(col => `<th>${esc(col.label)}</th>`).join('')}</tr></thead><tbody>${body}</tbody></table></div>
    <div class="pager" data-key="${key}">
      <span>${t('total')}: ${total} · ${t('page')} ${page}/${pageCount}</span>
      <div>${actions}<button data-page="prev" ${page <= 1 ? 'disabled' : ''}>${t('prev')}</button><button data-page="next" ${page >= pageCount ? 'disabled' : ''}>${t('next')}</button></div>
    </div>`;
}
function renderShell(titleKey, inner) {
  $('#page-title').textContent = t(titleKey);
  $('#view-root').innerHTML = inner;
}
function filterBar(key, placeholders = {}) {
  const ps = pageState(key);
  return `<form class="toolbar" data-filter="${key}"><input name="q" value="${esc(ps.q)}" placeholder="${esc(placeholders.q || t('filter'))}" /><button>${t('search')}</button><button type="button" data-reset>${t('reset')}</button></form>`;
}
async function loadOverview() {
  const [sources, catalog, policies] = await Promise.all([api('admin/sources?page_size=1'), api('source-catalog'), api('admin/rate-policies?page_size=1')]);
  const groups = {};
  catalog.forEach(item => groups[item.connector_status] = (groups[item.connector_status] || 0) + 1);
  renderShell('overview', `<div class="metric-grid"><div class="metric"><span>${t('sources')}</span><strong>${sources.total}</strong></div><div class="metric"><span>${t('catalog')}</span><strong>${catalog.length}</strong></div><div class="metric"><span>${t('policies')}</span><strong>${policies.total}</strong></div><div class="metric"><span>${t('coolingDown')}</span><strong>${policies.items.filter(p => p.cooldown_until).length}</strong></div></div><div class="panel"><div class="panel-head"><h2>${t('connectorCoverage')}</h2></div><div class="coverage-list">${Object.entries(groups).sort().map(([k,v]) => `<div class="coverage-item"><strong>${v}</strong><span>${esc(k)}</span></div>`).join('')}</div></div>`);
}
async function loadSources() {
  const ps = pageState('sources');
  const data = await api(`admin/sources?${qs({ q: ps.q, page: ps.page, page_size: ps.pageSize, sort: ps.sort || 'created_at', direction: ps.direction || 'desc' })}`);
  ps.data = data;
  renderShell('sources', `${filterBar('sources', {q: `${t('filter')} ${t('name')} / ${t('platform')}`})}<div class="panel"><div class="panel-head"><h2>${t('sources')}</h2></div>${renderTable({ key:'sources', columns:[{label:t('name'),key:'name'},{label:t('platform'),key:'platform'},{label:t('type'),key:'source_type'},{label:t('health'),render:r=>badge(r.health_status)},{label:t('provider'),key:'provider'},{label:t('id'),render:r=>`<code>${esc(r.id)}</code>`}], rows:data.items, total:data.total, page:data.page, pageSize:data.page_size })}</div>`);
}
async function loadCatalog() {
  const data = await api('source-catalog');
  const ps = pageState('catalog');
  const filtered = data.filter(item => !ps.q || JSON.stringify(item).toLowerCase().includes(ps.q.toLowerCase()));
  const start = (ps.page - 1) * ps.pageSize;
  renderShell('catalog', `${filterBar('catalog')}<div class="panel"><div class="panel-head"><h2>${t('catalog')}</h2></div>${renderTable({ key:'catalog', columns:[{label:t('platform'),key:'platform'},{label:t('priority'),key:'priority'},{label:t('status'),render:r=>badge(r.connector_status)},{label:t('path'),key:'suggested_path'},{label:t('notes'),key:'notes'}], rows:filtered.slice(start,start+ps.pageSize), total:filtered.length, page:ps.page, pageSize:ps.pageSize })}</div>`);
}
async function loadPolicies() {
  const ps = pageState('ratePolicies');
  const data = await api(`admin/rate-policies?${qs({ q: ps.q, page: ps.page, page_size: ps.pageSize, sort: ps.sort || 'platform', direction: ps.direction || 'asc' })}`);
  ps.data = data;
  const rows = data.items.map(p => ({...p, actions:`<div class="row-actions" data-platform="${esc(p.platform)}"><button data-policy="save">${t('save')}</button><button data-policy="clear">${t('clear')}</button></div>`}));
  renderShell('ratePolicies', `${filterBar('ratePolicies')}<div class="panel"><div class="panel-head"><h2>${t('ratePolicies')}</h2></div>${renderTable({ key:'ratePolicies', columns:[{label:t('platform'),key:'platform'},{label:t('minSec'),render:p=>`<input class="policy-input" data-field="min_interval_seconds" type="number" value="${esc(p.min_interval_seconds)}">`},{label:t('cooldownSec'),render:p=>`<input class="policy-input" data-field="cooldown_seconds" type="number" value="${esc(p.cooldown_seconds)}">`},{label:t('burst'),render:p=>`<input class="policy-input" data-field="burst_limit" type="number" value="${esc(p.burst_limit)}">`},{label:t('enabled'),render:p=>`<input data-field="enabled" type="checkbox" ${p.enabled?'checked':''}>`},{label:t('cooldownUntil'),key:'cooldown_until'},{label:t('lastError'),key:'last_error'},{label:t('actions'),key:'actions'}], rows, total:data.total, page:data.page, pageSize:data.page_size })}</div>`);
}
async function loadEvidence() {
  const ps = pageState('evidence');
  const data = await api(`evidence/search?${qs({ query: ps.q || 'agent', limit: ps.pageSize })}`);
  renderShell('evidence', `${filterBar('evidence', {q:t('search')})}<div class="panel"><div class="panel-head"><h2>${t('evidence')}</h2></div>${renderTable({ key:'evidence', columns:[{label:t('title'),render:r=>`<a href="${esc(r.url||'#')}" target="_blank">${esc(r.title||r.id)}</a>`},{label:t('platform'),key:'platform'},{label:t('itemType'),key:'item_type'},{label:t('source'),key:'source_name'},{label:t('fetchedAt'),key:'fetched_at'}], rows:data, total:data.length, page:1, pageSize:ps.pageSize })}</div>`);
}
async function loadCompanies() {
  const ps = pageState('companies');
  const data = await api(`admin/companies?${qs({ q: ps.q || '宁德时代', page: ps.page, page_size: ps.pageSize, dedupe: true })}`);
  ps.data = data;
  renderShell('companies', `${filterBar('companies', {q:t('company')})}<div class="panel"><div class="panel-head"><h2>${t('companies')}</h2></div>${renderTable({ key:'companies', columns:[{label:t('company'),key:'company_name'},{label:t('creditCode'),key:'credit_code'},{label:t('industry'),key:'industry'},{label:t('region'),key:'region'},{label:t('registration'),key:'registration_status'},{label:t('provider'),key:'provider'}], rows:data.items, total:data.total, page:data.page, pageSize:data.page_size })}</div>`);
}
const loaders = { overview: loadOverview, sources: loadSources, catalog: loadCatalog, ratePolicies: loadPolicies, evidence: loadEvidence, companies: loadCompanies };
function renderNav() { $('#nav').innerHTML = Object.keys(loaders).map(key => `<button class="nav ${state.view===key?'active':''}" data-view="${key}">${t(key)}</button>`).join(''); }
function applyChrome() { document.documentElement.lang = state.lang === 'zh' ? 'zh-CN' : 'en'; document.documentElement.dataset.theme = state.theme; document.querySelectorAll('[data-i18n]').forEach(el => el.textContent = t(el.dataset.i18n)); $('#theme-toggle').textContent = state.theme === 'dark' ? t('themeLight') : t('themeDark'); $('#lang-toggle').textContent = t('langToggle'); renderNav(); }
async function render() { applyChrome(); try { await loaders[state.view](); } catch(e) { showStatus(e.message, 'error'); } }
async function savePolicy(row) { const platform = row.querySelector('[data-platform]')?.dataset.platform; const payload = {}; row.querySelectorAll('[data-field]').forEach(el => payload[el.dataset.field] = el.type === 'checkbox' ? el.checked : Number(el.value)); await api(`rate-policies/${encodeURIComponent(platform)}`, { method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload) }); showStatus(`${t('save')} ${platform}`); await render(); }
async function clearPolicy(row) { const platform = row.querySelector('[data-platform]')?.dataset.platform; await api(`rate-policies/${encodeURIComponent(platform)}/clear-cooldown`, { method:'POST' }); showStatus(`${t('clear')} ${platform}`); await render(); }
document.addEventListener('click', ev => { const nav = ev.target.closest('[data-view]'); if(nav){ state.view=nav.dataset.view; pageState(state.view).page=1; render(); } const pager = ev.target.closest('[data-page]'); if(pager){ const key=pager.closest('.pager').dataset.key; const ps=pageState(key); ps.page += pager.dataset.page === 'next' ? 1 : -1; render(); } const policy = ev.target.closest('[data-policy]'); if(policy){ const row=policy.closest('tr'); policy.dataset.policy === 'save' ? savePolicy(row) : clearPolicy(row); } if(ev.target.matches('[data-reset]')){ const key=ev.target.closest('[data-filter]').dataset.filter; state.pages[key] = { page:1, pageSize:20, q:'', sort:'', direction:'asc', data:{items:[],total:0,page:1,page_size:20} }; render(); }});
document.addEventListener('submit', ev => { const form = ev.target.closest('[data-filter]'); if(!form) return; ev.preventDefault(); const key=form.dataset.filter; const ps=pageState(key); ps.q = new FormData(form).get('q') || ''; ps.page = 1; render(); });
on('#refresh', 'click', render);
on('#theme-toggle', 'click', () => { state.theme = state.theme === 'dark' ? 'light' : 'dark'; localStorage.setItem('guda.theme', state.theme); render(); });
on('#lang-toggle', 'click', () => { state.lang = state.lang === 'zh' ? 'en' : 'zh'; localStorage.setItem('guda.lang', state.lang); render(); });
render();
