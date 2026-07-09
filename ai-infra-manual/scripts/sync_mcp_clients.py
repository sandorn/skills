#!/usr/bin/env python3
"""
Regenerate all client MCP configs from LiteLLM's mcp_servers.

命名规范: LiteLLM 代理 MCP -> {name}_LL (下划线 + _LL 后缀)
原生 stdio MCP 不在此脚本管理。

Run this after ANY change to ~/.litellm/config.yaml MCP section.

Client configs written:
  ~/.claude.json                 (Claude Desktop -> projects.*.mcpServers)
  AppData/Roaming/Code/User/mcp.json  (VS Code)
  ~/.codebuddy/mcp.json        (CodeBuddy - preserves non-_LL entries)
  ~/.continue/config.yaml      (Continue - replaces mcp_servers:, preserves models:)

Usage:
  python sync_mcp_clients.py
"""
import json, os, yaml, copy

HOME = os.path.expanduser('~')
LITELLM_PATH = os.path.join(HOME, '.litellm', 'config.yaml')
CLAUDE_JSON = os.path.join(HOME, '.claude.json')
AUTH = 'Bearer sk-1234'
API_URL = 'http://127.0.0.1:4000'


def get_litellm_mcps():
    with open(LITELLM_PATH, 'r', encoding='utf-8') as f:
        lc = yaml.safe_load(f)
    return sorted(lc.get('mcp_servers', {}).keys())


def build_mcp_entries(litellm_names):
    """key = {name}_LL, url = /mcp/{name}"""
    entries = {}
    for name in litellm_names:
        key = f'{name}_LL'
        entries[key] = {
            'url': f'{API_URL}/mcp/{name}',
            'headers': {'Authorization': AUTH}
        }
    return entries


def build_mcp_servers_dict(entries):
    result = {}
    for key, entry in entries.items():
        result[key] = {
            'type': 'http',
            'url': entry['url'],
            'headers': copy.deepcopy(entry['headers'])
        }
    return result


def write_claude_desktop(entries):
    path = CLAUDE_JSON
    if not os.path.exists(path):
        data = {'projects': {HOME: {'mcpServers': {}}}}
    else:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

    projects = data.get('projects', {})
    mcp_dict = build_mcp_servers_dict(entries)

    if not projects:
        projects[HOME] = {}
    for proj_path in projects:
        if isinstance(projects[proj_path], dict):
            projects[proj_path]['mcpServers'] = mcp_dict
            break

    data['projects'] = projects
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f'[OK] Claude Desktop  -> {path} ({len(entries)} MCP)')


def write_vscode(entries):
    path = os.path.join(HOME, 'AppData', 'Roaming', 'Code', 'User', 'mcp.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    config = {'servers': {}}
    for key, entry in entries.items():
        config['servers'][key] = {
            'type': 'http',
            'url': entry['url'],
            'headers': entry['headers']
        }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f'[OK] VS Code         -> {path} ({len(entries)} MCP)')


def write_codebuddy(entries):
    path = os.path.join(HOME, '.codebuddy', 'mcp.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    extra = {}
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            old = json.load(f)
        for k, v in old.get('mcpServers', {}).items():
            if not k.endswith('_LL'):
                extra[k] = v
    config = {'mcpServers': {}}
    for key, entry in entries.items():
        config['mcpServers'][key] = {
            'type': 'http',
            'url': entry['url'],
            'headers': entry['headers']
        }
    config['mcpServers'].update(extra)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f'[OK] CodeBuddy       -> {path} ({len(entries)} _LL + {len(extra)} native)')


def write_continue(entries):
    path = os.path.join(HOME, '.continue', 'config.yaml')
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.split('\n')
    models_start = None
    for i, line in enumerate(lines):
        if line.strip() == 'models:' and i > 0:
            models_start = i
            break
    if models_start is None:
        models_start = len(lines)
    mcp_lines = ['mcp_servers:']
    for key in sorted(entries.keys()):
        entry = entries[key]
        mcp_lines.append(f'    # LiteLLM proxy: {key}')
        mcp_lines.append(f'    {key}:')
        mcp_lines.append(f'        transport: http')
        mcp_lines.append(f"        url: '{entry['url']}'")
        mcp_lines.append(f'        headers:')
        mcp_lines.append(f"            Authorization: 'Bearer sk-1234'")
        mcp_lines.append(f'        enabled: true')
        mcp_lines.append('')
    new_content = '\n'.join(mcp_lines) + '\n' + '\n'.join(lines[models_start:])
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'[OK] Continue        -> {path} ({len(entries)} MCP, models preserved)')


def main():
    litellm_names = get_litellm_mcps()
    entries = build_mcp_entries(litellm_names)
    print('=== MCP Client Sync ===')
    print(f'LiteLLM MCP count: {len(litellm_names)}')
    print(f'Naming: {{name}}_LL suffix\n')
    write_claude_desktop(entries)
    write_vscode(entries)
    write_codebuddy(entries)
    write_continue(entries)
    print('\nAll 4 clients synced. Restart clients for new MCPs to appear.')


if __name__ == '__main__':
    main()
