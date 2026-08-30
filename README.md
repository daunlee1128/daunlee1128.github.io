# blog

Jekyll(GitHub Pages 기본 빌드) 기술 블로그. 글 = front matter 붙은 마크다운.

## 처음 클론했을 때

```bash
git config core.hooksPath .githooks            # pre-push 검사 활성화 (한 번)
cp /path/to/your/.denylist .denylist           # 로컬 전용 — gitignore 되어 있음. 없으면 push 가 거부된다(fail-closed)
git config core.hooksPath                      # → .githooks 가 나와야 한다. 이 설정이 없으면 검사 자체가 없다 — 클론·rename 뒤마다 확인
```

> `core.hooksPath` 는 `.git/config` 에 저장된다 — 저장소를 다시 클론하거나 디렉터리를 새로 만들면 따라오지 않는다.
> 설정이 비어 있으면 훅이 아예 실행되지 않고 push 가 그냥 통과한다. 세 번째 명령으로 매번 확인한다.

`.denylist` 형식: 한 줄에 `패턴<TAB>치환어`. 치환어는 생략 가능, `#` 주석. 훅은 1열(`grep -Ein`)만 본다. 1열이 잘못된 정규식이면 검사가 실패로 끝난다(fail-closed) — 괄호·`+`·`|` 같은 메타문자는 `\`로 이스케이프한다.

## 글 올리기

1. 초안은 `drafts/` (gitignore). `/blog-post` 스킬이 여기에 만든다.
2. 미리 검사: `scripts/check-publish.sh drafts/<slug>.md`
3. 게시 = 컬렉션으로 이동: `git mv` 가 아니라 `mv drafts/<slug>.md _tech/` (또는 `_insights/`). front matter의 임시 `source:` 키는 지운다.
4. 커밋 → push. pre-push 훅이 push 되는 커밋 범위의 모든 blob(뒤 커밋에서 지운 파일 포함)을 검사한다(`check-publish.sh --range`).
   팁 트리만 보면 "새어 든 파일을 다음 커밋에서 지우고 push" 가 통과해 버리는데, 원격에는 그 blob 이 그대로 남는다. 걸리면 거부한다.
   **글을 고친다. denylist 를 완화하지 않는다.** 이미 커밋된 누출은 그 커밋을 되감아야(rebase/reset) 지워진다.

수동 실행 3종: `scripts/check-publish.sh <파일…>` · `--tree <sha>` · `--range <범위>`(`a..b` 또는 `<sha> --not --remotes`).

front matter 계약:

```yaml
---
kind: troubleshooting      # tech 전용: design | config | impl | ops | troubleshooting
title: 제목
date: 2026-09-02          # 미래 날짜여도 게시된다 (future: true) — 예약 발행 없음
stack: [kong, bedrock]     # _data/stacks.yml 슬러그만
tags: [사용기]              # 선택 (insights 구분용)
summary: 한 줄 요약
explain: /explain/name.html   # 선택
---
```

본문 규약: 절 제목은 앞 줄에 `{: #situation data-k="SITUATION"}` (id 필수·ASCII, `data-k` 캡션 선택) + `## 제목`. 헤더 안에 HTML 금지. 재발 방지 등 강조는
`<div class="callout" markdown="1">**재발 방지** — …</div>`. 목차는 h2에서 자동.

## 오탐이 났을 때

검사는 내장 패턴(이메일·전화·`git@…:`·gitlab URL·`*.internal`/`*.corp`·사설 IP)을 항상 적용한다.
공개해도 무해한 문자열이 여기에 걸리면 `.allowlist` 에 **그 리터럴 한 줄**을 추가한다.

- 정규식이 아니라 **리터럴 부분 문자열**이다. 8자 미만은 거부한다(너무 넓은 면제 방지).
- 매치된 줄 전체가 아니라 **그 리터럴만** 검사에서 빠진다 — 같은 줄의 다른 누출은 그대로 걸린다.
- `.denylist` 에 걸리는 항목은 `.allowlist` 에 넣을 수 없다(거부된다). 면제로 denylist 를 완화할 수 없다.
- `.denylist` 와 달리 `.allowlist` 는 **추적되는 파일**이다 — 공개해도 무해한 것만 넣는다.

예: `git@github.com:` 같은 공개 호스트 접두사, 사설 IP 로 오인되는 4자리 버전 문자열(`10.0.<빌드>.<패치>` 꼴).
내장 패턴 자체는 절대 손대지 않는다.

## 계정 생성 후 바꿀 것

- [ ] `_config.yml`: `title` · `handle` · `url` · `github_url` 을 실제 계정 값으로
- [ ] 디렉터리(그리고 저장소 이름)를 `<id>.github.io` 로 rename
- [ ] rename 뒤 `git config core.hooksPath .githooks` 를 다시 실행하고 `git config core.hooksPath` 로 확인
- [ ] `.denylist` 작성(없으면 push 가 fail-closed 로 거부된다)
- [ ] `git remote add origin https://github.com/<id>/<id>.github.io.git`
- [ ] GitHub Pages 설정: Source = 브랜치 `main` / 루트(`/`)

## 스택 추가

`_data/stacks.yml`에 넣고 `python3 scripts/gen-stack-stubs.py` → `stack/<slug>.md` 생성. 글이 없는 스택은 사이드바에 나오지 않는다.

## 로컬 빌드 (선택)

ruby + `gem install bundler` 후 `bundle install`. `scripts/dev-build.sh [--with-samples]` → `_site/`.
테스트: `python3 -m unittest discover -s scripts/tests -v` (bundle 없으면 빌드 테스트는 skip).

## 구조

`_tech/` `_insights/` 컬렉션 · `stack/` 스택별 목록 stub · `explain/` self-contained HTML(front matter 없음, 그대로 복사) · `_data/stacks.yml` 스택 원장 · `_data/kinds.yml` 하위 구분 · `assets/` tokens.css(Radix Themes 앵커) · site.css · theme.js · filter.js.
