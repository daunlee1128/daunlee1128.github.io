#!/usr/bin/env bash
# 로컬 빌드. repo를 임시 디렉터리에 복사한 뒤(옵션: drafts/samples/ 병합) jekyll build → <repo>/_site
# usage: scripts/dev-build.sh [--with-samples]
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if ! command -v bundle >/dev/null 2>&1; then echo "SKIP: bundle not found (Task 0 참고)"; exit 3; fi
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
rsync -a --exclude .git --exclude _site --exclude .jekyll-cache --exclude drafts "$ROOT/" "$TMP/"
if [ "${1:-}" = "--with-samples" ] && [ -d "$ROOT/drafts/samples" ]; then
  rsync -a "$ROOT/drafts/samples/" "$TMP/"
fi
( cd "$TMP" && BUNDLE_GEMFILE="$ROOT/Gemfile" bundle exec jekyll build -s "$TMP" -d "$ROOT/_site" --quiet )
echo "OK: built to $ROOT/_site ($(find "$ROOT/_site" -name '*.html' | wc -l) html files)"
