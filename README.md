# daunlee1128.github.io

Jekyll(GitHub Pages 기본 빌드) 블로그. 글 = front matter 붙은 마크다운 파일 한 개.
**게시는 배포가 아니라 파일 이동이다** — `drafts/` 에서 컬렉션 디렉터리로 옮기고 push 하면 끝.

## 구조

```
_tech/  _insights/     글 본체(컬렉션). 여기 있는 파일 = 게시된 글
drafts/                초안. gitignore — 절대 추적되지 않는다
stack/                 스택별 목록 stub. _data/stacks.yml 에서 생성(직접 수정 금지)
explain/               글에 딸린 self-contained HTML. front matter 없이 그대로 복사된다
_data/stacks.yml       스택 원장 — 사이드바 스택 맵의 유일한 출처
_data/kinds.yml        tech 하위 구분(design·config·impl·ops·troubleshooting)과 배지 색
_layouts/ _includes/   default·list·page·post·stack 레이아웃, 헤더·사이드바·목차·글줄
assets/                tokens.css(Radix 색 앵커) · site.css · theme.js(다크) · filter.js(종류 필터·더 보기) · article.js(표 카드화·그림 크게·목차 현재 절)
scripts/               check-publish.sh · dev-build.sh · gen-stack-stubs.py · tests/
.githooks/pre-push     push 전 유출 검사
.denylist              로컬 전용 검사 패턴(gitignore). 없으면 push 가 거부된다
.allowlist             오탐 면제(추적됨)
```

`index.md`(전체) · `tech/index.md` · `insights/index.md` 는 목록 페이지 껍데기고, 실제 글 수집은 `_layouts/list.html` 이 한다.

## 클론 직후 (한 번)

```bash
git config core.hooksPath .githooks            # pre-push 검사 활성화
cp /path/to/your/.denylist .denylist           # 로컬 전용 — 없으면 push 가 거부된다(fail-closed)
git config core.hooksPath                      # → .githooks 가 나와야 한다
```

> `core.hooksPath` 는 `.git/config` 에 저장된다 — 다시 클론하거나 디렉터리를 새로 만들면 따라오지 않는다.
> 설정이 비어 있으면 훅이 아예 실행되지 않고 push 가 그냥 통과한다. 세 번째 명령으로 매번 확인한다.

## 글 하나의 수명

1. **초안** — `drafts/<slug>.md` 에 쓴다. `drafts/` 는 gitignore 라 여기 있는 동안은 아무것도 새어 나가지 않는다.
2. **검사** — `scripts/check-publish.sh drafts/<slug>.md`
3. **게시** — `mv drafts/<slug>.md _tech/` (또는 `_insights/`). `git mv` 가 아니다 — 원본은 추적되지 않는 파일이다.
   front matter 의 임시 `source:` 같은 키는 지운다.
4. **커밋 → push** — pre-push 훅이 push 되는 커밋 범위의 모든 blob 을 검사한다.
5. GitHub Pages 가 `main` 루트를 빌드한다. 별도 CI 없음.

수정·삭제도 같다. 파일을 고쳐 커밋하면 반영되고, 컬렉션에서 지우면 내려간다.

### front matter 계약

```yaml
---
kind: troubleshooting      # tech 전용: design | config | impl | ops | troubleshooting
title: 제목
date: 2026-09-02           # 미래 날짜여도 게시된다 (future: true) — 예약 발행 없음
stack: [kong, bedrock]     # _data/stacks.yml 슬러그만
tags: [사용기]              # 선택 (insights 구분용)
summary: 한 줄 요약          # 목록 페이지에 그대로 나온다
explain: /explain/name.html   # 선택
---
```

### 본문 규약

- 절 제목은 앞 줄에 `{: #situation data-k="SITUATION"}` (id 필수·ASCII, `data-k` 캡션 선택) + `## 제목`.
  목차(`quicknav-toc`)는 **id 가 있는 h2 만** 줍는다. 헤더 안에 HTML 금지.
- 강조 블록: `<div class="callout" markdown="1">**재발 방지** — …</div>`

## 유출 검사

`scripts/check-publish.sh` 하나가 세 가지 모드로 돈다.

```bash
scripts/check-publish.sh                        # 작업 트리의 추적 파일 전체
scripts/check-publish.sh drafts/x.md …          # 지정 파일
scripts/check-publish.sh --tree <sha>           # 그 커밋의 트리
scripts/check-publish.sh --range <범위>          # 범위의 모든 blob (pre-push 가 호출)
```

`--range` 를 쓰는 이유: 팁 트리만 보면 "새어 든 파일을 다음 커밋에서 지우고 push" 가 통과해 버리는데, 원격 이력에는 그 blob 이 그대로 남는다.
**걸리면 글을 고친다. denylist 를 완화하지 않는다.** 이미 커밋된 누출은 그 커밋을 되감아야(rebase/reset) 지워진다.

`.denylist` 형식: 한 줄에 `패턴<TAB>치환어`(치환어 생략 가능, `#` 주석). 훅은 1열(`grep -Ein`)만 본다.
1열이 잘못된 정규식이면 검사가 실패로 끝난다(fail-closed) — 괄호·`+`·`|` 같은 메타문자는 `\` 로 이스케이프한다.

### 오탐이 났을 때

검사는 내장 패턴(이메일 · 전화 · `git@…:` · gitlab URL · `*.internal`/`*.corp` · 사설 IP)을 항상 적용한다.
공개해도 무해한 문자열이 여기 걸리면 `.allowlist` 에 **그 리터럴 한 줄**을 추가한다.

- 정규식이 아니라 **리터럴 부분 문자열**이다. 8자 미만은 거부한다(너무 넓은 면제 방지).
- 매치된 줄 전체가 아니라 **그 리터럴만** 빠진다 — 같은 줄의 다른 누출은 그대로 걸린다.
- `.denylist` 에 걸리는 항목은 `.allowlist` 에 넣을 수 없다(거부된다).
- `.denylist` 와 달리 `.allowlist` 는 **추적되는 파일**이다 — 공개해도 무해한 것만 넣는다.

예: `git@github.com:` 같은 공개 호스트 접두사, 사설 IP 로 오인되는 4자리 버전 문자열(`10.0.<빌드>.<패치>` 꼴).
내장 패턴 자체는 손대지 않는다.

## 스택 추가

`_data/stacks.yml` 의 그룹에 `{ slug, name }` 을 넣고 `python3 scripts/gen-stack-stubs.py` → `stack/<slug>.md` 생성(멱등, yml 에서 빠진 stub 은 삭제).
slug 는 `[a-z0-9-]`. 글이 하나도 없는 스택은 사이드바에 나오지 않는다.

## 로컬 빌드 · 테스트 (선택)

```bash
gem install bundler && bundle install
scripts/dev-build.sh [--with-samples]          # → _site/ (bundle 없으면 SKIP)
python3 -m unittest discover -s scripts/tests -v
```

`dev-build.sh` 는 repo 를 임시 디렉터리에 복사해 빌드한다 — `--with-samples` 면 `drafts/samples/` 를 얹어 초안까지 렌더한다.
빌드 테스트는 bundle 이 없으면 skip 된다.
