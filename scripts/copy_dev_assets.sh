#!/usr/bin/env bash
set -euo pipefail

# 开发环境种子数据重置脚本
# 每次 make dev_run 调用，将 seed 数据拷贝到 data-dev/ 并重置 MySQL 数据

DEV_DATA="data-dev"

echo "🔄 重置开发环境数据 ($DEV_DATA)..."

# --- 重置 MySQL 数据（触发 init 脚本重新执行） ---
MYSQL_DIR="$DEV_DATA/mysql"
if [[ -d "$MYSQL_DIR" ]]; then
  echo "🗑️  清空 MySQL 数据: $MYSQL_DIR"
  sudo rm -rf "$MYSQL_DIR"
fi
mkdir -p "$MYSQL_DIR"
echo "✅ MySQL 数据目录已重置"

# --- judgend 种子数据 ---
JUDGE_SRC="data/judgend-seed"
JUDGE_DST="$DEV_DATA/judgend"

if [[ ! -d "$JUDGE_SRC" ]]; then
  echo "❌ Error: $JUDGE_SRC 不存在"
  exit 1
fi

mkdir -p "$JUDGE_DST"

if compgen -G "$JUDGE_SRC/*" > /dev/null; then
  cp -r "$JUDGE_SRC"/* "$JUDGE_DST"/
  echo "✅ judgend 资源拷贝完成: $JUDGE_SRC -> $JUDGE_DST"
else
  echo "⚠️  $JUDGE_SRC 为空，跳过拷贝"
fi

# --- agentend 种子数据 ---
AGENT_SRC="data/agent-seed"
AGENT_DST="$DEV_DATA/agent"

if [[ -d "$AGENT_SRC" ]]; then
  mkdir -p "$AGENT_DST"
  if compgen -G "$AGENT_SRC/*" > /dev/null; then
    cp -r "$AGENT_SRC"/* "$AGENT_DST"/
    echo "✅ agentend 资源拷贝完成: $AGENT_SRC -> $AGENT_DST"
  else
    echo "⚠️  $AGENT_SRC 为空，跳过拷贝"
  fi
else
  echo "⚠️  $AGENT_SRC 不存在，跳过 agentend 种子数据拷贝"
fi

# --- backend 种子数据 (user-code) ---
BACKEND_CODE_SRC="data/backend-seed/user-code"
BACKEND_CODE_DST="$DEV_DATA/backend/data/user-code"

if [[ -d "$BACKEND_CODE_SRC" ]]; then
  mkdir -p "$BACKEND_CODE_DST"
  if compgen -G "$BACKEND_CODE_SRC/*" > /dev/null; then
    cp -r "$BACKEND_CODE_SRC"/* "$BACKEND_CODE_DST"/
    echo "✅ backend user-code 种子拷贝完成: $BACKEND_CODE_SRC -> $BACKEND_CODE_DST"
  else
    echo "⚠️  $BACKEND_CODE_SRC 为空，跳过拷贝"
  fi
else
  echo "⚠️  $BACKEND_CODE_SRC 不存在，跳过 backend 种子数据拷贝"
fi

echo "🎉 开发环境数据重置完成"
