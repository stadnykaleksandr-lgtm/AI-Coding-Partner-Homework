# Research Notes — context7 Queries

## Query 1: Python decimal module for monetary arithmetic

- **Search**: "Python decimal module monetary arithmetic ROUND_HALF_UP"
- **context7 library ID**: `/python/decimal`
- **Applied**: Used `decimal.Decimal` throughout all agents instead of `float` for amount handling. Used `Decimal(str(value))` pattern when converting from JSON strings to avoid float precision loss. The `InvalidOperation` exception from `decimal` module is caught in the validator to handle malformed amount strings.

Key pattern applied:
```python
from decimal import Decimal, InvalidOperation

try:
    amount = Decimal(str(data["amount"]))
    if amount <= 0:
        raise ValueError("Amount must be positive")
except (InvalidOperation, ValueError):
    # reject transaction
```

---

## Query 2: fastmcp Python MCP server framework

- **Search**: "fastmcp Python MCP server tools resources"
- **context7 library ID**: `/jlowin/fastmcp`
- **Applied**: Used `fastmcp` to build `mcp/server.py`. Key patterns:
  - `FastMCP(name)` to create the server instance
  - `@mcp.tool()` decorator to expose callable tools
  - `@mcp.resource("pipeline://summary")` decorator to expose a readable resource
  - `mcp.run()` to start the server

Key pattern applied:
```python
from fastmcp import FastMCP

mcp = FastMCP("pipeline-status")

@mcp.tool()
def get_transaction_status(transaction_id: str) -> dict:
    ...

@mcp.resource("pipeline://summary")
def pipeline_summary() -> str:
    ...

if __name__ == "__main__":
    mcp.run()
```

---

## Query 3: Python pathlib for file-based message passing

- **Search**: "Python pathlib file glob JSON message queue"
- **context7 library ID**: `/python/pathlib`
- **Applied**: Used `Path` throughout for cross-platform file operations. Used `Path.mkdir(parents=True, exist_ok=True)` for directory setup, and `Path.glob("*.json")` pattern for scanning result files in the MCP server.
