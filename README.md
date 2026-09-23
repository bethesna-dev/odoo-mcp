# Solidum Odoo Connector

A Cursor marketplace plugin plus a Python stdio [MCP](https://modelcontextprotocol.io) server that connects Cursor (or any MCP client) to an Odoo instance over XML-RPC.

## Tools

| Tool | Kind | What it does |
|---|---|---|
| `list_models` | read | List installed models (optional name filter) |
| `get_model_schema` | read | Field definitions for a model (`fields_get`) |
| `search_records` | read | `search_read` with an Odoo domain; limit capped at 200 |
| `get_record` | read | Read one record by id |
| `create_record` | **write** | Create a record; returns the new id |
| `update_record` | **write** | Update fields on a record |

Write tools are always listed but refuse to run unless `ODOO_ALLOW_WRITES=1`. The tools don't expose deletes or arbitrary method calls.

## Configuration

| Variable | Required | Notes |
|---|---|---|
| `ODOO_URL` | yes | e.g. `https://mycompany.odoo.com` |
| `ODOO_DB` | yes | Database name |
| `ODOO_USERNAME` | yes | Login of the Odoo user |
| `ODOO_API_KEY` | one of | Preferred. Create one under *Preferences → Account Security → New API Key* |
| `ODOO_PASSWORD` | one of | Used only if `ODOO_API_KEY` is unset |
| `ODOO_ALLOW_WRITES` | no | Set to `1` to enable `create_record` / `update_record` |

Keep credentials in your shell environment or a local `.env` (git-ignored). Don't commit them.

## Install in Cursor

### As a plugin

The repo is a Cursor plugin (`.cursor-plugin/plugin.json`) and a single-plugin marketplace (`.cursor-plugin/marketplace.json`). The plugin registers the MCP server from [`mcp.json`](mcp.json). The server runs through `uvx`, so you need [uv](https://docs.astral.sh/uv/) installed. It reads the `ODOO_*` variables from the environment Cursor was launched with.

### Manual `mcp.json`

Add this to `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project):

```json
{
  "mcpServers": {
    "odoo": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/bethesna-dev/odoo-mcp", "odoo-mcp"],
      "env": {
        "ODOO_URL": "https://mycompany.odoo.com",
        "ODOO_DB": "mycompany",
        "ODOO_USERNAME": "bot@mycompany.com",
        "ODOO_API_KEY": "${env:ODOO_API_KEY}"
      }
    }
  }
}
```

For a local checkout, use `"command": "uv", "args": ["run", "--directory", "/path/to/odoo-mcp", "odoo-mcp"]`.

## Development

```bash
uv run --group dev pytest   # unit tests, Odoo RPC is mocked
uv run odoo-mcp             # start the stdio server (needs ODOO_* env)
```

Layout:

- `src/odoo_mcp/client.py`: env config and a thin XML-RPC client (stdlib `xmlrpc.client`)
- `src/odoo_mcp/server.py`: MCP tool definitions (`mcp` SDK 2.x `MCPServer`)
- `tests/`: tests that mock the XML-RPC proxies; no live Odoo needed

## License

MIT
