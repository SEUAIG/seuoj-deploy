#!/usr/bin/env bash
set -euo pipefail

TARGET_DIRS=(
  "data/agent"
  "data/backend"
  "data/judgend"
  "data/mysql"
)

echo "⚠️  即将删除以下目录："
for dir in "${TARGET_DIRS[@]}"; do
  echo "  - $dir"
done

read -p "确认删除？(y/N): " confirm

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "❌ 已取消"
  exit 0
fi

echo "🧹 开始清理..."

for dir in "${TARGET_DIRS[@]}"; do
  if [[ -d "$dir" ]]; then
    echo "➡️  删除: $dir"
    sudo rm -rf "$dir"
  else
    echo "✔️  不存在: $dir"
  fi
done

echo "🎉 清理完成"