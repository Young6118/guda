# Tianyan AI Integration

## Status

Tianyan AI is configured as an authoritative company and business intelligence source.

Integration mode for this workspace:

- Actual agent integration: Tianyan AI CLI + Hermes Skill, following the official Tianyan guide.
- CLI package: `tyc-cli`
- CLI command: `tyc`
- Endpoint: `https://mcp.tianyancha.com/v1`
- Hermes skill: `tyc-it`
- Secret location: Tianyan CLI login/config state, not project files.

Do not commit API keys. The project `.gitignore` excludes `.env` and runtime artifacts.

## Why Tianyan AI Matters

Tianyan AI is a high-authority structured source for China business intelligence. It complements public discussion sources with verified company facts.

Use it for:

- Company identity resolution.
- Business registration and status.
- Legal representative, registration capital, address, industry.
- Shareholders, actual control, group and related-party analysis.
- Litigation, enforcement, administrative penalties, operating exceptions.
- Bid information, qualifications, products, recruitment, suppliers/customers.
- IP signals such as patents, trademarks, software copyrights.
- Industry/company discovery by region, tag, ranking, park, or keyword.

## Source Registry Entry

Suggested source configuration:

```json
{
  "id": "src_tianyan_ai",
  "name": "Tianyan AI",
  "platform": "tianyancha",
  "source_type": "official_or_authorized_api",
  "access_status": "active",
  "provider": "tianyan_ai_cli",
  "base_url": "https://mcp.tianyancha.com/v1",
  "auth_profile_id": "secret:TYC_API_KEY_OR_TYC_CLI_LOGIN_STATE",
  "rate_limit_policy": "budgeted business queries; no bulk scans without approval",
  "cost_model": "account quota / paid API usage; track per collection run",
  "coverage_notes": "China company registration, risk, equity, operations, IP, executives, history, industry discovery",
  "compliance_notes": "Use official Tianyan AI access. Do not expose API key. Preserve source and query provenance. Avoid high-cost/risk scans unless approved."
}
```

## Collection Task Patterns

Tianyan AI is not a general social listening stream. It is an enrichment and verification source.

Recommended task types:

### Company Enrichment

Given company names extracted from public discussion, resolve and enrich them.

- Input: company name, USCC, brand, alias.
- First call: `tyc company search-companies <query>`.
- Then: registration info or basic profile.
- Output: normalized company entity record.

### Risk Snapshot

For companies found in supplier/customer/market discussions, generate a lightweight risk snapshot.

- Anchor company.
- Query basic profile.
- Query risk overview only when needed.
- Avoid legal/risk deep dives unless task budget allows.

### Industry Discovery

For topic packs such as semiconductor, AI applications, ecommerce, or marketing tools, discover relevant companies by industry/region/tag and enrich top candidates.

Examples:

- semiconductor companies in Shanghai/Shenzhen/Suzhou.
- AI application companies in Beijing/Shanghai/Hangzhou/Shenzhen.
- cross-border ecommerce service providers.

### Entity Disambiguation

When social posts mention ambiguous company names, use Tianyan AI to identify the likely formal entity.

## CLI Usage Examples

List tool layers:

```bash
tyc layers --md
```

Search companies:

```bash
tyc company search-companies "宁德时代" --head 40
```

Get registration info:

```bash
tyc company registration-info "宁德时代新能源科技股份有限公司" --head 40
```

Use markdown output for human review:

```bash
tyc company registration-info "宁德时代新能源科技股份有限公司" --md --head 40
```

## Connector Wrapper Direction

The platform can call Tianyan AI through the `tyc` CLI initially. Later it can use MCP directly if we need in-process tool calls.

MVP wrapper responsibilities:

- Verify `tyc` exists.
- Call `tyc` with compact JSON output.
- Redact secrets from logs.
- Enforce per-task budget and allowlist of low-cost commands.
- Normalize returned records into `company_entities`, `raw_items`, and `evidence_items`.

## Safety Rules

- Never log the full API key.
- Never store the API key in repo files.
- Do not run high-cost scans without explicit task budget.
- For first validation, use one lightweight registration-info query.
- Keep raw Tianyan responses as structured payloads with source/run metadata.
