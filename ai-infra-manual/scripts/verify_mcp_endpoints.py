#!/usr/bin/env python3
"""
Verify LiteLLM MCP endpoint connectivity via Streamable HTTP (SSE).

Tests every MCP server registered in LiteLLM by sending a JSON-RPC
tools/list request to its /mcp/<name> endpoint.
Reports reachable, unreachable, and summary stats.

Usage:
    python scripts/verify_mcp_endpoints.py

Exit code: 0 if all OK, 1 if any endpoint failed.
"""
import json
import sys
import urllib.error
import urllib.request

LITELLM_BASE = 'http://127.0.0.1:4000'
AUTH_HEADER = 'Bearer sk-1234'

# All MCP endpoints registered in LiteLLM (~/.litellm/config.yaml mcp_servers)
MCP_ENDPOINTS = [
    'context7',
    'playwright',
    'github',
    'filesystem',
    'firecrawl',
    'windows_admin',
    'yaml_lint',
    'officecli',
    'git',
    'sequential_thinking',
    'pandoc',
    'litellm_admin',
    'memory_official',
]


def test_endpoint(name: str) -> tuple[bool, str]:
    """Send JSON-RPC tools/list to a MCP endpoint. Returns (ok, detail)."""
    url = f'{LITELLM_BASE}/mcp/{name}'
    headers = {
        'Authorization': AUTH_HEADER,
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
    }
    body = json.dumps({
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'tools/list',
        'params': {},
    }).encode()

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method='POST')
        resp = urllib.request.urlopen(req, timeout=8)
        ct = resp.headers.get('Content-Type', '') or ''
        rbody = resp.read()

        if 'text/event-stream' in ct:
            return True, f'SSE stream ({len(rbody)} bytes, handshake OK)'
        elif 'json' in ct:
            try:
                data = json.loads(rbody)
                tools = data.get('result', {}).get('tools', [])
                return True, f'{len(tools)} tools discovered'
            except json.JSONDecodeError:
                return True, f'HTTP {resp.status} ({ct}, non-JSON body)'
        else:
            return True, f'HTTP {resp.status} ({ct})'
    except urllib.error.HTTPError as e:
        return False, f'HTTP {e.code} {e.reason}'
    except urllib.error.URLError as e:
        return False, f'Connection failed: {e.reason}'
    except OSError as e:
        return False, str(e)


def main():
    print('=' * 60)
    print('LiteLLM MCP Endpoint Connectivity Check')
    print(f'Base: {LITELLM_BASE}')
    print('=' * 60)

    # Step 1: LiteLLM gateway health
    try:
        req = urllib.request.Request(f'{LITELLM_BASE}/health/readiness', method='GET')
        urllib.request.urlopen(req, timeout=3)
        print('\n[OK] LiteLLM gateway is running')
    except Exception as e:
        print(f'\n[FAIL] LiteLLM gateway is DOWN: {e}')
        print('Start LiteLLM first, then re-run this script.')
        sys.exit(1)

    # Step 2: Test each MCP endpoint
    print(f'\nTesting {len(MCP_ENDPOINTS)} MCP endpoints...\n')
    results = []
    for name in MCP_ENDPOINTS:
        ok, detail = test_endpoint(name)
        icon = '[OK]' if ok else '[FAIL]'
        print(f'  {icon} {name:<26s} {detail}')
        results.append((name, ok, detail))

    # Step 3: Summary
    ok_count = sum(1 for _, ok, _ in results if ok)
    fail_count = len(results) - ok_count
    print(f'\n{"=" * 60}')
    print(f'Summary: {ok_count} OK, {fail_count} FAIL (of {len(results)} total)')
    print(f'{"=" * 60}')

    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
