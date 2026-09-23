from unittest.mock import MagicMock

import pytest

from odoo_mcp import client as client_mod
from odoo_mcp.client import OdooClient, OdooConfig, OdooConfigError

ENV = {"ODOO_URL": "https://odoo.example.com/", "ODOO_DB": "prod", "ODOO_USERNAME": "bot@example.com"}


def test_config_prefers_api_key_and_strips_url():
    cfg = OdooConfig.from_env({**ENV, "ODOO_API_KEY": "key", "ODOO_PASSWORD": "pw"})
    assert cfg.url == "https://odoo.example.com"
    assert cfg.secret == "key"


def test_config_falls_back_to_password():
    assert OdooConfig.from_env({**ENV, "ODOO_PASSWORD": "pw"}).secret == "pw"


def test_config_reports_missing_vars():
    with pytest.raises(OdooConfigError, match="ODOO_DB.*ODOO_API_KEY or ODOO_PASSWORD"):
        OdooConfig.from_env({"ODOO_URL": "x", "ODOO_USERNAME": "u"})


@pytest.fixture
def proxies(monkeypatch):
    common, models = MagicMock(), MagicMock()
    monkeypatch.setattr(
        client_mod.xmlrpc.client, "ServerProxy", lambda url, **_: common if url.endswith("/common") else models
    )
    return common, models


def test_execute_authenticates_once_and_calls_execute_kw(proxies):
    common, models = proxies
    common.authenticate.return_value = 7
    models.execute_kw.return_value = [{"id": 1}]
    client = OdooClient(OdooConfig.from_env({**ENV, "ODOO_API_KEY": "key"}))

    assert client.execute("res.partner", "search_read", [], limit=5) == [{"id": 1}]
    client.execute("res.partner", "search_read", [])

    common.authenticate.assert_called_once_with("prod", "bot@example.com", "key", {})
    models.execute_kw.assert_called_with("prod", 7, "key", "res.partner", "search_read", [[]], {})


def test_failed_auth_raises(proxies):
    proxies[0].authenticate.return_value = False
    client = OdooClient(OdooConfig.from_env({**ENV, "ODOO_PASSWORD": "bad"}))
    with pytest.raises(PermissionError):
        client.execute("res.partner", "read", [1])
