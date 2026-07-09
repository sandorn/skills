#!/usr/bin/env python3
"""
Verify MCP sync: Hermes config.yaml vs LiteLLM config.yaml.
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
        print(f"[ERROR] {label}: {path} not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"[ERROR] {label}: YAML parse error\n{e}")
        sys.exit(1)

def main():
    lc = load(LITELLM_PATH, 'LiteLLM')
    hc = load(HERMES_PATH, 'Hermes')

    litellm_names = set(lc.get('mcp_servers', {}).keys())

    hermes_mcp = hc.get('mcp_servers', {})
    hermes_stripped = {}
    for k in hermes_mcp:
        if k.endswith('_LL'):
            name = k[:-3]
        else:
            name = k
        hermes_stripped[name] = k

    hermes_names = set(hermes_stripped.keys())
    missing = litellm_names - hermes_names
    orphans = hermes_names - litellm_names

    print(f"=== MCP Sync Audit ===")
    print(f"LiteLLM MCP:  {len(litellm_names)}")
    print(f"Hermes MCP:   {len(hermes_names)}")

    if missing:
        print(f"\n  MISSING from Hermes ({len(missing)}):")
        for n in sorted(missing):
            print(f"  -> {n}_LL  (url: /mcp/{n})")

    if orphans:
        print(f"\n  ORPHANED in Hermes ({len(orphans)}):")
        for n in sorted(orphans):
            print(f"  -> {hermes_stripped[n]}  (remove)")

    if not missing and not orphans:
        print(f"\n  IN SYNC - all {len(litellm_names)} MCPs matched.")
    else:
        print(f"\n  Fix and run `hermes mcp list` to verify.")

    common = litellm_names & hermes_names
    print(f"\nIn sync: {len(common)}/{len(litellm_names)}")
    print(f"Missing: {len(missing)}, Orphaned: {len(orphans)}")

if __name__ == '__main__':
    main()
