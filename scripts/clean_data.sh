#!/usr/bin/env bash
set -euo pipefail

PROD_DIRS=(
  "data/agent"
  "data/backend"
  "data/judgend"
  "data/mysql"
)

DEV_DIRS=(
  "data-dev/agent"
  "data-dev/backend"
  "data-dev/judgend"
  "data-dev/mysql"
)

echo "⚠️  即将删除以下目录："
echo ""
echo "  生产环境:"
for dir in "${PROD_DIRS[@]}"; do
  echo "    - $dir"
done
echo ""
echo "  开发环境:"
for dir in "${DEV_DIRS[@]}"; do
  echo "    - $dir"
done

echo ""
read -p "确认删除？(y/N): " confirm

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "❌ 已取消"
  exit 0
fi

echo "🧹 开始清理..."

for dir in "${PROD_DIRS[@]}" "${DEV_DIRS[@]}"; do
  if [[ -d "$dir" ]]; then
    echo "➡️  删除: $dir"
    sudo rm -rf "$dir"
  else
    echo "✔️  不存在: $dir"
  fi
done

echo "🎉 清理完成"
