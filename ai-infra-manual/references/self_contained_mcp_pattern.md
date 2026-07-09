# Self-Contained MCP Pattern for Skill Development
## Overview
This implementation packages custom, skill-exclusive MCP services directly inside the skill directory, eliminating dependencies on global LiteLLM/Hermes configs and enabling fully portable, zero-config deployment of skills with custom MCP backend logic.

## Directory Structure
```
<skill-root>/
├─ mcp/                      # Skill-exclusive MCP services
│  ├─ <mcp-1>/              # First custom MCP service
│  │  └─ <server-file>
│  └─ <mcp-2>/              # Second custom MCP service
│     └─ <server-file>
├─ scripts/mcp_utils.py     # Dynamic MCP registration utility
└─ .env                     # MCP API credentials and configuration
```

## Dynamic Registration Flow
1. Any entry script in the skill imports `ensure_mcps_ready()` from `mcp_utils.py` on launch
2. The utility checks if required MCPs are already registered in the current Hermes session
3. If not registered, automatically registers them using skill-local MCP paths
4. MCPs are registered with session-only scope: automatically cleaned up when Hermes restarts, no global configuration pollution

## Key Benefits
- ✅ 100% self-contained skill: no external dependencies, copy the single directory to deploy to any Hermes instance
- ✅ Zero global config changes: no need to modify LiteLLM `config.yaml` or Hermes system settings
- ✅ On-demand resource usage: MCP processes only started when the skill is used, automatically idle-reaped by Hermes
- ✅ Version synced: MCP code is tracked with the rest of the skill in Git, eliminates version mismatch issues
- ✅ Environment isolation: MCPs read credentials from skill-local `.env`, no conflict with global environment variables

## Troubleshooting
- Registration errors: ensure Node.js/Python dependencies are installed for each MCP service
- API errors: verify API keys and endpoint configuration in the skill root `.env` file are valid
- Path errors: always use relative paths resolved via `Path(__file__)` instead of hardcoded absolute paths to keep the skill portable

## Pitfall Avoidance
🚫 Do not hardcode absolute paths to MCPs outside the skill directory, always resolve paths relative to the skill root for cross-machine portability.
