#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${1:-data}"

CONFIG_FILE="agent_config.yaml"
ENV_FILE=".env"

DIRS=(
  "$DATA_DIR/agent"
  "$DATA_DIR/backend"
  "$DATA_DIR/mysql"
  "$DATA_DIR/judgend"
)

AIJLIB_DIR="$DATA_DIR/judgend/testlib"
AIJLIB_REPO="https://github.com/SEUAIG/aijlib.git"

echo "🔍 检查必要文件..."

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "❌ Error: $CONFIG_FILE 不存在"
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ Error: $ENV_FILE 不存在"
  exit 1
fi

echo "✅ 配置文件检查通过"
echo "📁 检查/创建目录 (数据目录: $DATA_DIR)..."

for dir in "${DIRS[@]}"; do
  if [[ ! -d "$dir" ]]; then
    echo "➡️  创建目录: $dir"
    mkdir -p "$dir"
  else
    echo "✔️  已存在: $dir"
  fi
done

echo "✅ 目录检查完成"

# ===== 拉取 aijlib =====
echo "📦 准备 aijlib..."

if [[ -d "$AIJLIB_DIR/.git" ]]; then
  echo "🔄 已存在仓库，执行 git pull..."
  git -C "$AIJLIB_DIR" pull
elif [[ -d "$AIJLIB_DIR" ]]; then
  echo "⚠️  $AIJLIB_DIR 已存在但不是 git 仓库，跳过（请手动处理）"
else
  echo "⬇️  克隆 aijlib..."
  git clone "$AIJLIB_REPO" "$AIJLIB_DIR" --depth 1
fi

echo "🎉 初始化完成"
