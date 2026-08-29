#!/usr/bin/env bash
# 게시 전 결정형 검사 (스펙 §2.7). 훅 없이 수동 실행 가능.
#   scripts/check-publish.sh                 작업 트리의 추적 파일 전체
#   scripts/check-publish.sh drafts/x.md …   지정 파일(작업 트리)
#   scripts/check-publish.sh --tree <sha>    그 커밋의 트리 전체
#   scripts/check-publish.sh --range <범위>  그 범위에서 닿는 모든 blob (pre-push 가 호출)
#     <범위> 는 git rev-list 가 받는 것이면 무엇이든. 예) "a..b", "b --not --remotes".
#     공백이 들어갈 수 있으므로 rev-list 에 넘길 때 일부러 따옴표 없이 쓴다(단어 분리 의도).
#     팁 트리만 보면 뒤 커밋에서 지운 파일이 이력으로 새어 나가므로 범위 전체의 blob 을 본다.
# 환경변수 DENYLIST: 기본 <repo>/.denylist. 한 줄 = 패턴<TAB>치환어 — 여기서는 1열만 쓴다.
# 환경변수 ALLOWLIST: 기본 <repo>/.allowlist. 한 줄 = 리터럴 부분 문자열(정규식 아님).
set -u
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
DENYLIST="${DENYLIST:-$ROOT/.denylist}"
ALLOWLIST="${ALLOWLIST:-$ROOT/.allowlist}"
BINARY_EXT='png|jpg|jpeg|gif|webp|svg|ico|pdf|woff|woff2|ttf|otf|zip'
MASK='⟨allow⟩'
# 내장 패턴 — 공개 무해. <org>/<repo> 형태 GitHub URL 은 OSS 링크와 구분이 안 되므로 .denylist 로.
# 이 배열은 건드리지 않는다. 오탐(예: 4자리 버전 문자열)은 .allowlist 로 그 리터럴만 면제한다.
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

mode=work; tree=""; range=""
if [ "${1:-}" = "--tree" ]; then mode=tree; tree="${2:?--tree needs a sha}"; shift 2
elif [ "${1:-}" = "--range" ]; then mode=range; range="${2:?--range needs a rev-range}"; shift 2; fi

# 1. 자기 보호 — denylist 부재 = fail-closed
if [ ! -f "$DENYLIST" ]; then say "FAIL: $DENYLIST 없음 (fail-closed). README 의 '.denylist' 절 참고"; exit 1; fi

# 대상 파일 목록 — files[i] 는 보고/이진 판정용 경로, range 모드에서는 blobs[i] 가 내용 출처
files=(); blobs=()
if [ "$mode" = tree ]; then
  if ! listing=$(git -C "$ROOT" ls-tree -r --name-only "$tree" 2>&1); then
    say "FAIL: git ls-tree 실패 ($tree)"; say "$listing"; exit 1
  fi
  [ -n "$listing" ] && mapfile -t files <<<"$listing"
elif [ "$mode" = range ]; then
  # $range 는 일부러 따옴표 없이 — "b --not --remotes" 같이 여러 낱말일 수 있다.
  if ! objs_raw=$(git -C "$ROOT" rev-list --objects $range 2>&1); then
    say "FAIL: git rev-list 실패 ($range)"; say "$objs_raw"; exit 1
  fi
  # rev-list --objects: blob/tree 는 "<sha> <path>", 커밋은 "<sha>" 뿐. blob sha 로 중복 제거.
  cand_sha=(); cand_path=(); declare -A seen_sha=()
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    case "$line" in
      *' '*) sha="${line%% *}"; path="${line#* }" ;;
      *) continue ;;   # 커밋 — 경로 없음
    esac
    [ -z "$path" ] && continue
    [ -n "${seen_sha[$sha]:-}" ] && continue
    seen_sha[$sha]=1
    cand_sha+=("$sha"); cand_path+=("$path")
  done <<<"$objs_raw"
  if [ "${#cand_sha[@]}" -gt 0 ]; then
    if ! types=$(printf '%s\n' "${cand_sha[@]}" | git -C "$ROOT" cat-file --batch-check='%(objectname) %(objecttype)' 2>&1); then
      say "FAIL: git cat-file 실패 ($range)"; say "$types"; exit 1
    fi
    declare -A is_blob=()
    while IFS=' ' read -r s t _rest; do [ "$t" = blob ] && is_blob[$s]=1; done <<<"$types"
    for i in "${!cand_sha[@]}"; do
      if [ -n "${is_blob[${cand_sha[$i]}]:-}" ]; then files+=("${cand_path[$i]}"); blobs+=("${cand_sha[$i]}"); fi
    done
  fi
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

# 1''. 자기 보호 — denylist 정규식 구문 오류 = fail-closed (silent fail-open 방지)
for pat in "${patterns[@]}"; do
  printf '' | grep -E -e "$pat" >/dev/null 2>&1
  if [ $? -eq 2 ]; then say "FAIL: .denylist 잘못된 정규식: $pat"; exit 1; fi
done

# 1'''. 오탐 면제 목록 — 리터럴만, 8자 이상, denylist 에 걸리는 항목은 거부(면제로 완화 금지)
allow=()
if [ -f "$ALLOWLIST" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%%$'\r'}"
    case "$line" in ''|'#'*) continue ;; esac
    if [ "${#line}" -lt 8 ]; then say "FAIL: .allowlist 항목이 너무 짧음: $line"; exit 1; fi
    for pat in "${patterns[@]}"; do
      if printf '%s\n' "$line" | grep -Eiq -e "$pat"; then say "FAIL: .allowlist 항목이 denylist 에 걸림: $line"; exit 1; fi
    done
    allow+=("$line")
  done < "$ALLOWLIST"
fi

content_of() {  # $1 = files 인덱스
  local i="$1"
  case "$mode" in
    tree)  git -C "$ROOT" show "$tree:${files[$i]}" ;;
    range) git -C "$ROOT" cat-file blob "${blobs[$i]}" ;;
    *)     cat "$ROOT/${files[$i]}" 2>/dev/null || cat "${files[$i]}" ;;
  esac
}

scanned=0
for i in "${!files[@]}"; do
  f="${files[$i]}"
  ext="${f##*.}"; ext="${ext,,}"
  if [[ "$f" == *.* ]] && [[ "$ext" =~ ^($BINARY_EXT)$ ]]; then continue; fi
  scanned=$((scanned+1))
  body=$(content_of "$i") || { say "FAIL: $f 를 읽을 수 없음"; fail=1; continue; }
  # 허용 리터럴만 마스킹 — 줄 전체가 아니라 그 리터럴만 검사에서 빠진다(줄 번호는 그대로).
  for lit in "${allow[@]}"; do body="${body//"$lit"/$MASK}"; done
  for pat in "${patterns[@]}"; do
    hits=$(printf '%s\n' "$body" | grep -Ein -e "$pat") && { printf '%s\n' "$hits" | awk -v f="$f" '{print f ":" $0}' >&2; fail=1; }
  done
  for pat in "${BUILTIN[@]}"; do
    hits=$(printf '%s\n' "$body" | grep -Ein -e "$pat") && { printf '%s\n' "$hits" | awk -v f="$f" '{print f ":" $0}' >&2; fail=1; }
  done
done

# 2. 자기 보호 — 대상이 있어야 할 모드에서 0개 = fail-closed (git 이 조용히 빈 목록을 준 경우)
if { [ "$mode" = tree ] || [ "$mode" = range ]; } && [ "$scanned" -eq 0 ]; then
  say "FAIL: 검사한 파일이 0개 — 대상이 비었거나 읽지 못함"; exit 1
fi

if [ "$fail" -ne 0 ]; then say "FAIL: 위 항목을 고친 뒤 다시 시도 (denylist 를 완화하지 않는다)"; exit 1; fi
echo "OK: $scanned files scanned"
