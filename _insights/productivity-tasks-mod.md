---
type: insights
title: Claude Code productivity plugin과 mod로 작업 관리를 해 본 후기
date: 2026-09-24
stack: [claude-code]
tags: [사용기]
summary: "productivity plugin의 TASKS.md에 mod를 하나 붙여, Claude가 일하면서 할 일도 같이 고치고 터미널에서 바로 보이게 했다. 샘플 화면으로 보는 사용 모습과 좋았던 점·아쉬운 점, 세팅 순서."
---

할 일 목록이 작업을 따라오도록 Claude Code productivity plugin에 mod를 하나 만들어 붙여 써 봤다.
써 보니 목록을 따로 챙기는 수고는 줄었고, 몇 군데는 아쉬웠다.
아래 화면과 예시는 이 글을 위해 만든 샘플 폴더이고, 인물·프로젝트·용어는 모두 가상 예시다.
Claude Code로 할 일을 관리해 보려는 사람을 독자로 한다. 따라 하려면 [세팅](#setup)부터 보면 된다.

{: #how}
## 할 일은 TASKS.md, 맥락은 memory에 두고 Claude가 일하면서 고치게 한다

productivity plugin은 할 일을 `TASKS.md`에, 사람·약어·프로젝트 같은 맥락을 `CLAUDE.md`와 `memory/`에 둔다.
여기에 붙인 mod는 열린 할 일을 매 턴 Claude에게 보여 주고, 할 일 추가·완료용 tool과 터미널 pane을 준다.

<figure class="fig">
<div class="fig-scroll">
<img src="/assets/img/productivity-tasks-mod/terminal-tasks-pane.png" alt="Claude Code 터미널 오른쪽 tasks pane. Active 5건과 Waiting On 3건에는 번호와 완료 버튼이 붙고 Someday 2건은 목록으로만 나온다. 하단 상태줄에 할 일 Active 5 · Waiting On 3이 보인다" loading="lazy">
</div>
<figcaption>샘플 폴더에서 연 tasks pane으로, 번호 키를 누르면 그 줄의 할 일이 완료된다(항목은 가상 예시).</figcaption>
</figure>

일을 시작할 때는 "지금 할 일은 뭐야?"라고 묻고, 오늘 할 일 하나를 골라 시킨다.
Claude는 일하면서 끝난 할 일은 완료로 옮기고, 새로 생긴 일은 추가한다.
내가 결정해야 하는 일은 Waiting On에 올려 두게 했다.

넓게 보고 싶을 때는 plugin이 만든 dashboard.html을 브라우저로 연다.

<figure class="fig">
<div class="fig-scroll">
<img src="/assets/img/productivity-tasks-mod/dashboard-board.png" alt="dashboard.html Tasks 탭 Board 보기: Active, Waiting On, Someday, Done 네 컬럼 칸반. 카드마다 due·since·P1 메모가 있고 Atlas PRD 카드에 하위 체크리스트 3개 중 1개가 체크돼 있다" loading="lazy">
</div>
<figcaption>샘플 TASKS.md를 dashboard 보드로 본 화면으로, 파일의 들여쓴 하위 항목이 카드 안 체크리스트가 된다.</figcaption>
</figure>

Memory 탭에서는 Claude가 알고 있는 맥락을 본다.
할 일에 "WSR", "박팀장"처럼 줄여 써도 Claude가 풀어 읽는 근거가 여기 있다.

<figure class="fig">
<div class="fig-scroll">
<img src="/assets/img/productivity-tasks-mod/memory-overview.png" alt="dashboard Memory 탭 Overview: Context 18, Projects 3, People 5 카운트와 CLAUDE.md 내용(Me: 홍길동, 제품팀 PM과 People 표)" loading="lazy">
</div>
<figcaption>샘플 Overview로, Claude가 session마다 읽는 맥락이 맞는지 파일을 열지 않고 확인할 수 있다(인물은 가상 예시).</figcaption>
</figure>

<figure class="fig">
<div class="fig-scroll">
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px">
<div><img src="/assets/img/productivity-tasks-mod/memory-glossary.png" alt="Glossary 화면: WSR, PRD, OKR, QBR, RFC, P0/P1/P2, EOD, KPI 약어 표" loading="lazy"><div>Glossary</div></div>
<div><img src="/assets/img/productivity-tasks-mod/memory-context.png" alt="Context 화면: 쓰는 도구(메신저, 이슈 트래커, 위키, 캘린더, BI 도구), 팀별 역할과 담당자, 매일 10:00 스탠드업 같은 프로세스" loading="lazy"><div>Context</div></div>
<div><img src="/assets/img/productivity-tasks-mod/memory-people.png" alt="People 화면: 5명의 카드마다 별칭, 역할, 팀, 소통 선호" loading="lazy"><div>People</div></div>
<div><img src="/assets/img/productivity-tasks-mod/memory-projects.png" alt="Projects 화면: Atlas, Onboard, Bridge 카드마다 코드명, 별칭, 상태, 설명" loading="lazy"><div>Projects</div></div>
</div>
</div>
<figcaption>샘플 memory/ 파일을 탭별로 본 화면으로, 할 일 제목의 줄임말을 여기서 풀어 준다(모두 가상 예시).</figcaption>
</figure>

{: #review}
## 할 일이 작업을 따라오는 건 좋았고 확인 장치와 취소 처리는 아쉬웠다

좋았던 점은 셋이다.

- TASKS.md를 따로 챙기지 않아도 된다. Claude가 일하면서 완료와 추가를 알아서 해 줬다.
- 새 session을 열어도 할 일을 다시 설명하지 않는다. "지금 할 일은 뭐야?" 한마디면 된다.
- 터미널을 떠나지 않고 할 일을 본다. 한눈에 보고 싶을 때만 dashboard를 연다.

아쉬운 점도 셋이다.

- Claude가 끝내기 전에 한 번 막는 장치는 생각만큼 쓸모가 없었다. 대개 "반영할 것 없음" 한 줄로 넘어갔다.
- 추가·완료 tool만 만들어서, 취소한 할 일도 완료로 남는다.
- mod가 아직 early access 기능이라 환경변수를 켜야 한다. 업데이트 때마다 멈추지 않을지도 신경이 쓰인다.

{: #why}
## 계기는 TASKS.md를 챙기는 일이 자꾸 밀린 것이다

`/productivity:start`로 TASKS.md를 만들어 두고, `/productivity:update`로 틈틈이 챙기려고 했다.
그런데 일에 집중하다 보면 업데이트를 자꾸 잊거나 뒤로 미루게 됐다. 여러 session에 나눠 일하다 보니 목록은 금방 실제 작업과 어긋났다.
그러다 Claude Code mod가 떠올라 찾아봤다. 작업하는 session 화면에 할 일이 바로 보이면, 보이는 김에 바로 고치게 되지 않을까 싶었다.
그렇게 pane부터 만들다가 "이왕이면 hook으로 붙이자"는 생각이 들어, 갱신까지 자동으로 되게 했다.

{: #setup}
## 세팅은 plugin 설치, 초기화, mod 등록 순서다

1. productivity plugin을 설치한다.

   ```bash
   claude plugin marketplace add anthropics/knowledge-work-plugins
   claude plugin install productivity@knowledge-work-plugins
   ```

2. 작업 폴더에서 `claude`를 띄우고 `/productivity:start`를 실행한다. TASKS.md와 dashboard.html이 생긴다. 이어지는 질문에 답하면 `CLAUDE.md`와 `memory/`가 채워진다.
3. dashboard.html을 브라우저로 열고 작업 폴더를 한 번 고른다.
4. mod를 `mods/tasks`에 두고 작업 폴더의 `.claude/settings.json`으로 켠다. mod는 early access 기능이라 `CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1`이 필요하다.

mod 코드는 Claude Code에게 mods README와 내장 mod 예제를 읽혀 함께 만들었다.

<details markdown="1">
<summary>mod를 켜는 설정을 보려면 펼치기: 샘플 폴더의 .claude/settings.json</summary>

이 폴더에서 `claude`만 실행해도 mod가 켜진다. `sample-mods`는 `mods/` 폴더를 가리키는 로컬 marketplace 이름이다.
`tasks@sample-mods`가 잡히려면 `mods/.claude-plugin/marketplace.json`의 `plugins`에 `{ "name": "tasks", "source": "./tasks" }`가 등록돼 있어야 한다.

```json
{
  "env": { "CLAUDE_CODE_ENABLE_FUNCTION_HOOKS": "1" },
  "enabledPlugins": { "tasks@sample-mods": true },
  "extraKnownMarketplaces": {
    "sample-mods": {
      "source": { "source": "directory", "path": "/path/to/sample-task-management/mods" }
    }
  },
  "tui": "fullscreen"
}
```

</details>

mod는 그 폴더에서 `claude`를 띄울 때만 켜진다.
