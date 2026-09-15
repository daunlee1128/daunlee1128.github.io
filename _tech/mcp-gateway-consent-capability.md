---
type: tech
kind: troubleshooting
title: MCP 게이트웨이 뒤에서 동의 화면이 안 뜬다
date: 2026-09-07
stack: [agentcore, claude-code]
summary: REQUEST interceptor가 클라이언트의 부족한 MCP capability를 대신 선언했지만, RESPONSE interceptor가 Gateway의 실제 응답 모양(dict)을 list로 잘못 가정해 그대로 통과시켰다. dict를 list로 바꿔 순회하도록 고치고 라이브에서 재현·확인했다.
---

AgentCore Gateway 앞의 interceptor가 capability를 대신 선언해 줬는데도, 신규 사용자의 첫 tool 호출은 동의 화면 대신 클라이언트 오류로 끝났다.
로그와 코드를 대조해 원인을 인터셉터의 응답 파싱 한 곳으로 좁히고 고쳤다.
capability를 대신 선언해도 그다음 응답의 실제 모양을 다르게 가정하면 새는 자리가 생긴다.

독자는 AgentCore Gateway 앞에 interceptor를 붙인 사람이다.
클라이언트가 못 하는 MCP capability 선언을 그 interceptor가 대신 채워 준다.
답은 [응답 파싱을 고친 절](#fix)에 있다.

{: #situation data-k="SITUATION"}
## 어디서, 무엇을 하다가

이 Gateway는 MCP `2026-07-28`만 쓰도록 구성돼 있었다. 이 버전은 `initialize` 핸드셰이크가 없다(2026-09-03 확인).
클라이언트는 매 `tools/call` 요청의 `_meta.io.modelcontextprotocol/clientCapabilities`로 capability를 선언해야 한다.
선언이 아예 없으면 `-32602`가 돌아온다.
3LO consent(elicitation)에 필요한 capability를 안 알리면 [`-32021`][aws-elicitation](HTTP 400, 인가 URL 없음)이 돌아온다.

클라이언트가 url mode capability를 스스로 안 알린다는 것은 더 이른 단계(2026-08-31)에 처음 발견됐다.

<details markdown="1">
<summary>첫 발견 경위를 볼 사람이 펼치기: local mock 캡처와 당시 오류</summary>

local mock MCP server로 Claude Code 2.1.236의 `initialize` 요청을 캡처하니 다음과 같았다.

```json
{
  "requested_protocol_version": "2025-11-25",
  "declared_capabilities": {
    "roots": { "listChanged": true },
    "elicitation": {}
  }
}
```

`elicitation`을 선언하긴 하지만 그 아래 url mode 선언이 없다. 이 캡처는 `tools/call`이 없어 매 요청 `_meta` 선언 여부까지는 못 봤다.
그래도 같은 시기 실제 plugin 호출에서 받은 `-32021 Missing required client capability`와는 맞아떨어졌다.

</details>

이 gap을 메우려고 REQUEST interceptor를 붙였다. `tools/call` 요청의 `_meta`에 `elicitation.url` 하위 capability가 없을 때만 채워 넣는다(이미 있으면 손대지 않는다).

```python
elicitation = capabilities.get("elicitation")
if not isinstance(elicitation, dict):
    elicitation = {}
    capabilities["elicitation"] = elicitation
if "url" not in elicitation:
    elicitation["url"] = {}
    decision = "inject"
```

{: #symptom data-k="SYMPTOM"}
## 보이는 것

이미 유효한 Token Vault grant가 있는 사용자로 먼저 실측했다(2026-09-07 11:27 KST). CloudWatch에 REQUEST `decision=inject`, RESPONSE `decision=pass status=200`이 찍혔다. 하지만 이 사용자는 grant가 있어 애초에 동의 challenge가 발생하지 않았다.
RESPONSE 쪽이 실제로 URL을 찾아 안내 문구로 바꾸는지는 이 시험만으로는 알 수 없었다.

grant가 없는 신규 사용자로 다시 시험했다(같은 날 12:55:03 KST). REQUEST는 똑같이 `decision=inject`, RESPONSE도 `decision=pass status=200`이었다. 그런데 Claude Code는 동의 화면 대신 다음 오류로 끝났다.

```text
Client does not support URL-mode elicitation requests
```

{: #root-cause data-k="ROOT CAUSE"}
## 가설 → 확인

RESPONSE interceptor는 `_authorization_url`이라는 함수로 Gateway 응답의 `inputRequests`에서 인가 URL을 찾는다. 확인한 내용을 정리하면 다음과 같다.

| 가설 | 확인 방법 | 판정 |
|---|---|---|
| Gateway가 capability 선언 부족으로 거절했다(`-32021`) | CloudWatch 로그의 status 코드 대조 | 기각 — `-32021`은 HTTP 400인데 실제 status는 200이었다 |
| 그 오류 문구가 Gateway의 `-32021`을 클라이언트가 다르게 표시한 것 | Claude Code 2.1.263 바이너리에 `strings` 실행 | 기각 — 문구가 바이너리 안에 그대로 있는 client-side 문자열이었다 |
| RESPONSE interceptor가 Gateway의 실제 응답 모양을 못 읽어 그대로 통과시켰다 | `_authorization_url` 코드와 Gateway가 실제로 보낸 `inputRequests` 모양 대조 | 확인 |

status 200과 client-side 거절이 함께 온다는 것은 Gateway가 실제로 URL-mode `input_required`를 돌려줬다는 뜻이다.
REQUEST interceptor의 capability 주입은 Gateway에 받아들여졌고, 문제는 그다음이었다.
RESPONSE interceptor의 `_authorization_url` 함수는 `inputRequests`를 list로만 순회했다.
그런데 Gateway는 요청 id를 key로 하는 dict(map)를 보냈다.
dict를 그대로 순회하면 key 문자열만 나오고 그 안의 `url`은 못 찾는다.
함수는 `None`을 반환했고, 인터셉터는 "elicitation 아님"으로 오판해 원본 응답을 그대로 통과시켰다.

{: #fix data-k="FIX"}
## RESPONSE interceptor가 dict 모양 응답도 읽도록 고쳤다

이 글의 조건: Gateway는 MCP `2026-07-28`만 활성화하도록 구성돼 있었고, 관측한 클라이언트는 Claude Code 2.1.263, interceptor는 Python 3.12 Lambda다.

`inputRequests`가 dict면 list로 바꿔 순회하도록 6줄을 더했다.

```diff
     result = body.get("result")
     if isinstance(result, dict) and result.get("resultType") == "input_required":
-        for request in result.get("inputRequests", []):
+        input_requests = result.get("inputRequests", [])
+        # Gateway는 inputRequests를 요청 id를 key로 하는 map으로 보낸다(2026-09-07 live). list도 허용.
+        if isinstance(input_requests, dict):
+            input_requests = list(input_requests.values())
+        if not isinstance(input_requests, list):
+            input_requests = []
+        for request in input_requests:
             if not isinstance(request, dict):
                 continue
```

찾은 URL은 `USER_MESSAGE.format(url=url)`로 안내 문구에 담아 `resultType: complete`인 200 응답으로 바꾼다.
클라이언트는 이제 raw challenge 대신 사람이 읽을 안내를 받는다. dict 모양을 재현하는 회귀 테스트를 추가했다(11건 PASS).
Lambda를 다시 배포했다.

재배포 뒤 같은 사용자로 다시 호출하자 로그 경로가 `inject → rewrite`로 바뀌었다.
실제로 연결 안내 문구와 AgentCore authorize URL을 받았다 — 수정 자체는 라이브에서 재현·확인됐다.
(그 뒤 브라우저에서 Keycloak 로그인·Atlassian 동의까지 진행했지만 콜백 앱이 별도 사유로 실패했다. 이건 다른 컴포넌트의 문제라 여기서 다루지 않는다.)

{: #prevention data-k="PREVENTION"}
## 이 처방이 새로 만드는 것

이 수정에는 대가가 있었다. 내부 테스트 harness는 같은 버그 덕분에 raw `input_required` 응답을 직접 받아 파싱하고 있었다.
수정 뒤에는 harness도 사람이 읽는 안내 문구를 받게 돼 그 자동 처리가 깨진다.
실제 클라이언트와 자동화 도구가 같은 응답에서 다른 것을 기대한다면, 그 응답을 바꾸는 수정은 둘의 공존 방식까지 함께 결정해야 한다.

[aws-elicitation]: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-mcp-elicitation.html
