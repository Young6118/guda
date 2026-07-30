# Compliance Notes

## Principle

The platform should collect and analyze data responsibly. It should prefer official APIs, authorized access, paid data providers with compliance commitments, public RSS/search feeds, and manual imports over brittle or aggressive scraping.

## Rules

1. Preserve source URLs and citations.
2. Do not collect private messages, private groups, or non-public data without explicit authorization.
3. Avoid collecting sensitive personal information unless strictly necessary and legally permitted.
4. Hash or redact user identifiers where possible.
5. Store source terms, access status, and compliance notes in the source registry.
6. Track paid provider provenance and license restrictions.
7. Use per-source rate limits and budgets.
8. Make browser-assisted collection explicit, auditable, and low volume.
9. Separate raw evidence from AI interpretation.
10. Allow deletion/export of source data if required by policy or law.

## Authenticated and Headless Collection

Some sources will require logged-in or browser-based acquisition. Treat this as a controlled escalation layer, not the default path.

Allowed pattern:

1. Try official/authorized APIs first.
2. Try public endpoints or paid provider APIs next.
3. Use logged-in browser sessions for exploratory, low-volume, human-reviewable collection.
4. Use headless authenticated collection only when a source/task explicitly allows it and the value justifies the maintenance/compliance risk.

Controls required for logged-in/headless collection:

- Store `session_profile_id`, acquisition layer, and run logs for every item fetched.
- Keep cookies/tokens in private runtime storage, not in committed files.
- Set per-source rate limits, max pages/items per run, and cooldown windows.
- Disable broad recurring headless scans by default.
- Do not bypass paywalls, private groups, private messages, permission dialogs, or access controls.
- Use manual review for new selectors/workflows before enabling recurrence.
- Record failure reasons such as login expired, captcha, rate limit, selector drift, or content unavailable.

## Platform Notes

### GitHub

Use official REST/GraphQL APIs where possible. Respect rate limits and secondary rate limits. Prefer ETags/webhooks for recurring monitoring.

### Reddit

Commercial access may require approval or payment. Use official API or compliant data providers for production use.

### X / Twitter

Official API and paid providers can be costly. Budget and provenance tracking are required.

### WeChat Public Accounts

Official account statistics and comments are available only for authorized accounts/articles. Public article discovery can be done via search/providers/manual research, but comments and metrics are constrained.

### Douyin

Official APIs often require user authorization and may only cover authorized account content or specific approved scopes. Public platform-wide listening likely requires a provider or manual research workflow.

### Xiaohongshu

High-value source but platform access is restrictive. Prefer official/authorized business access, paid provider samples, or low-volume browser-assisted research. Treat aggressive crawling as high risk.

### Bilibili

Public video metadata, comments, and danmaku can be accessible but should still be rate-limited and cited.

### Zhihu / Weibo / Xueqiu

Use provider/manual/browser-assisted paths carefully. Treat broad scraping as higher risk.

### AxData / eltdx / TdxQuant MCP / A-share Market Data

Use AxData as the preferred framework reference because it is Apache-2.0 and designed as a local quantitative database framework. Treat eltdx as a useful TDX protocol/MCP research adapter, but note its Research-Only license: do not use eltdx-derived code/data for commercial, paid, production, resale, or automated trading services unless separate permission and upstream data rights are resolved. Treat tdxquant-mcp as evaluation-only until its repository license and TdxQuant/通达信 terminal/data rights are clear; it requires a local logged-in terminal and includes trading tools. Collection adapters must not expose real trading operations, and any trading-capable tool must remain `dry_run=true` or be excluded entirely. Record third-party data-source terms for TDX, exchanges, F10 providers, and financial websites before any production use.

### Google Maps

Use Google Maps MCP only under Google Maps Platform terms, billing, quota, attribution, caching, and retention rules. Store source/provider terms in the source registry. Treat geocodes, place details, reviews metadata, distance matrix, directions, and elevation as enrichment data, not unrestricted raw data for resale. Avoid repeatedly polling static location data; cache only in ways allowed by the provider terms.

## Insight Safety

Every insight must show:

- Evidence count.
- Source distribution.
- Representative citations.
- Time range.
- Confidence.
- Caveats and bias notes.

Do not infer private attributes or overstate market conclusions from narrow samples.
