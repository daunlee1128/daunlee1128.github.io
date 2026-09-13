---
type: insights
title: "Claude Code가 만든 md·html을 GitHub Pages에 그대로 올릴 수 있나"
date: 2026-09-02
stack: [claude-code, github-pages]
tags: [사용기]
summary: "웹 에디터에 다시 붙여넣는 일을 줄이려고 로컬 파일을 글 단위로 골랐다. 사흘간 사이트를 세운 뒤, 볼트에서 고른 기술 글 11편을 한 번에 옮겼다."
---

웹 에디터에 다시 붙여넣는 일을 줄이려고 로컬 파일을 글 단위로 골랐다.
사흘간 사이트를 세운 뒤, 볼트에서 고른 기술 글 11편을 한 번에 옮겼다.
독자는 그대로 옮겨지는 경계와 무료 호스팅에서 공개되는 범위를 얻는다.
Claude Code로 md·html을 로컬에 쌓아 두는 사람을 전제로 한다.
답은 [컬렉션과 front matter를 나눈 절](#files)에 있다.

해 볼 것:

1. 올릴 글 하나에 아래 답 절의 front matter를 붙인다.
2. 공개하면 안 되는 초안 디렉터리를 추적 대상에서 뺀다.

   ```gitignore
   # .gitignore
   drafts/
   ```

3. 이 repo를 clone했다면 커밋된 유출 검사 훅을 켠다.

   ```bash
   git config core.hooksPath .githooks
   git config --get core.hooksPath
   ```

{: #first-batch}
## 사이트를 세운 뒤 기술 글 11편을 한 번에 옮겼다

설계 문서를 모아 둔 디렉터리 하나에 md 8·html 15·png 11이 있었다.
옮겨 적는 일 때문에 파일이 쌓여도 블로그는 미뤘다.

2026-08-30부터 09-01까지 커밋 28개로 Jekyll 사이트를 세웠다.
KST 기준 날짜 범위로 git 이력을 다시 센 값이다.
이 구축 구간의 추적 파일은 레이아웃·CSS·검사 스크립트를 포함해 63개였다.
09-07에는 볼트에서 고른 기술 글 11편을 `_tech/`로 옮겼다.
게시 커밋 `20b963c`에 11편이 함께 들어 있다.
한 편당 걸린 시간은 이 일괄 커밋으로 계산할 수 없다.

설정법을 순서대로 설명하는 글과 달리, 여기서는 파일을 골라 옮긴 범위를 다룬다.
볼트 전체를 사이트로 바꾸는 작업은 하지 않았다.

<details markdown="1">
<summary>같은 이유로 블로그를 미뤘다면 펼치기: 파일 이동으로 줄어든 작업</summary>

미룬 이유는 붙여넣기·재업로드·이관처럼 원문을 옮기는 작업이었다.

| 어떤 작업이 걸렸나 | 무엇이 필요했나 | 이 구성에서는 어떻게 했나 |
|---|---|---|
| 웹 에디터에 붙여넣기 | 로컬 md 복사와 형식 재정리 | md를 컬렉션에 넣고 공통 레이아웃 적용 |
| html 산출물 올리기 | 캡처하거나 별도 호스팅 찾기 | front matter 없이 정적 파일로 배치 |
| 게시 경로 익히기 | 플랫폼 에디터·배포 도구 관리 | 파일 이동, commit, push |
| 생성기 교체 | 플랫폼에서 원문 내보내기 | repo의 md를 원문으로 유지 |

</details>

{: #files}
## md는 컬렉션에서 글로 처리하고 통짜 html은 정적 파일로 둔다

이 글의 조건: Free 플랜 public repo, GitHub Pages 기본 Jekyll 빌드.
별도 CI workflow는 없다. 로컬은 github-pages 232·Jekyll 3.10.0·kramdown 2.4.0이다.
버전은 2026-09-12 `Gemfile.lock`으로 확인했다.
로컬 Gemfile·lock은 GitHub Pages 서버 빌드의 입력이 아니다.

이 repo는 `_posts/` 대신 `_tech/`·`_insights/` 컬렉션을 쓴다.
아래는 기술 글의 여섯 키를 채운 예다.
구분선 `---`는 여섯 키에 포함하지 않는다.

```yaml
---
type: tech
kind: config
title: GitHub Pages 게시 경로를 설정했다
date: 2026-09-12
stack: [github-pages]
summary: 초안과 게시 파일을 디렉터리로 나눴다.
---
```

insights 글은 `type: insights`로 쓰고 `kind` 대신 `tags`를 둔다.
front matter만 붙였다고 발행 준비가 끝나는 것은 아니다.
컬렉션 위치, 링크, 공개해도 되는 내용을 함께 확인한다.

통짜 html은 front matter 없이 `explain/`에 둔다.
Jekyll은 이 파일을 정적 파일로 복사한다.
front matter를 붙이면 Liquid 처리 대상이 된다.
이는 [Jekyll front matter](https://jekyllrb.com/docs/front-matter/)와 [정적 파일 규약](https://jekyllrb.com/docs/static-files/)에서 확인했다(2026-09-12).

<details markdown="1">
<summary>볼트를 통째로 옮기려면 펼치기: 2026-09-01 집계와 파일별 손질</summary>

로컬 볼트 1개를 `find`·`grep`으로 셌다.
2026-09-01 기준 md 457개, html 64개였다.
아래 분모는 발행된 블로그 파일 수가 아니라 이 볼트의 파일 수다.

| 볼트에 무엇이 있었나 | 몇 개였나 | 이 repo로 옮길 때 무엇을 하나 |
|---|---|---|
| front matter 없는 md | 243 / 457 | 필요한 키를 채우고 컬렉션에 배치 |
| 한글 파일명 | 252 / 457 | URL로 쓸 ASCII 슬러그 선택 |
| 이중 중괄호가 든 html | 3 / 64 | 통짜 산출물에는 front matter를 붙이지 않음 |

이 집계는 저장된 당시 기록이다. 현재 볼트를 다시 센 값은 아니다.
파일 하나씩 손보는 방법은 고른 글을 옮기는 범위에서만 썼다.
전체 자동 미러링에는 별도 변환이 필요하다고 판단한다(추론).

</details>

{: #public}
## Free 플랜에서는 원문과 커밋 이력까지 공개된다

GitHub Free의 Pages는 public repo를 전제로 한다.
Pro·Team 등은 private repo에서도 Pages를 호스팅할 수 있다.
repo의 공개 여부와 사이트의 접근 제어는 별개다.
[GitHub Pages 플랜 안내](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)를 확인했다(2026-09-12).

사이트 비공개 발행은 Enterprise Cloud 조직의 project site에 제공된다.
해당 조직이 소유한 private·internal repo 등 추가 조건이 있다.
이 개인 사이트를 상위 플랜으로 바꾸기만 하면 비공개가 된다는 뜻은 아니다.
[GitHub Pages 접근 제어 문서](https://docs.github.com/en/enterprise-cloud@latest/pages/getting-started-with-github-pages/changing-the-visibility-of-your-github-pages-site)에 따른 범위다(2026-09-12).

초안 디렉터리는 gitignore하고, push 전 유출 검사를 붙였다.
이미 추적된 파일은 gitignore만 추가해도 추적에서 빠지지 않는다.
[Git gitignore 문서](https://git-scm.com/docs/gitignore)의 규약이다(2026-09-12 확인).
이 작업에서 쓴 Git은 2.50.1이다.
처음에는 최신 트리만 검사했다.
그러면 누출 파일을 다음 커밋에서 지운 뒤 push할 때 놓친다.
원격 이력에는 이전 blob이 남아서 검사 범위를 커밋 전체로 바꿨다.

<details markdown="1">
<summary>훅을 검토하려면 펼치기: 첫 push와 브랜치 삭제를 포함한 전체 코드</summary>

아래는 이 repo에 커밋된 `.githooks/pre-push`다.
2026-09-12에 HEAD와 로컬 사본이 같은지 확인했다.
앞의 `core.hooksPath` 설정이 있어야 이 파일을 실행한다.

```bash
#!/usr/bin/env bash
# pre-push: push 되는 각 ref 의 "커밋 범위 전체 blob" 을 scripts/check-publish.sh 로 검사한다.
#           팁 트리만 보면 뒤 커밋에서 지운 파일이 원격 이력으로 새어 나간다.
# 설치: git config core.hooksPath .githooks   (README)
set -u
ROOT=$(git rev-parse --show-toplevel)
zero=$(printf '0%.0s' $(seq 1 40))   # 전부 0 인 OID = ref 없음. SHA-1 기준 40자.
status=0
while read -r local_ref local_sha remote_ref remote_sha; do
  [ "$local_sha" = "$zero" ] && continue   # ref 삭제
  if [ "$remote_sha" = "$zero" ]; then
    range="$local_sha --not --remotes"     # 새 브랜치/첫 push: 원격에 없는 모든 커밋
  else
    range="$remote_sha..$local_sha"
  fi
  echo "check-publish: $local_ref ($(git rev-parse --short "$local_sha")) range: $range" >&2
  # $range 는 일부러 따옴표 없이 — 여러 낱말일 수 있다.
  "$ROOT/scripts/check-publish.sh" --range $range || status=1
done
exit $status
```

`$range`의 비인용은 의도적이다. 새 브랜치에서는 여러 인자로 나눠 넘긴다.
훅은 검사기의 호출부다. 다른 repo에 이 파일만 복사하면 검사가 완성되지 않는다.
이 repo의 `scripts/check-publish.sh`와 로컬 `.denylist`도 필요하다.

검사기는 이메일·전화번호·SSH git 주소·GitLab URL·내부 도메인·사설 IP를 찾는다.
여기에 `.denylist` 패턴을 더한다.
호출부는 커밋된 코드 기준이고, 미커밋 검사기 변경의 동작까지 검증했다는 뜻은 아니다.

</details>

{: #limits}
## 골라 옮길 양을 넘으면 다시 판단한다

웹 에디터에 다시 붙이는 방법이 가장 적은 준비로 시작할 수 있다.
나는 로컬 원문을 계속 쓰려는 목적 때문에 파일 이동을 택했다.

| 어떤 상황인가 | 어떤 판단을 남기나 | 근거 종류 |
|---|---|---|
| md·html을 글 단위로 골라 올림 | 이 작업 범위에서 권함 | 11편 일괄 게시 기록, [미확인: DOCS-6 · 작성자가 권고에 쓴 근거 종류] |
| 볼트 전체 자동 미러링 | 수동 이동을 그대로 확대하는 것은 보류 | 변환 필요성은 추론, [미확인: DOCS-6 · 비교·기각 근거 종류] |
| 초안과 커밋 이력까지 비공개여야 함 | 이 Free·public 구성은 맞지 않음 | 플랜 문서 확인, [미확인: DOCS-6 · 당시 권고 근거 종류] |
| 댓글·통계·구독 관리가 필요함 | 필요한 기능의 운영 경로부터 확인 | [미확인: DOCS-6 · 외부 서비스가 필요하다는 판단의 근거 종류] |

확인한 경험은 사이트 구축과 11편 일괄 게시까지다.
파일마다 손보는 양이 늘면 이 방법의 비용도 달라진다.
그때는 옮길 파일 수와 파일당 손질을 기준으로 다시 비교해야 한다.
