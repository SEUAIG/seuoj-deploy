#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${1:-data}"

CONFIG_DIR="config"
AGENT_CONFIG_FILE="$CONFIG_DIR/agent_config.yaml"
PROMPTS_CONFIG_FILE="$CONFIG_DIR/prompts.yaml"
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

if [[ ! -f "$AGENT_CONFIG_FILE" ]]; then
  echo "❌ Error: $AGENT_CONFIG_FILE 不存在"
  exit 1
fi

if [[ ! -f "$PROMPTS_CONFIG_FILE" ]]; then
  echo "❌ Error: $PROMPTS_CONFIG_FILE 不存在"
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

echo "🎉 初始化完成"
