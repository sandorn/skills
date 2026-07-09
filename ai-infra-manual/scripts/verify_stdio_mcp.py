#!/usr/bin/env python3
"""
Stdio MCP 服务器快速验证脚本
用法: python verify_stdio_mcp.py <command> [args...]

示例:
  python verify_stdio_mcp.py npx -y @veldica/publishready-mcp
  python verify_stdio_mcp.py node C:/path/to/server.js
"""
import subprocess, json, sys, time

def main():
    if len(sys.argv) < 2:
        print("用法: python verify_stdio_mcp.py <command> [args...]")
        sys.exit(1)

    cmd = sys.argv[1:]
    name = cmd[0] if len(cmd) == 1 else f"{cmd[0]} ..."
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

    req = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}) + '\n'

    try:
        stdout, stderr = proc.communicate(input=req, timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate(timeout=3)
        print(f'[TIMEOUT]')
        if stderr.strip(): print(f'stderr: {stderr[:200]}')
        sys.exit(1)

    # 解析 JSON-RPC
    for line in stdout.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            tools = data.get('result', {}).get('tools', [])
            print(f'[OK] {len(tools)} tools:')
            for t in tools:
                desc = t.get('description', '')[:80]
                params = list(t.get('inputSchema', {}).get('properties', {}).keys())
                print(f'  - {t["name"]}')
                if params: print(f'    args: {", ".join(params[:5])}')
                if desc: print(f'    {desc}')
            sys.exit(0)
        except json.JSONDecodeError:
            continue

    print(f'[WARN] 未识别响应, stdout: {stdout[:200]}')
    if stderr.strip(): print(f'stderr: {stderr[:200]}')
    sys.exit(1)

if __name__ == '__main__':
    main()
