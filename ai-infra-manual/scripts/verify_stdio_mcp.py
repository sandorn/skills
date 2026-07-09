#!/usr/bin/env python3
"""
Stdio MCP 服务器快速验证脚本
支持完整的 MCP initialize 握手，兼容 FastMCP 服务器。

用法: python verify_stdio_mcp.py <command> [args...]

示例:
  python verify_stdio_mcp.py npx -y @veldica/publishready-mcp
  python verify_stdio_mcp.py node C:/path/to/server.js
  python verify_stdio_mcp.py npx -y @modelcontextprotocol/server-memory
"""
import subprocess, json, sys, time


def send_and_read(proc, text, timeout=5):
    proc.stdin.write(text + '\n')
    proc.stdin.flush()
    time.sleep(0.5)


def main():
    if len(sys.argv) < 2:
        print('用法: python verify_stdio_mcp.py <command> [args...]')
        sys.exit(1)

    cmd = sys.argv[1:]
    name = cmd[0] if len(cmd) == 1 else f'{cmd[0]} ...'
    use_shell = cmd[0].endswith('.cmd')

    print(f'连接: {name}')
    sys.stdout.flush()

    full_cmd = ' '.join(f'"{c}"' if ' ' in c else c for c in cmd) if use_shell else cmd

    try:
        proc = subprocess.Popen(
            full_cmd if use_shell else cmd,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, shell=use_shell,
        )
    except FileNotFoundError:
        print(f'[FAIL] 命令未找到: {cmd[0]}')
        sys.exit(1)

    time.sleep(2)

    # Step 1: 初始化握手
    print('  -> initialize...')
    init = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                       'params': {'protocolVersion': '2024-11-05', 'capabilities': {},
                                  'clientInfo': {'name': 'verify-stdio-mcp', 'version': '1.0'}}})
    send_and_read(proc, init)
    time.sleep(0.5)

    # Step 2: 通知
    print('  -> notifications/initialized...')
    send_and_read(proc, json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'}))
    time.sleep(0.3)

    # Step 3: 查询工具列表
    print('  -> tools/list...')
    req = json.dumps({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'})
    send_and_read(proc, req)

    try:
        stdout, stderr = proc.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate(timeout=3)
        print('[TIMEOUT]')
        if stderr.strip():
            print(f'stderr: {stderr[:200]}')
        sys.exit(1)

    # 解析响应，优先 tools/list(id=2)
    for line in stdout.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if data.get('id') != 2:
                continue
            tools = data.get('result', {}).get('tools', [])
            print(f'[OK] {len(tools)} tools:')
            for t in tools:
                desc = t.get('description', '')[:80]
                params = list(t.get('inputSchema', {}).get('properties', {}).keys())
                print(f'  - {t["name"]}')
                if params:
                    print(f'    args: {", ".join(params[:5])}')
                if desc:
                    print(f'    {desc}')
            sys.exit(0)
        except json.JSONDecodeError:
            continue

    # Fallback: 兼容不按 id 区分的老服务器
    for line in stdout.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            tools = data.get('result', {}).get('tools', [])
            if tools:
                print(f'[OK] {len(tools)} tools (fallback):')
                for t in tools:
                    print(f'  - {t["name"]}')
                sys.exit(0)
        except json.JSONDecodeError:
            continue

    print(f'[WARN] 未识别响应, stdout({len(stdout)}B): {stdout[:200]}')
    if stderr.strip():
        print(f'stderr({len(stderr)}B): {stderr[:200]}')
    sys.exit(1)


if __name__ == '__main__':
    main()
