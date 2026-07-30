# Search Skill Integrations

This project uses multiple search skills/providers as practical information-source adapters.

## Installed Skills

### Tavily Search

- Skill: `tavily-search`
- Hermes path: `~/.hermes/skills/tavily-search`
- CLI: `tvly`
- Env var: `TAVILY_API_KEY`
- Status: installed and authenticated.
- Use for: high-quality general web search, news search, domain-filtered search, extraction workflows.

Example:

```bash
tvly search "social listening platform architecture" --max-results 5 --json
```

### AnySearch

- Skill: `anysearch`
- Hermes path: `~/.hermes/skills/anysearch`
- Runtime: Python CLI configured in `runtime.conf`
- Env var: `ANYSEARCH_API_KEY` optional
- Status: installed and anonymous search verified. Add key for higher limits.
- Use for: general web search, vertical domain search, batch search, URL extraction.

Configured command:

```bash
python3 /root/.hermes/skills/anysearch/scripts/anysearch_cli.py
```

Example:

```bash
python3 /root/.hermes/skills/anysearch/scripts/anysearch_cli.py search "semiconductor supply chain pain points" --max_results 5
```

### Baidu Search

- Skill: `baidu-search`
- Hermes path: `~/.hermes/skills/baidu-search`
- Env vars: `BAIDU_SEARCH_API_KEY` preferred, or `QIANFAN_API_KEY`
- Required key format: `bce-v3/...`
- Status: installed; missing API key.
- Use for: Chinese web search, Baidu Baike, MiaoDong Baike, Qianfan AI search.

Example after key is configured:

```bash
python3 /root/.hermes/skills/baidu-search/scripts/search.py "半导体 产业链 痛点" --json
```

## Global Env Location

Secrets should be stored in:

```text
~/.hermes/.env
```

Expected entries:

```bash
TAVILY_API_KEY=tvly-...
ANYSEARCH_API_KEY=as_sk_...
BAIDU_SEARCH_API_KEY=bce-v3/...
```

Do not commit provider keys into the project repository.
