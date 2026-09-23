import asyncio
import xmlrpc.client
from unittest.mock import MagicMock

import pytest

from odoo_mcp import server
from odoo_mcp.server import ToolError


@pytest.fixture
def odoo(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(server, "_client", fake)
    monkeypatch.delenv("ODOO_ALLOW_WRITES", raising=False)
    return fake


def test_all_core_tools_registered_with_annotations():
    tools = {t.name: t for t in asyncio.run(server.mcp.list_tools())}
    assert set(tools) == {
        "list_models",
        "get_model_schema",
        "search_records",
        "get_record",
        "create_record",
        "update_record",
    }
    for name in ("list_models", "get_model_schema", "search_records", "get_record"):
        assert tools[name].annotations.read_only_hint is True
    for name in ("create_record", "update_record"):
        assert tools[name].annotations.read_only_hint is False


def test_search_records_caps_limit(odoo):
    odoo.execute.return_value = [{"id": 1, "name": "Acme"}]
    result = server.search_records("res.partner", [["is_company", "=", True]], ["name"], limit=10_000, order="name")
    assert result == [{"id": 1, "name": "Acme"}]
    odoo.execute.assert_called_once_with(
        "res.partner", "search_read", [["is_company", "=", True]], limit=server.MAX_LIMIT, offset=0, fields=["name"], order="name"
    )


def test_list_models_filter(odoo):
    server.list_models("partner")
    args, kwargs = odoo.execute.call_args
    assert args[:2] == ("ir.model", "search_read")
    assert args[2][0] == "|"
    assert kwargs["fields"] == ["model", "name"]


def test_get_model_schema(odoo):
    server.get_model_schema("sale.order")
    odoo.execute.assert_called_once_with("sale.order", "fields_get", attributes=server.SCHEMA_ATTRIBUTES)


def test_get_record_found_and_missing(odoo):
    odoo.execute.return_value = [{"id": 3}]
    assert server.get_record("res.partner", 3) == {"id": 3}
    odoo.execute.return_value = []
    with pytest.raises(ToolError):
        server.get_record("res.partner", 4)


def test_writes_blocked_by_default(odoo):
    with pytest.raises(ToolError, match="ODOO_ALLOW_WRITES"):
        server.create_record("res.partner", {"name": "X"})
    with pytest.raises(ToolError, match="ODOO_ALLOW_WRITES"):
        server.update_record("res.partner", 1, {"name": "X"})
    odoo.execute.assert_not_called()


def test_writes_allowed_when_enabled(odoo, monkeypatch):
    monkeypatch.setenv("ODOO_ALLOW_WRITES", "1")
    odoo.execute.return_value = 42
    assert server.create_record("res.partner", {"name": "X"}) == 42
    odoo.execute.return_value = True
    assert server.update_record("res.partner", 42, {"name": "Y"}) is True
    odoo.execute.assert_called_with("res.partner", "write", [42], {"name": "Y"})


def test_call_tool_through_mcp(odoo):
    odoo.execute.return_value = [{"id": 1}]
    result = asyncio.run(server.mcp.call_tool("get_record", {"model": "res.partner", "record_id": 1}))
    assert result.is_error is False
    assert '"id": 1' in result.content[0].text


def test_odoo_fault_becomes_readable_tool_error(odoo):
    odoo.execute.side_effect = xmlrpc.client.Fault(1, "Traceback ...\nValueError: Invalid field 'nope' on model 'res.partner'")
    with pytest.raises(ToolError, match="Invalid field 'nope'"):
        server.search_records("res.partner", fields=["nope"])


def test_write_gate_message_reaches_client(odoo):
    # ToolError (unlike other exceptions) keeps its message when sent to the client.
    with pytest.raises(ToolError, match="create_record: Write tools are disabled.*ODOO_ALLOW_WRITES=1"):
        asyncio.run(server.mcp.call_tool("create_record", {"model": "res.partner", "values": {"name": "X"}}))
