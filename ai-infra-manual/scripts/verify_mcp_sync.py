#!/usr/bin/env python3
"""
Verify MCP sync: Hermes config.yaml vs LiteLLM config.yaml.

命名规范:
  - LiteLLM HTTP proxy -> Hermes key = {name}_LL (strip _LL to compare)
  - Hermes native stdio -> no suffix, not compared against LiteLLM

Run after ANY LiteLLM config change to detect orphans and missing entries.
"""
import yaml, os, sys

HOME = os.path.expanduser('~')
LITELLM_PATH = os.path.join(HOME, '.litellm', 'config.yaml')
HERMES_PATH = os.path.join(HOME, '.hermes', 'config.yaml')


def load(path, label):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f'[ERROR] {label}: {path} not found')
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f'[ERROR] {label}: YAML parse error\n{e}')
        sys.exit(1)


def main():
    lc = load(LITELLM_PATH, 'LiteLLM')
    hc = load(HERMES_PATH, 'Hermes')

    litellm_names = set(lc.get('mcp_servers', {}).keys())
    hermes_mcp = hc.get('mcp_servers', {})

    # 分离: _LL 后缀=HTTP proxy, 无后缀=原生 stdio
    hermes_proxy = {}
    hermes_native = {}
    for k in hermes_mcp:
        if k.endswith('_LL'):
            hermes_proxy[k[:-3]] = k
        else:
            hermes_native[k] = True

    proxy_stripped = set(hermes_proxy.keys())
    missing = litellm_names - proxy_stripped
    orphans = proxy_stripped - litellm_names

    print('=== MCP Sync Audit ===')
    print(f'LiteLLM MCP:         {len(litellm_names)}')
    print(f'Hermes HTTP proxy:   {len(hermes_proxy)}')
    print(f'Hermes native stdio: {len(hermes_native)}')
    for n in sorted(hermes_native):
        print(f'  - {n}')

    if missing:
        print(f'\n  MISSING from Hermes ({len(missing)}):')
        for n in sorted(missing):
            print(f'  -> {n}_LL  (url: /mcp/{n})')
            print(f'    Add to config:')
            print(f'      {n}_LL:')
            print(f"        url: 'http://127.0.0.1:4000/mcp/{n}'")
            print(f"        headers: {{'Authorization': 'Bearer sk-1234'}}")
            print(f'        enabled: true')
            print()

    if orphans:
        print(f'\n  ORPHANED in Hermes (no longer in LiteLLM) ({len(orphans)}):')
        for n in sorted(orphans):
            print(f'  -> {hermes_proxy[n]}  (remove from config.yaml)')
        print()

    if not missing and not orphans:
        print(f'\n  IN SYNC — all {len(litellm_names)} LiteLLM MCPs matched.')
    else:
        print(f'--- Run `hermes mcp list` after fixing ---')

    common = litellm_names & proxy_stripped
    print(f'\nIn sync:  {len(common)}/{len(litellm_names)}')
    print(f'Missing:  {len(missing)}')
    print(f'Orphaned: {len(orphans)}')


if __name__ == '__main__':
    main()
