#!/usr/bin/env bash
# 게시 전 결정형 검사 (스펙 §2.7). 훅 없이 수동 실행 가능.
#   scripts/check-publish.sh                 작업 트리의 추적 파일 전체
#   scripts/check-publish.sh drafts/x.md …   지정 파일(작업 트리)
#   scripts/check-publish.sh --tree <sha>    그 커밋의 트리 전체 (pre-push 가 호출)
# 환경변수 DENYLIST: 기본 <repo>/.denylist. 한 줄 = 패턴<TAB>치환어 — 여기서는 1열만 쓴다.
set -u
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
DENYLIST="${DENYLIST:-$ROOT/.denylist}"
BINARY_EXT='png|jpg|jpeg|gif|webp|svg|ico|pdf|woff|woff2|ttf|otf|zip'
# 내장 패턴 — 공개 무해. <org>/<repo> 형태 GitHub URL 은 OSS 링크와 구분이 안 되므로 .denylist 로.
BUILTIN=(
  '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
  '01[016789]-?[0-9]{3,4}-?[0-9]{4}'
  'git@[A-Za-z0-9.-]+:'
  'https?://gitlab\.'
  '[A-Za-z0-9-]+\.(internal|corp)([/:[:space:]"'"'"']|$)'
  '(^|[^0-9.])(10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3})([^0-9.]|$)'
)

fail=0
say() { printf '%s\n' "$*" >&2; }

mode=work; tree=""
if [ "${1:-}" = "--tree" ]; then mode=tree; tree="${2:?--tree needs a sha}"; shift 2; fi

# 1. 자기 보호 — denylist 부재 = fail-closed
if [ ! -f "$DENYLIST" ]; then say "FAIL: $DENYLIST 없음 (fail-closed). README 의 '.denylist' 절 참고"; exit 1; fi

# 대상 파일 목록
if [ "$mode" = tree ]; then
  mapfile -t files < <(git -C "$ROOT" ls-tree -r --name-only "$tree")
elif [ $# -gt 0 ]; then
  files=("$@")
else
  mapfile -t files < <(git -C "$ROOT" ls-files)
fi

# 1'. 자기 보호 — .denylist 가 대상에 포함되면 거부
for f in "${files[@]}"; do
  if [ "$f" = ".denylist" ] || [ "$(basename "$f")" = ".denylist" ]; then say "FAIL: .denylist 가 트리에 포함됨 — .gitignore 확인"; fail=1; fi
done

# 패턴 목록: denylist 1열 + 내장
patterns=()
while IFS= read -r line || [ -n "$line" ]; do
  line="${line%%$'\r'}"
  case "$line" in ''|'#'*) continue ;; esac
  pat="${line%%$'\t'*}"
  [ -n "$pat" ] && patterns+=("$pat")
done < "$DENYLIST"

content_of() {  # $1 = path
  if [ "$mode" = tree ]; then git -C "$ROOT" show "$tree:$1"; else cat "$ROOT/$1" 2>/dev/null || cat "$1"; fi
}

scanned=0
for f in "${files[@]}"; do
  ext="${f##*.}"; ext="${ext,,}"
  if [[ "$f" == *.* ]] && [[ "$ext" =~ ^($BINARY_EXT)$ ]]; then continue; fi
  scanned=$((scanned+1))
  body=$(content_of "$f") || { say "FAIL: $f 를 읽을 수 없음"; fail=1; continue; }
  for pat in "${patterns[@]}"; do
    hits=$(printf '%s\n' "$body" | grep -Ein -e "$pat") && { printf '%s\n' "$hits" | sed "s|^|$f:|" >&2; fail=1; }
  done
  for pat in "${BUILTIN[@]}"; do
    hits=$(printf '%s\n' "$body" | grep -En -e "$pat") && { printf '%s\n' "$hits" | sed "s|^|$f:|" >&2; fail=1; }
  done
done

if [ "$fail" -ne 0 ]; then say "FAIL: 위 항목을 고친 뒤 다시 시도 (denylist 를 완화하지 않는다)"; exit 1; fi
echo "OK: $scanned files scanned"
