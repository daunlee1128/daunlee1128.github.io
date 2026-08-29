# blog

Jekyll(GitHub Pages 기본 빌드) 기술 블로그. 글 = front matter 붙은 마크다운.

## 처음 클론했을 때

```bash
git config core.hooksPath .githooks            # pre-push 검사 활성화 (한 번)
cp /path/to/your/.denylist .denylist            # 로컬 전용 — gitignore 되어 있음. 없으면 push 가 거부된다(fail-closed)
```

`.denylist` 형식: 한 줄에 `패턴<TAB>치환어`. 치환어는 생략 가능, `#` 주석. 훅은 1열(`grep -Ein`)만 본다. 1열이 잘못된 정규식이면 검사가 실패로 끝난다(fail-closed) — 괄호·`+`·`|` 같은 메타문자는 `\`로 이스케이프한다.

## 글 올리기

1. 초안은 `drafts/` (gitignore). `/blog-post` 스킬이 여기에 만든다.
2. 미리 검사: `scripts/check-publish.sh drafts/<slug>.md`
3. 게시 = 컬렉션으로 이동: `git mv` 가 아니라 `mv drafts/<slug>.md _tech/` (또는 `_insights/`). front matter의 임시 `source:` 키는 지운다.
4. 커밋 → push. pre-push 훅이 push 되는 트리 전체를 검사하고, 걸리면 거부한다. **글을 고친다. denylist 를 완화하지 않는다.**

front matter 계약:

```yaml
---
kind: troubleshooting      # tech 전용: design | config | impl | ops | troubleshooting
title: 제목
date: 2026-09-02
stack: [kong, bedrock]     # _data/stacks.yml 슬러그만
tags: [사용기]              # 선택 (insights 구분용)
summary: 한 줄 요약
explain: /explain/name.html   # 선택
---
```

본문 규약: 절 제목은 앞 줄에 `{: #situation data-k="SITUATION"}` (id 필수·ASCII, `data-k` 캡션 선택) + `## 제목`. 헤더 안에 HTML 금지. 재발 방지 등 강조는
`<div class="callout" markdown="1">**재발 방지** — …</div>`. 목차는 h2에서 자동.

## 스택 추가

`_data/stacks.yml`에 넣고 `python3 scripts/gen-stack-stubs.py` → `stack/<slug>.md` 생성. 글이 없는 스택은 사이드바에 나오지 않는다.

## 로컬 빌드 (선택)

ruby + `gem install bundler` 후 `bundle install`. `scripts/dev-build.sh [--with-samples]` → `_site/`.
테스트: `python3 -m unittest discover -s scripts/tests -v` (bundle 없으면 빌드 테스트는 skip).

## 구조

`_tech/` `_insights/` 컬렉션 · `stack/` 스택별 목록 stub · `explain/` self-contained HTML(front matter 없음, 그대로 복사) · `_data/stacks.yml` 스택 원장 · `_data/kinds.yml` 하위 구분 · `assets/` tokens.css(Radix Themes 앵커) · site.css · theme.js · filter.js.
