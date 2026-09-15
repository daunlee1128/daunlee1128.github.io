---
type: tech
kind: troubleshooting
title: 문서를 읽은 Claude Code 세션이 이후 요청에서도 계속 막힌다
date: 2026-09-07
stack: [mitmproxy, claude-code]
summary: mitmproxy 가드레일이 tool_result까지 검사에 넣어, DROP TABLE이 적힌 문서를 읽은 Claude Code 세션이 이후 요청에서도 계속 막혔다. tool_result를 검사에서 빼 사람이 친 글자만 보도록 고쳤다.
---

`DROP TABLE`이 적힌 문서를 읽은 Claude Code 세션이 그 뒤로 계속 막혔다.
`system`에 이어 `tool_result`도 차단 검사에서 뺐다.
검사에서 뺄 것과 남길 것을 가르는 기준을 얻는다.
독자는 Claude Code 같은 AI 코딩 CLI 요청 앞에 인라인 가드레일을 직접 운영하는 사람이다.
답은 [사람이 친 글자를 기준으로 검사 범위를 좁힌 절](#fix)에 있다.

{: #situation}
## 문서 읽기 다음 요청부터 세션이 막혔다

Claude Code 요청은 로컬의 mitmproxy 가드레일을 거쳐 외부 LLM API로 나간다.
OAuth 토큰은 건드리지 않고 요청 body만 검사한다.
정책은 PII 탐지·마스킹과 파괴적 SQL 차단이다.

2026-07-02, 프록시를 거친 세션에 워크스페이스 요약을 맡겼다.
세션이 가드레일 저장소의 트러블슈팅 문서를 읽었다.
그 문서에는 앞선 오탐 사례를 설명하려고 적어 둔 `DROP TABLE` 예시가 있었다.
읽기 결과를 실은 다음 요청이 403으로 막혔다.

감사 로그에 남은 그 세션의 마지막 기록은 403 5회 연속이다.
약 22초 뒤 다른 세션도 몇 차례 성공하다가 403을 받기 시작해, 로그에는 4회 연속까지 남아 있다.
이 세션은 가드레일 코드 파일 `content.py`를 읽은 직후 첫 403을 받았다.
이 파일 자체에도 이 버그를 설명하는 예시로 `DROP TABLE` 문자열이 있다.

{: #diagnosis}
## 도구 출력도 검사 대상이면 이력에 남은 파일 내용이 계속 걸린다

검사 대상 텍스트는 가드레일 코드의 `collect_text` 함수가 모은다. 이 함수를 기준으로 세 가설을 확인했다.

| 가설 | 무엇으로 확인했나 | 판정 |
|---|---|---|
| 인증·세션 만료 | 403 응답 오류 타입 `guardrail_blocked`(인증 실패와 다른 코드 경로) | 인증 실패가 아님 |
| 그때그때 새로 입력한 내용의 문제 | [Messages API][messages-api]의 무상태 이력 재전송 구조(문서 확인 2026-09-15) | 새 입력뿐 아니라 이력에 남은 과거 도구 출력도 검사 대상 |
| 이미 적용된 `system` 제외로 충분 | 수정 전 `collect_text`에 남아 있던 `tool_result` 순회 분기 | 도구 출력 분기가 원인 |

감사 로그의 `request_body`는 20,000자에서 잘린다. 그래서 이 로그만으로 어느 블록이 매치됐는지는 확정하지 못했다.
확정한 것은 이력에 `tool_result`로 남은 파일 내용이 검사 대상이었다는 코드상의 사실이다.

{: #fix}
## 사람이 친 글자를 기준으로 `system`과 `tool_result`를 뺐다

이 글의 조건: mitmproxy 로컬 인라인 프록시, Messages API 요청 body 검사, Claude Code 클라이언트.
사건은 2026-07-02, 코드를 고친 날은 2026-07-14(커밋 `3dc6e4f`)다.

기준은 "사람이 친 글자인가"다. 구현은 `role: "user"` 메시지의 `text` 블록만 모은다.

| 요청에 실린 입력 | 사람이 친 글자인가 | 수정 전 차단 검사 | 수정 후 차단 검사 |
|---|---|---|---|
| top-level `system` | 아니다 | 제외 | 제외 |
| `user` 메시지 안의 `tool_result` | 아니다 | 포함 | 제외 |
| 사용자가 직접 친 프롬프트 | 그렇다 | 포함 | 포함 |

`tool_result`도 `role: "user"` 안에 실린다. `role`만으로는 사람이 친 것과 도구가 만든 것을 가를 수 없다.
마스킹(PII 탐지)은 이 구분과 상관없이 종전대로 전체 메시지에 적용한다.

회귀 테스트 4개로 확인했다. `tool_result` 안의 `DROP TABLE`은 통과하고, 나란히 놓인 사용자 직접 입력의 같은 문자열은 그대로 차단된다(`tests/test_guardrail.py` 2026-09-15 재확인, 36/36 pass).

{: #limits}
## 도구 출력 검사를 포기하고도 남는 위험은 있다

도구가 읽어 온 파일에 실제 파괴적 SQL이 있어도 이제는 검사를 통과한다.
악의적인 클라이언트가 사용자 입력을 `tool_result` 블록으로 위장해도 막지 못한다.
이 경계는 보안 경계가 아니라 신뢰된 클라이언트(Claude Code)의 오사용을 감시하는 장치다.

이미 막힌 세션은 프록시를 고친 코드로 재기동한 뒤 다시 요청해 확인한다.
기존 세션 복구가 필요하면 프록시를 거치지 않는 환경에서 세션을 재개한다.

```bash
claude --resume
```

[Bedrock Guardrails의 오탐 조정 안내][bedrock]는 탐지 강도를 다룬다(문서 확인 2026-09-15).
이 글의 차이는 검사에 넣을 텍스트의 출처를 가른 데 있다. 이 구현은 Bedrock Guardrails를 쓰지 않는다.

[bedrock]: https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-harmful-content-handling-options.html
[messages-api]: https://platform.claude.com/docs/en/build-with-claude/working-with-messages
