#!/usr/bin/env bash
"""每日自动备份 — 打包正文/设定/大纲/追踪，保留最近7天。

配置方式（根据项目路径修改 PROJECT_ROOT）：
    0 3 * * * bash scripts/auto_backup.sh

该脚本由 cronjob 每日本地时间凌晨3点执行。
备份文件路径：{PROJECT_ROOT}/.writer/backups/YYYY-MM-DD.tar.gz
"""

import os, sys, tarfile, shutil, glob
from datetime import datetime, timedelta
from pathlib import Path


# ⚠️ 修改此行指向实际项目根目录
PROJECT_ROOT = "D:/Writer/重生2001：传奇带进现实"

BACKUP_DIR = os.path.join(PROJECT_ROOT, ".writer", "backups")
RETENTION_DAYS = 7


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


def create_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)

    date_str = datetime.now().strftime('%Y-%m-%d')
    backup_file = os.path.join(BACKUP_DIR, f'{date_str}.tar.gz')

    if os.path.exists(backup_file):
        print(f"⏭️  今日备份已存在: {backup_file}")
        return

    # 收集要备份的文件
    base = Path(PROJECT_ROOT)
    files_to_backup = []
    total_size = 0

    for f in base.rglob('*'):
        if not f.is_file():
            continue
        rel = str(f.relative_to(base))
        if should_include(rel):
            files_to_backup.append((str(f), rel))
            total_size += f.stat().st_size

    # 创建 tar.gz
    with tarfile.open(backup_file, 'w:gz') as tar:
        for full_path, rel_path in files_to_backup:
            tar.add(full_path, arcname=rel_path)

    size_mb = total_size / 1024 / 1024
    archive_mb = os.path.getsize(backup_file) / 1024 / 1024
    print(f"✅ 备份完成: {backup_file}")
    print(f"   {len(files_to_backup)} 文件 ({size_mb:.1f} MB → {archive_mb:.1f} MB)")

    # 清理过期备份
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    for old in sorted(glob.glob(os.path.join(BACKUP_DIR, '*.tar.gz'))):
        old_date_str = os.path.basename(old).replace('.tar.gz', '')
        try:
            old_date = datetime.strptime(old_date_str, '%Y-%m-%d')
            if old_date < cutoff:
                os.remove(old)
                print(f"🗑️  清理过期: {os.path.basename(old)}")
        except ValueError:
            pass  # 文件名不符合日期格式，跳过

    print(f"💾 当前备份数: {len(glob.glob(os.path.join(BACKUP_DIR, '*.tar.gz')))}")
    print(f"📁 备份目录: {BACKUP_DIR}")


if __name__ == '__main__':
    create_backup()
