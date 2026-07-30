"""Tianyan AI CLI wrapper.

This module intentionally calls the `tyc` CLI instead of storing or handling the
API key directly. Authentication lives in the Tianyan CLI config/login state.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any


class TianyanAIError(RuntimeError):
    """Raised when the Tianyan AI CLI is unavailable or returns invalid data."""


@dataclass(frozen=True)
class TianyanAIClient:
    """Small wrapper around the official `tyc` CLI."""

    command: str = "tyc"
    timeout_seconds: int = 60

    def ensure_available(self) -> str:
        path = shutil.which(self.command)
        if not path:
            raise TianyanAIError("Tianyan AI CLI command `tyc` was not found. Install tyc-cli and run `tyc init` first.")
        return path

    def run_json(self, args: list[str]) -> dict[str, Any]:
        self.ensure_available()
        cmd = [self.command, *args, "--compact"]
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=self.timeout_seconds)
        if proc.returncode != 0:
            raise TianyanAIError(_redact_secret(proc.stderr or proc.stdout or "tyc command failed"))
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise TianyanAIError(f"tyc returned non-JSON output: {proc.stdout[:500]}") from exc

    def search_companies(self, query: str, head: int = 20) -> dict[str, Any]:
        return self.run_json(["company", "companies", query, "--head", str(head)])

    def registration_info(self, company_name: str, head: int = 80) -> dict[str, Any]:
        return self.run_json(["company", "registration-info", company_name, "--head", str(head)])

    def layers(self) -> dict[str, Any]:
        return self.run_json(["layers"])


def _redact_secret(text: str) -> str:
    import re

    return re.sub(r"mcpk\d*_[A-Za-z0-9_\-]+", "mcpk_REDACTED", text)
