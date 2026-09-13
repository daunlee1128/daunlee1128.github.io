---
type: tech
kind: troubleshooting
title: "가드레일에 한 번 막힌 Claude Code 세션이 무해한 입력에도 계속 막힌다"
date: 2026-09-07
stack: [mitmproxy, claude-code]
summary: "DROP TABLE이 적힌 문서를 읽은 Claude Code 세션이 그 뒤로 계속 막혔다. system에 이어 tool_result도 차단 검사에서 뺐다."
---

`DROP TABLE`이 적힌 문서를 읽은 Claude Code 세션이 그 뒤로 계속 막혔다.
`system`에 이어 `tool_result`도 차단 검사에서 뺐다.
검사에서 뺄 것을 가르는 기준을 얻는다.
독자는 AI 코딩 CLI 요청 앞에 인라인 가드레일을 운영 중인 사람이다.
답은 [사람이 친 글자를 기준으로 검사 범위를 좁힌 절](#fix)에 있다.

바로 할 것:

1. 가드레일 repo 루트에서 마지막 차단 이벤트를 찾는다.

   ```bash
   jq 'select(.event=="blocked")' logs/claude_audit.jsonl | tail -1
   ```

2. 검사기가 새 입력만 보는지 `messages` 이력 전체를 보는지 확인한다.
3. 도구 출력 속 파괴적 SQL 탐지를 포기할 수 있는지 판단한다.
4. 가능하다면 검사 범위를 아래 답 절의 입력 구분으로 좁힌다.
5. `tool_result` 제외와 직접 입력 차단을 회귀 테스트로 함께 확인한다.

{: #situation}
## 문서 읽기 다음 요청부터 세션이 막혔다

Claude Code 요청은 로컬의 mitmproxy 가드레일을 거쳐 외부 LLM API로 나간다.
OAuth 토큰은 건드리지 않고 요청 body만 검사한다.
정책은 PII 탐지·마스킹과 파괴적 SQL 차단이다.

2026-07-02, 프록시를 거친 세션에 워크스페이스 요약을 맡겼다.
세션이 가드레일 repo의 트러블슈팅 문서를 통째로 읽었다.
그 문서 14행에 `DROP TABLE`이 있었다.
읽기 결과를 실은 다음 요청이 403으로 막혔다.
재로그인해도 무해한 입력을 보낼 때 같은 증상이 났다.
사고를 진단하던 세션도 가드레일 코드 주석을 읽은 뒤 막혔다.
두 파일 모두 앞선 오탐을 설명하려고 적은 예시였다.

감사 로그에서 첫 세션은 5연속 403으로 끝났다.
22초 뒤 시작한 새 세션도 4연속 403으로 끝났다.
이는 2026-07-02의 두 세션을 시간순으로 대조한 결과다.

<details markdown="1">
<summary>재로그인 안내를 봤다면 펼치기: 그날의 차단 로그와 실제 응답</summary>

Claude Code는 이 사건에서 “Please run /login”을 표시했다.
[미확인: GUARD-8 · 2026-07-02 당시 Claude Code 버전]
이 표시만으로 인증 실패를 단정할 수 없었다.

아래는 첫 차단 로그에서 요청 식별자를 뺀 줄이다. 시각은 UTC다.

```json
{"ts":"2026-07-02T05:51:34.459863+00:00","event":"blocked","path":"/v1/messages?beta=true","rule":"drop_table","severity":"high","message":"destructive SQL"}
```

`drop_table` 룰과 응답 생성 코드를 대조하면 HTTP 403의 body는 아래와 같다.
클라이언트 표시와 프록시의 오류 타입을 구분해야 한다.

```json
{"type":"error","error":{"type":"guardrail_blocked","message":"destructive SQL"}}
```

코드 확인일은 2026-09-12다. 검사기 오류로 닫는 경로는 503 `guardrail_error`다.
감사 로그의 `request_body`는 20,000자에서 잘린다.
그래서 이 로그만으로 매칭 문자열이 어느 블록에 있었는지는 확정하지 못한다.

</details>

{: #diagnosis}
## 이력에 남은 도구 출력이 다음 턴에도 검사됐다

앞선 수정에서는 top-level `system`을 차단 검사에서 제외했다.
하지만 `user` 메시지 안의 `tool_result`를 모으는 분기는 남아 있었다.
이 위치는 로그 전문 대신 수정 커밋과 회귀 테스트로 확인했다.
테스트 주석은 이 사례를 2026-07-02의 오탐 변형으로 명시한다.

이력은 다음 요청에도 다시 간다.
따라서 과거 도구 출력이 검사 대상이면 새 입력을 바꿔도 같은 룰에 걸린다.

<details markdown="1">
<summary>다른 원인을 어떻게 가렸는지 보려면 펼치기: 확인 방법과 남은 구간</summary>

| 가설 | 무엇으로 확인했나 | 어디까지 판정했나 |
|---|---|---|
| 인증·토큰 만료 | 재로그인 뒤 재요청과 `guardrail_blocked` 응답 | 인증만으로 설명되지 않음 |
| 새 입력의 파괴적 SQL | 무해한 입력에서도 같은 세션 차단 | 새 입력만이 원인은 아님 |
| `system` 제외로 해결 | 수정 전 수집 코드와 tool_result 회귀 테스트 | 도구 출력 분기가 남아 있었음 |
| 가드레일이 꺼진 구간에도 차단 | 감사 로그와 실제 컨테이너 가동 구간 대조 필요 | [미확인: GUARD-9 · 껐다고 알았던 구간과 실제 가동 구간] |

마지막 행의 대조 결과는 복원하지 못했다.
여기서 확인하는 것은 검사 제외 기준까지다.

</details>

{: #fix}
## 사람이 친 글자를 기준으로 `system`과 `tool_result`를 검사에서 뺐다

이 글의 조건: mitmproxy 로컬 인라인 프록시, Messages API 요청 body 검사.
mitmproxy 버전은 미확인이다. Claude Code 버전은 GUARD-8에 남겼다.
사건은 2026-07-02, 제외 코드를 고친 날은 2026-07-14다.

기준은 “사람이 친 글자인가”다.
구현은 `user` 메시지의 문자열·`text` 블록을 모은다.
그 안의 `<system-reminder>` 주입 문구도 뺀다.
이는 신뢰된 클라이언트의 입력 형식에 기대는 기준이다.

| 요청에 실린 입력 | 사람이 친 글자인가 | 앞선 수정에서 | 이번 수정에서 |
|---|---|---|---|
| top-level `system` | 아니다 | 제외 | 제외 |
| `user` 안의 `tool_result` | 아니다 | 검사 | 제외 |
| 사용자가 직접 친 프롬프트 | 그렇다 | 검사 | 검사 |

`tool_result`는 `role: "user"` 안에 실린다.
그래서 `role`만으로는 직접 입력과 도구 출력을 나눌 수 없다.
PII 마스킹은 도구 출력에도 계속 적용한다.

`tool_result` 안의 `DROP TABLE`은 회귀 테스트에서 통과한다.
옆의 직접 입력에 같은 문자열을 넣으면 차단한다.
고친 뒤 검증 근거는 이 테스트까지다.
수정 뒤 실제 세션을 재현한 기록은 확보하지 못했다.

막힌 요청을 분석할 때는 `role`과 content의 `type`을 함께 보라.
로그가 잘렸다면 그 로그만으로 매치 위치를 확정하지 않는다.

<details markdown="1">
<summary>제외 코드를 검토하려면 펼치기: API 계약, 코드 발췌와 테스트 출력</summary>

Messages API는 호출자가 대화 이력을 보내는 무상태 API다.
2026-09-12에 [Messages API 문서](https://platform.claude.com/docs/en/build-with-claude/working-with-messages)를 확인했다.

아래는 리스트형 content를 모으는 분기의 발췌다.
수정에서는 `tool_result`를 순회하는 분기를 제거했다.
`take`는 문자열에서 `<system-reminder>`를 제거해 수집한다.

```python
# collect_text 안: role == "user"를 확인한 뒤의 리스트 분기
for blk in content:
    if not isinstance(blk, dict):
        continue
    if blk.get("type") == "text":
        take(blk.get("text"))
```

2026-09-12에 가드레일 repo 루트에서 내장 러너를 실행했다.
아래는 출력의 마지막 줄이다. 전체 36개 중 이번 조치의 회귀 테스트는 4개다.

```bash
python3 tests/test_guardrail.py
```

```text
36/36 passed
```

4개는 리스트·문자열형 도구 출력 제외, 수집 결과, 나란한 직접 입력 차단을 검사한다.
실제 프록시를 통과시키는 부하 테스트 결과는 아니다.

</details>

{: #limits}
## 도구 출력 탐지를 포기하고도 남는 오탐은 있다

도구가 읽어 온 파일에 실제 파괴적 SQL이 있어도 차단 검사를 통과한다.
악의적인 클라이언트가 직접 입력을 `tool_result`로 위장해도 막지 못한다.
이 처방은 신뢰된 코딩 CLI의 오사용 감시에만 적용했다.

<details markdown="1">
<summary>더 싼 조치를 먼저 검토하려면 펼치기: 새 세션부터 비교한 대안</summary>

| 대안 | 어디까지 판단했나 | 근거 종류 |
|---|---|---|
| 새 세션으로 시작 | 새 세션도 4연속 차단, [미확인: GUARD-4 · 같은 파일을 다시 읽어 재발한 것인지] | 로그 확인 |
| `system`만 제외한 상태 유지 | 도구 출력 분기가 남아 같은 부류를 놓침 | 코드·회귀 테스트 확인 |
| 새로 붙은 turn만 검사 | [미확인: GUARD-3 · 실제 비교 여부, 기각 이유와 근거 종류] | 미확인 |

복구 문서에 남은 방법은 프록시를 거치지 않는 환경에서 세션을 재개하는 것이다.
그 환경을 먼저 준비한 뒤 아래 명령을 쓴다. 명령 자체가 프록시를 끄지는 않는다.

```bash
claude --resume
```

</details>

[Bedrock의 오탐 조정 안내](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-harmful-content-handling-options.html)는 탐지 모드와 필터 강도를 다룬다.
이 글의 차이는 검사기에 넣을 텍스트의 출처를 가른 데 있다.
문서 비교일은 2026-09-12이며, 이 구현은 Bedrock Guardrails를 쓰지 않는다.

블록 형식만으로 사람이 쓴 글인지 완전히 가릴 수는 없다.
태그 없이 `text`에 주입되는 내용은 여전히 검사 대상이다.
이력 전체를 검사하는 구조도 남아서, 다른 오탐이 나면 후속 턴까지 막힐 수 있다.
