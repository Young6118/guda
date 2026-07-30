# Tianyan AI Connector

This package wraps the official `tyc` CLI.

Authentication is handled by Tianyan CLI login/config state. Do not store the API key in this repository.

## Setup

```bash
npm install -g tyc-cli
tyc init --url "https://mcp.tianyancha.com/v1" --authorization "$TYC_API_KEY"
```

## Smoke Test

```bash
tyc --version
tyc company registration-info "宁德时代新能源科技股份有限公司" --head 40
```

## Python Usage

```python
from integrations.tianyan_ai import TianyanAIClient

client = TianyanAIClient()
profile = client.registration_info("宁德时代新能源科技股份有限公司")
```
