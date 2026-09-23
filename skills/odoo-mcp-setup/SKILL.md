---
name: odoo-mcp-setup
description: Set up the Solidum Odoo MCP server (odoo-mcp) in Cursor, Grok Bot or any other stdio MCP client. Use when the user asks how to connect Odoo, which environment variables are needed, how to enable write tools, or why the odoo tools fail to start.
---

# Odoo MCP setup

The server is a Python stdio MCP server. It talks to Odoo over XML-RPC and runs through `uvx`, so [uv](https://docs.astral.sh/uv/) must be installed.

## Environment variables

| Variable | Required | Notes |
|---|---|---|
| `ODOO_URL` | yes | e.g. `https://mycompany.odoo.com` |
| `ODOO_DB` | yes | Database name |
| `ODOO_USERNAME` | yes | Login of the Odoo user |
| `ODOO_API_KEY` | one of | Preferred. Odoo: Preferences → Account Security → New API Key |
| `ODOO_PASSWORD` | one of | Only used if `ODOO_API_KEY` is unset |
| `ODOO_ALLOW_WRITES` | no | `1` enables `create_record` and `update_record`. Anything else keeps the server read-only. |

Recommendations:

- Use a dedicated Odoo user for the bot with only the access rights it needs (e.g. Accounting / Billing, not Settings).
- Start read-only. Turn on `ODOO_ALLOW_WRITES=1` only after the read results look right, ideally on a staging database first.
- Keep the key in the shell environment, a local `.env` (git-ignored) or a secret manager. Never paste it into chat, commits or shared configs.

## Cursor

Installed as a plugin, the server reads the `ODOO_*` variables from the environment Cursor was started with.

Manual setup in `~/.cursor/mcp.json` or `.cursor/mcp.json`:

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

## Grok Bot and other MCP clients

Any client that can start a stdio MCP server works. Register a stdio server (in Grok Bot via AddMcpServer with stdio transport) with:

- command: `uvx`
- args: `--from git+https://github.com/bethesna-dev/odoo-mcp odoo-mcp`
- env: the `ODOO_*` variables above

If the client cannot inject env vars safely, point it at a small wrapper script that exports the variables from your own secret store and then runs `exec uvx --from git+https://github.com/bethesna-dev/odoo-mcp odoo-mcp`. Keep that wrapper out of version control if it references private paths.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `Missing Odoo configuration: ...` | One of `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_API_KEY` / `ODOO_PASSWORD` is not set in the client's environment |
| Authentication failed | Wrong database name, username, or an expired / revoked API key |
| `Write tools are disabled` | `ODOO_ALLOW_WRITES` is not exactly `1` |
| Access error on a model | The Odoo user lacks rights for that model |
| `uvx: command not found` | uv not installed or not on the client's `PATH` |

Test the connection with a harmless read: `list_models(name_filter="account.move")`.

Need help beyond the connector (Odoo customising, integrations, an inherited setup)? Solidum builds and maintains this plugin: https://solidum.tech
