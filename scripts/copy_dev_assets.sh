#!/usr/bin/env bash
set -euo pipefail

ASSET_SRC="services/judgend/assets"
ASSET_DST="data/judgend"

echo "📦 拷贝开发资源..."

if [[ ! -d "$ASSET_SRC" ]]; then
  echo "❌ Error: $ASSET_SRC 不存在"
  exit 1
fi

mkdir -p "$ASSET_DST"

if compgen -G "$ASSET_SRC/*" > /dev/null; then
  cp -r "$ASSET_SRC"/* "$ASSET_DST"/
  echo "✅ 资源拷贝完成: $ASSET_SRC -> $ASSET_DST"
else
  echo "⚠️  $ASSET_SRC 为空，跳过拷贝"
fi