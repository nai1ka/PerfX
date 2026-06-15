#!/usr/bin/env bash
set -euo pipefail

REGISTRY="${1:-}"
if [[ -z "$REGISTRY" ]]; then
  echo "Usage: $0 <dockerhub-username>"
  exit 1
fi

PLATFORM="${2:-linux/amd64}"   # override with e.g. "linux/amd64,linux/arm64"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

declare -A IMAGES=(
  [perfx-postgres]="$ROOT/Backend/postgres"
  [perfx-clickhouse]="$ROOT/Backend/clickhouse"
  [perfx-backend]="$ROOT/Backend/app"
  [perfx-frontend]="$ROOT/Frontend"
  [perfx-detector]="$ROOT/Analysis"
)

# Ensure a buildx builder capable of cross-platform builds exists
if ! docker buildx inspect perfx-builder &>/dev/null; then
  echo "==> Creating buildx builder"
  docker buildx create --name perfx-builder --use
else
  docker buildx use perfx-builder
fi

echo "==> Logging in to Docker Hub"
docker login

echo "==> Building and pushing images (platform: $PLATFORM)"
for name in "${!IMAGES[@]}"; do
  echo "--- $name"
  docker buildx build \
    --platform "$PLATFORM" \
    --push \
    -t "$REGISTRY/$name" \
    "${IMAGES[$name]}"
done

echo "==> Done. Images available at:"
for name in "${!IMAGES[@]}"; do
  echo "    docker.io/$REGISTRY/$name"
done
