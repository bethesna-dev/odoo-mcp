"""Stdio MCP server exposing core Odoo tools.

Read tools are always available. Write tools (create_record, update_record) are
registered but refuse to run unless ODOO_ALLOW_WRITES=1.
"""

from __future__ import annotations

import os
import xmlrpc.client
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from odoo_mcp.client import OdooClient, OdooConfig, OdooConfigError

MAX_LIMIT = 200
SCHEMA_ATTRIBUTES = ["string", "type", "required", "readonly", "relation", "selection", "help"]

READ = ToolAnnotations(read_only_hint=True, open_world_hint=True)
WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=True)

mcp = MCPServer(
    "odoo",
    instructions=(
        "Tools for an Odoo instance. Use list_models and get_model_schema to discover "
        "models and fields before searching. Domains use Odoo syntax, e.g. "
        '[["is_company", "=", true]]. Writes require ODOO_ALLOW_WRITES=1.'
    ),
)

_client: OdooClient | None = None


def get_client() -> OdooClient:
    global _client
    if _client is None:
        _client = OdooClient(OdooConfig.from_env())
    return _client


def _execute(model: str, method: str, *args: Any, **kwargs: Any) -> Any:
    """Call Odoo, turning expected failures into ToolErrors the model can read."""
    try:
        return get_client().execute(model, method, *args, **kwargs)
    except (OdooConfigError, PermissionError) as exc:
        raise ToolError(str(exc)) from exc
    except xmlrpc.client.Fault as exc:
        # Odoo puts the full server traceback in faultString; the last line is the message.
        raise ToolError(exc.faultString.strip().splitlines()[-1]) from exc


def _require_writes() -> None:
    if os.environ.get("ODOO_ALLOW_WRITES") != "1":
        raise ToolError("Write tools are disabled. Set ODOO_ALLOW_WRITES=1 to enable them.")


@mcp.tool(annotations=READ)
def list_models(name_filter: str = "", limit: int = 50) -> list[dict[str, Any]]:
    """List installed Odoo models, optionally filtered by technical or display name."""
    domain: list[Any] = ["|", ["model", "ilike", name_filter], ["name", "ilike", name_filter]] if name_filter else []
    return _execute(
        "ir.model", "search_read", domain, fields=["model", "name"], limit=min(limit, MAX_LIMIT), order="model"
    )


@mcp.tool(annotations=READ)
def get_model_schema(model: str) -> dict[str, Any]:
    """Return field definitions (type, label, relation, ...) for an Odoo model."""
    return _execute(model, "fields_get", attributes=SCHEMA_ATTRIBUTES)


@mcp.tool(annotations=READ)
def search_records(
    model: str,
    domain: list[Any] | None = None,
    fields: list[str] | None = None,
    limit: int = 20,
    offset: int = 0,
    order: str | None = None,
) -> list[dict[str, Any]]:
    """Search an Odoo model with a domain and return matching records."""
    kwargs: dict[str, Any] = {"limit": min(limit, MAX_LIMIT), "offset": offset}
    if fields:
        kwargs["fields"] = fields
    if order:
        kwargs["order"] = order
    return _execute(model, "search_read", domain or [], **kwargs)


@mcp.tool(annotations=READ)
def get_record(model: str, record_id: int, fields: list[str] | None = None) -> dict[str, Any]:
    """Read a single record by id."""
    kwargs = {"fields": fields} if fields else {}
    records = _execute(model, "read", [record_id], **kwargs)
    if not records:
        raise ToolError(f"{model} record {record_id} not found")
    return records[0]


@mcp.tool(annotations=WRITE)
def create_record(model: str, values: dict[str, Any]) -> int:
    """[WRITE] Create a record and return its id. Requires ODOO_ALLOW_WRITES=1."""
    _require_writes()
    return _execute(model, "create", values)


@mcp.tool(annotations=WRITE)
def update_record(model: str, record_id: int, values: dict[str, Any]) -> bool:
    """[WRITE] Update fields on an existing record. Requires ODOO_ALLOW_WRITES=1."""
    _require_writes()
    return _execute(model, "write", [record_id], values)


def main() -> None:
    mcp.run("stdio")


if __name__ == "__main__":
    main()
