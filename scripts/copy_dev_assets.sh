#!/usr/bin/env bash
set -euo pipefail

echo "📦 拷贝开发资源..."

# --- judgend 种子数据 ---
JUDGE_SRC="data/judgend-seed"
JUDGE_DST="data/judgend"

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
AGENT_DST="data/agent"

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