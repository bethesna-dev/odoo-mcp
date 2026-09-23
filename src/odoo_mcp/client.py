"""Minimal Odoo XML-RPC client (stdlib only)."""

from __future__ import annotations

import os
import xmlrpc.client
from dataclasses import dataclass
from typing import Any


class OdooConfigError(RuntimeError):
    """Raised when required Odoo environment variables are missing."""


@dataclass(frozen=True)
class OdooConfig:
    url: str
    db: str
    username: str
    secret: str  # API key (preferred) or password; Odoo accepts either over XML-RPC

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> OdooConfig:
        env = dict(os.environ if env is None else env)
        secret = env.get("ODOO_API_KEY") or env.get("ODOO_PASSWORD", "")
        values = {
            "ODOO_URL": env.get("ODOO_URL", "").rstrip("/"),
            "ODOO_DB": env.get("ODOO_DB", ""),
            "ODOO_USERNAME": env.get("ODOO_USERNAME", ""),
            "ODOO_API_KEY or ODOO_PASSWORD": secret,
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise OdooConfigError(f"Missing Odoo configuration: {', '.join(missing)}")
        return cls(
            url=values["ODOO_URL"],
            db=values["ODOO_DB"],
            username=values["ODOO_USERNAME"],
            secret=secret,
        )


class OdooClient:
    def __init__(self, config: OdooConfig) -> None:
        self.config = config
        self._common = xmlrpc.client.ServerProxy(f"{config.url}/xmlrpc/2/common", allow_none=True)
        self._models = xmlrpc.client.ServerProxy(f"{config.url}/xmlrpc/2/object", allow_none=True)
        self._uid: int | None = None

    @property
    def uid(self) -> int:
        if self._uid is None:
            uid = self._common.authenticate(self.config.db, self.config.username, self.config.secret, {})
            if not uid:
                raise PermissionError("Odoo authentication failed; check ODOO_USERNAME and ODOO_API_KEY/ODOO_PASSWORD")
            self._uid = uid
        return self._uid

    def execute(self, model: str, method: str, *args: Any, **kwargs: Any) -> Any:
        return self._models.execute_kw(self.config.db, self.uid, self.config.secret, model, method, list(args), kwargs)
