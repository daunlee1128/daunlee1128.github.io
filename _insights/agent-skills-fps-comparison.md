---
type: insights
title: "Claude Code 스킬 package 5개를 같은 FPS 원샷 과제로 비교한 결과"
date: 2026-09-22
stack: [claude-code, langfuse, docker]
tags: [사용기, 실험 정리]
summary: "같은 60초 FPS 원샷 과제를 순정 baseline과 Superpowers·Matt Pocock·ECC·Ponytail·gstack으로 한 번씩 돌렸다. 여섯 조건 모두 구현 뒤 확인·수정·재검증으로 이어졌고, 차이는 그 과정을 이루는 역할·문서·검사 범위와 투입량이었다."
---

GitHub에서 별을 많이 받은 Agent Skills가 실제 작업에서 무엇이 다른지 궁금했다.
그래서 2026-09-16에 같은 FPS 원샷 과제를 순정 baseline과 스킬 package 5개로 한 번씩 돌렸다.
여섯 조건 모두 구현 뒤 확인·수정·재검증으로 이어졌다.
달랐던 것은 그 과정을 이루는 역할·문서·검사 범위와 투입량이었다.
유명한 Agent Skills를 직접 실험해 보려는 사람, package마다 성능이 어떻게 다른지 궁금한 사람을 독자로 한다.
숫자는 [비교](#comparison), 판정은 [독립 평가](#quality), 한계는 [마지막 절](#limits)에 있다.

{: #unit}
## 비교 단위는 개별 SKILL.md가 아니라 package 전체로 잡았다

Skill·Rule은 작업 지침이고 Command·Agent·Hook은 실행 구성이라, 한 package 안에서 두 층이 같이 움직인다.
그래서 SKILL.md 한 장의 효과를 따지지 않고 package 전체가 만드는 개발 방식을 비교했다.
문서에 적힌 절차와 실제로 작동한 절차도 구분해 기록했다.

Star 순 후보 10개 중 5개를 실험했고, 나머지 5개는 설치·entry 활성화 검증까지만 했다.

<details markdown="1">
<summary>후보 10개가 무엇을 제공하는지 보려면 펼치기: 구성 요소 수와 Star 수</summary>

Star 수는 발표 시점(2026-09-17)에 보존한 값이고 실시간 통계가 아니다.
Star는 관심의 지표일 뿐 성능 순위가 아니다.
구성 요소 수는 skill·command·agent·rule·hook을 합친 개수다.

| 스킬 | 무엇을 제공하나 | 구성 요소 수 | Star | 이번 실험 |
|---|---|---:|---:|---|
| [Superpowers](https://github.com/obra/superpowers) | 설계부터 완료까지 개발 순서를 연결 | 15 | 287,284 | 실행 |
| [Matt Pocock Skills](https://github.com/mattpocock/skills) | 필요한 작업법을 작게 골라 조합 | 37 | 263,035 | 실행 |
| [ECC](https://github.com/affaan-m/ECC) | 스킬·명령·역할·hook을 함께 구성 | 600 | 259,499 | 실행 |
| [Ponytail](https://github.com/DietrichGebert/ponytail) | 요구를 이해한 뒤 필요한 코드만 남김 | 9 | 139,626 | 실행 |
| [Spec Kit](https://github.com/github/spec-kit) | 명세에서 구현까지 추적 가능한 문서 | 28 | 137,124 | 미실험 |
| [gstack](https://github.com/garrytan/gstack) | 제품 리뷰와 실제 browser QA 연결 | 57 | 133,270 | 실행 |
| [Addy Osmani Skills](https://github.com/addyosmani/agent-skills) | 개발 단계에 맞는 스킬 routing | 41 | 94,969 | 미실험 |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | 변경 하나를 proposal·spec·tasks로 관리 | 12 | 68,422 | 미실험 |
| [BMad Method](https://github.com/bmad-code-org/BMAD-METHOD) | 작업 크기에 맞춰 기획·설계 깊이 조절 | 35 | 53,068 | 미실험 |
| [GSD Core](https://github.com/open-gsd/gsd-core) | 긴 작업을 phase와 상태 문서로 이어 감 | 135 | 9,500 | 미실험 |

</details>

{: #task}
## 과제는 빈 프로젝트에서 60초 FPS 한 판을 원샷으로 만드는 것이었다

과제 「퇴근 사수」는 Vite + TypeScript + Three.js로 만드는 FPS다.
방 하나, 엄폐벽 하나, 정지한 드론 5개를 두고 60초 동안 쏜다.
테스트 통과로 끝나지 않고, container 안 Chromium에서 실제로 조작해 플레이를 검증해야 완료다.

<figure class="fig">
<div class="fig-scroll">
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px">
<div><img src="/assets/img/agent-skills-fps-comparison/baseline.jpg" alt="baseline의 플레이 화면: 상단 중앙 HUD, 오른쪽 아래 무기 모델" loading="lazy"><div>baseline</div></div>
<div><img src="/assets/img/agent-skills-fps-comparison/ponytail.jpg" alt="Ponytail의 플레이 화면: 왼쪽 위 한 줄 HUD, 명중 표시" loading="lazy"><div>Ponytail</div></div>
<div><img src="/assets/img/agent-skills-fps-comparison/matt-pocock.jpg" alt="Matt Pocock의 플레이 화면: 처리 점수와 퇴근까지 남은 시간 HUD" loading="lazy"><div>Matt Pocock</div></div>
<div><img src="/assets/img/agent-skills-fps-comparison/ecc.jpg" alt="ECC의 플레이 화면: 색 조명이 들어간 방과 무기 모델" loading="lazy"><div>ECC</div></div>
<div><img src="/assets/img/agent-skills-fps-comparison/superpowers.jpg" alt="Superpowers의 플레이 화면: 좌우 상단 HUD 카드와 엄폐벽" loading="lazy"><div>Superpowers</div></div>
<div><img src="/assets/img/agent-skills-fps-comparison/gstack.jpg" alt="gstack의 플레이 화면: 모서리의 작은 텍스트 HUD, 무기 모델 없음" loading="lazy"><div>gstack</div></div>
</div>
</div>
<figcaption>같은 요구로 만들었지만 HUD·조명·무기 표현은 조건마다 달랐다(각 조건이 자체 browser 검증에서 남긴 플레이 화면).</figcaption>
</figure>

<details open markdown="1">
<summary>독립 평가 판정을 요구별로 대조하려면 펼치기: 공통 확인 항목 A1–A11</summary>

| ID | 기능 | 확인할 것 |
|---|---|---|
| A1 | 실행 준비 | 프로젝트·패키지를 설치하고 개발 서버와 build를 실행한다 |
| A2 | 이동·조준 | 시작 후 pointer lock으로 마우스를 고정하고 WASD로 이동·조준한다 |
| A3 | 벽·엄폐물 | 외벽·엄폐벽을 통과할 수 없고, 가려진 드론은 이동해야 보인다 |
| A4 | 발사 | 클릭 한 번에 한 발과 발사 효과. 누르고 있어도 연사하지 않는다 |
| A5 | 명중·점수 | 벽 앞의 가장 가까운 드론 하나만 맞아 +10점. 벽·빗맞힘은 0점 |
| A6 | 드론 재등장 | 명중 효과 후 사라지고, 실제 플레이 시간 0.8초 뒤 같은 곳에 나타난다 |
| A7 | 화면·종료 | 점수·남은 시간·조작 안내가 HUD에 표시되고, 60초 후 조작·득점이 멈춘다 |
| A8 | 일시정지 | Esc·창 전환 시 입력·시간·재등장이 멈추고, 계속하기로 재개한다 |
| A9 | 다시 시작 | 일시정지·종료 화면에서 점수·60초·위치·드론 5개를 초기화한다 |
| A10 | 입력 실수 방지 | 시작·계속하기 클릭은 발사하지 않고, 정지·재시작 시 눌린 키를 해제한다 |
| A11 | 과제 범위 | 외부 이미지·3D model·audio·추가 게임 패키지와 범위 밖 기능을 넣지 않는다 |

시각 디자인은 장난감 같은 low-poly SF 분위기 안에서 자유롭게 정하게 했다.
multiplayer·login·storage·enemy AI·health·jump·weapon selection·mobile은 범위 밖이다.

</details>

입력은 baseline이 공통 본문만, package 조건이 절차 wrapper와 공통 본문을 이어 붙인 한 번의 입력이다.
package가 요구하는 설계 승인·사용자 선택 대기는 "사용자 사전 위임에 따른 자율 결정"으로 처리하게 했다.
그래서 이 비교는 package 원형 그대로가 아니라 공통 자율 실행 조건에서 package의 workflow를 적용한 결과다.

모든 조건은 같은 container·proxy·Claude Code 설정과 browser 검증 환경을 썼다.

<details markdown="1">
<summary>같은 환경을 재현하려면 펼치기: 격리·네트워크·Claude Code·browser 검증 설정</summary>

| 항목 | 이번 실행의 설정 |
|---|---|
| 격리 | 프로젝트마다 Claude Code container 하나, 자기 프로젝트 폴더만 mount |
| 네트워크 | 전용 proxy로 public HTTP·HTTPS와 호스트의 Langfuse만 연결 |
| Claude Code | 2.1.273, model claude-opus-5, effort high, 권한 모드 bypassPermissions |
| subagent 모델 | package가 정하는 대로 두고 따로 기록 |
| browser 검증 | Node.js 22.23.2, Playwright 1.63.0, Chromium 153.0.8010.12, Xvfb, software WebGL, 1280×720 |
| 관측 | Langfuse trace와 로컬 transcript를 대조해 model·tool·skill 호출과 token 집계 |

</details>

실행은 2026-09-16 하루에 했다.
baseline은 도중에 browser runtime을 보강하고 session을 재개해 입력이 2회다.
Matt Pocock은 "이어서 계속 진행해줘"를, gstack은 OAuth 만료 뒤 재개 입력을 한 번 더 넣었다.

{: #runs}
## 여섯 조건 모두 구현 뒤 확인·수정·재검증으로 갔지만 구성은 달랐다

아래는 실제 호출·산출물·수정·재검증 기록으로 확인한 흐름이다.
Skill·Agent 열은 Langfuse와 transcript를 대조했다(gstack 후반은 transcript만).

| 조건 | 실제로 진행한 흐름 | 불린 Skill | 불린 Agent |
|---|---|---|---|
| baseline | 구현, 로직 검사, 화면 수정, 재검증 | 0회(Bash 101회, Read 11회) | 0개 |
| Ponytail | full 진입, 최소 구현·화면 확인, ponytail-review, 재검증 | `ponytail`(full), `ponytail-review` | 0개 |
| Matt Pocock | 요구 질문·domain 정리, TDD, Standards·Spec 두 축 review | `setup-matt-pocock-skills`, `ask-matt`, `grill-with-docs`, `grilling`, `domain-modeling`, `implement`, `tdd`, `code-review` | Standards axis review, Spec axis review 2개 |
| ECC | feature-dev, explorer·architect agent, TDD, code-reviewer·verification-loop | `feature-dev`, `tdd-workflow`, `verification-loop` | `code-explorer`, `code-architect`, `code-reviewer` 3개(모두 Sonnet 5) |
| Superpowers | brainstorming·12 task 계획, task별 구현·review agent, 병합 뒤 검증 | `using-superpowers`, `brainstorming`, `writing-plans`, `using-git-worktrees`, `subagent-driven-development`, `verification-before-completion`, `finishing-a-development-branch` | task별 구현·review·재리뷰와 전체 branch 리뷰 20개(Opus·Sonnet·Haiku) |
| gstack | office-hours, autoplan 4단계 리뷰, 구현, specialist 6개·adversarial review, qa | `office-hours`, `autoplan`, `review`, `qa` | spec review 3개, CEO·Design·DX·Eng 계획 리뷰 4개, specialist 6개, adversarial 1개로 14개(모두 Sonnet 5) |

Matt Pocock은 `to-spec`·`to-tickets`를 단일 context로 충분하다고 판단해 부르지 않았다.
ECC에서 실제 발화한 hook은 GateGuard pre-bash 검사뿐이었다.

baseline도 추가 스킬 없이 스크린샷을 읽고 조명·무기·명중 효과를 고쳤다.
"TDD를 했다"는 보고도 실제 출력 순서를 대조해야 한다.
Superpowers의 첫 RED는 모듈이 아직 없어서 난 오류였고, assertion으로 버그를 재현한 RED와는 다르다.

{: #comparison}
## 작업 시간은 27분에서 2시간 8분, 입력 token은 3.68M에서 149.75M까지 벌어졌다

main 모델은 모두 Opus 5 / high다.
아래 값은 subagent와 cache 읽기를 포함한 기록값이다.

| 조건 | 사용자 입력 | 작업 시간 | 입력 token | 출력 token | model / tool 호출 | Skill / subagent |
|---|---|---:|---:|---:|---:|---:|
| baseline | 2회, 환경 변경 1회 | 44분 33초 | 13,278,574 | 147,127 | 112 / 112 | 0 / 0 |
| Ponytail | 1회 | 27분 29초 | 3,679,831 | 52,747 | 44 / 44 | 2 / 0 |
| Matt Pocock | 2회, 계속 진행 1회 | 47분 9초 | 22,286,304 | 164,797 | 161 / 162 | 8 / 2 |
| ECC | 1회 | 59분 55초 | 30,008,337 | 237,333 | 173 / 226 | 3 / 3 |
| Superpowers | 1회 | 2시간 8분 23초 | 57,679,203 | 546,253 | 544 / 571 | 7 / 20 |
| gstack | 2회, 인증 재개 | 2시간 5분 18초 | 149,752,247 | 524,552 | 357 / 380 | 4 / 14 |

테스트 수·문서량·commit 수는 규모이지 품질 순위가 아니다.

| 조건 | 앱 / 검사 LOC | 자체 unit 통과 | 자체 browser 통과 | PNG / 문서 / commit |
|---|---:|---:|---:|---:|
| baseline | 1,602 / 1,307 | 57 / 57 | 67 / 67 | 10 / 3 / 5 |
| Ponytail | 307 / 336 | 7 / 7 | 34 / 34 | 7 / 0 / 0 |
| Matt Pocock | 1,370 / 1,007 | 42 / 42 | 47 / 47 | 12 / 10 / 4 |
| ECC | 1,841 / 1,241 | 95 / 95 | 33 / 33 | 12 / 8 / 10 |
| Superpowers | 1,071 / 1,284 | 55 / 55 | 144 / 144 | 7 / 3 / 23 |
| gstack | 1,705 / 1,471 | 77 / 77 | 20 / 20 그룹 | 21 / 4 / 6 |

gstack의 browser 20은 시나리오 그룹 수라 다른 조건의 assertion 수와 직접 비교할 수 없다.

<details markdown="1">
<summary>숫자를 그대로 인용하려면 펼치기: 작업 시간·token·LOC의 집계 정의</summary>

- 작업 시간은 turn duration의 합이다. 모델·도구·hook 시간을 포함하고 중복·중단·입력 대기는 뺐다. CPU 시간이 아니다.
- 입력 token은 cache 읽기를 더한 누적 처리량이라 고유 prompt 길이와 다르다. 출력 token에는 thinking이 포함된다.
- gstack은 background 알림 뒤 자동으로 이어진 실행을 관측 hook이 수집하지 못해 Langfuse에 model 69/357, tool 69/380만 남았다. 인증 중단 구간과는 별개로 빠진 것이라, 그 구간은 transcript 전체로 셌다. 나머지 다섯은 Langfuse와 transcript 집계가 일치한다.
- LOC는 공백·주석을 포함한 physical line이고 node_modules·dist·lockfile은 뺐다.
- Langfuse의 cost 0은 이 인스턴스에 모델 가격을 넣지 않은 결과이지 무료 실행이 아니다.

</details>

{: #quality}
## 독립 평가에서는 baseline과 gstack이 필수 요구 미충족, 나머지 넷은 판정 보류였다

자체 검사 통과 수를 품질 점수로 바꾸지 않으려고 발표 당일(2026-09-17) 산출물 독립 평가를 따로 돌렸다.
평가 환경이 조건마다 같은 플레이 시나리오를 실제 mouse·keyboard로 3회 돌렸다.
조건명을 가린 두 별도 context가 그 기록과 코드를 따로 채점했다.
사람 검토는 아직 하지 않았다.

**평가 항목**

- **필수 요구 11개(A1–A11)**: 충족 / 미충족 / 판정 보류
- **품질 6개 축(각 0~10점)**: 기능 정확성 · 상태·경계 · 플레이·UI · 유지보수성 · 검증 산출물 · 실행·인수인계

| 조건 | 필수 요구 | 사유 |
|---|---|---|
| baseline | **미충족** | 60초 라운드 종료 지연 |
| gstack | **미충족** | 플레이 HUD에 조작 안내 누락 |
| Ponytail · Matt Pocock · ECC · Superpowers | 판정 보류 | 확인된 실패는 없고 재등장·종료 타이밍 등 일부 관측이 미확정 |

- 기능 정확성과 상태·경계는 미확인 항목을 최솟값으로 쳐도 여섯 조건 모두 10점 만점에 7.5점 이상이었다.
- 플레이·UI와 유지보수성은 미확인 항목 때문에 한 조건 안에서도 가능한 점수 폭이 넓어(예: 2.0~8.7점) 우열로 읽지 않는다.
- 항목 합산과 종합 순위는 두지 않았다.

{: #limits}
## 이 실험으로 조건의 보편적 우열은 판단할 수 없다

앞 절들이 보여 준 것은 실행 흐름의 차이와 이번 산출물 한 벌의 판정까지다.

- 과제가 하나이고 조건당 생성이 1회다. 반복 평가는 같은 산출물의 재현성 검사였다.
- 입력 횟수와 중간 환경 변경이 조건마다 달랐다(투입량 표의 사용자 입력 열).
- subagent 모델이 다르다. ECC·gstack은 Sonnet 5, Superpowers는 Opus·Sonnet·Haiku를 섞어 썼다.
- 검사 단위와 범위가 조건마다 다르다.
- software WebGL 환경이라 실물 GPU와 마우스 체감은 재지 않았다.
