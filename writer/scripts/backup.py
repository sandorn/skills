#!/usr/bin/env python3
"""每日自动备份 — 打包 chapters/setting/outline/tracking，保留最近7天。

用法：
    python3 scripts/backup.py <项目根目录> [--retention DAYS]

配置 cron：
    0 3 * * * cd /path/to/project && python3 scripts/backup.py .

该脚本由 cronjob 每日本地时间凌晨3点执行。
备份文件路径：{project_root}/.writer/backups/YYYY-MM-DD.tar.gz
"""

import os
import sys
import tarfile
import glob
import argparse
from datetime import datetime, timedelta
from pathlib import Path


def should_include(name):
    """备份过滤：只备份核心写作文件"""
    exclude_patterns = [
        '.writer/backups',
        '.writer/facts.db-journal',
        '.writer/runtime',
        'node_modules',
        '.git',
        '__pycache__',
        '.venv',
        '.pytest_cache',
    ]
    for pat in exclude_patterns:
        if pat in name.replace('\\', '/'):
            return False
    return True


def create_backup(project_root, retention_days=7):
    project_root = os.path.abspath(project_root)
    if not os.path.isdir(project_root):
        print(f"❌ 项目目录不存在: {project_root}")
        sys.exit(1)

    backup_dir = os.path.join(project_root, ".writer", "backups")
    os.makedirs(backup_dir, exist_ok=True)

    date_str = datetime.now().strftime('%Y-%m-%d')
    backup_file = os.path.join(backup_dir, f'{date_str}.tar.gz')

    if os.path.exists(backup_file):
        print(f"⏭️  今日备份已存在: {backup_file}")
        return

    # 收集要备份的文件
    base = Path(project_root)
    files_to_backup = []
    total_size = 0

    for f in base.rglob('*'):
        if not f.is_file():
            continue
        rel = str(f.relative_to(base))
        if should_include(rel):
            files_to_backup.append((str(f), rel))
            total_size += f.stat().st_size

    if not files_to_backup:
        print(f"⚠️  项目目录无文件: {project_root}")
        return

    # 创建 tar.gz
    with tarfile.open(backup_file, 'w:gz') as tar:
        for full_path, rel_path in files_to_backup:
            tar.add(full_path, arcname=rel_path)

    size_mb = total_size / 1024 / 1024
    archive_mb = os.path.getsize(backup_file) / 1024 / 1024
    print(f"✅ 备份完成: {backup_file}")
    print(f"   {len(files_to_backup)} 文件 ({size_mb:.1f} MB → {archive_mb:.1f} MB)")

    # 清理过期备份
    cutoff = datetime.now() - timedelta(days=retention_days)
    for old in sorted(glob.glob(os.path.join(backup_dir, '*.tar.gz'))):
        old_date_str = os.path.basename(old).replace('.tar.gz', '')
        try:
            old_date = datetime.strptime(old_date_str, '%Y-%m-%d')
            if old_date < cutoff:
                os.remove(old)
                print(f"🗑️  清理过期: {os.path.basename(old)}")
        except ValueError:
            pass  # 文件名不符合日期格式，跳过

    remaining = glob.glob(os.path.join(backup_dir, '*.tar.gz'))
    print(f"💾 当前备份数: {len(remaining)}")
    print(f"📁 备份目录: {backup_dir}")


def main():
    parser = argparse.ArgumentParser(
        description='Writer 项目每日自动备份',
        epilog='示例: python3 scripts/backup.py . --retention 14'
    )
    parser.add_argument(
        'project_root',
        help='项目根目录路径（包含 writer.json 或 setting/ + chapters/）'
    )
    parser.add_argument(
        '--retention', type=int, default=7,
        help='备份保留天数（默认: 7）'
    )
    args = parser.parse_args()
    create_backup(args.project_root, args.retention)


if __name__ == '__main__':
    main()
