---
type: tech
kind: troubleshooting
title: "MCP 게이트웨이 뒤에서 동의 화면이 안 뜬다"
date: 2026-09-07
stack: [agentcore, keycloak, claude-code]
summary: "요청 시점에는 tools/call.params._meta 아래에 url mode 선언을 넣는다. 응답 시점에는 고정 온보딩 주소가 든 성공 text로 바꾼다."
---

고칠 수 있는 자리를 넷 적고, 남은 게이트웨이 경계에 인터셉터를 뒀다.
사내 로그인은 됐다.
동의 이력이 없는 사용자의 첫 tool 호출은 거절됐다.
실측 capability와 주입 위치를 대조해 url mode 부재로 범위를 좁혔다.

독자는 AgentCore Gateway로 사용자별 3LO를 운영하는 사람이다.
답은 [“인터셉터가 url mode를 주입하고 온보딩 앱으로 이었다” 절](#boundary-url-bridge)에 있다.

바로 할 것:

1. `initialize`를 쓰는 version이면 local mock에서 capability를 캡처한다.
2. `elicitation: {}`를 url mode 지원으로 해석하지 않는다.
3. 운영이 `2026-07-28`이면 `tools/call.params._meta`를 확인한다.
4. url 응답도 HTTP 200, `resultType: complete`, `content[].type: text`로 바꾼다.
5. 동의 시작과 완료가 같은 사용자 token에 묶이는지 확인한다.

{: #first-call-url-mode }
## 첫 tool 호출은 url mode capability에서 멈췄다

[미확인: MCP-1 · 사건의 날짜, 처음 막힌 사용자, 발견자와 발견 경로]

진입 로그인은 끝났다.
첫 tool 호출은 HTTP 400으로 거절됐다.
브라우저로 이동할 동의 안내는 나오지 않았다.

Gateway와 클라이언트에서 서로 다른 url mode 거절을 확인했다.
두 오류는 계층과 version이 달랐다.

<details markdown="1">
<summary>오류 계층을 대조할 사람이 펼치기: 주입 전과 주입 뒤의 문구</summary>

- Claude Code 2.1.236: Gateway가 HTTP 400, `-32021`로 거절했다.
  오류는 `Missing required client capability`였다.
- Claude Code 2.1.263: HTTP 200 뒤 클라이언트가 거절했다.
  오류는 `Client does not support URL-mode elicitation requests`였다.

</details>

{: #observed-capability }
## 실측 initialize에는 elicitation 빈 객체가 있었다

2026-08-31에 local mock MCP server로 Claude Code 2.1.236의 요청을 캡처했다.
관련된 값만 옮기면 다음과 같다.

```json
{
  "protocolVersion": "2025-11-25",
  "capabilities": {
    "roots": { "listChanged": true },
    "elicitation": {}
  }
}
```

`elicitation` 자체가 빠진 것은 아니었다.
[MCP 2025-11-25 규격][m]은 빈 객체를 form mode 지원으로 본다.
url mode를 지원하려면 `elicitation.url`을 따로 선언해야 한다.

{: #actual-check-order }
## 실제 확인 순서는 계획과 반대였다

계획은 동의 저장, version, elicitation 순이었다.
실제는 protocol·wire, IAM, url mode, 동의 저장, interceptor 순으로 갔다.

<details markdown="1">
<summary>확인 과정을 재현할 사람이 펼치기: 날짜별 순서와 세 가설의 판정</summary>

1. 08-28에 protocol과 wire부터 보고 header 누락과 IAM 403을 떼어냈다.
2. 08-31에 local mock으로 url mode 미선언을 확인했다.
3. 09-01에 Token Vault의 out-of-band 동의 저장을 확인했다.
4. 09-07에 interceptor의 `_meta` 주입으로 넘어갔다.

| 가설 | 확인 방법 | 근거 종류 | 판정 |
|---|---|---|---|
| 진입 로그인이 막음 | 같은 사용자의 로그인 결과 확인 | 실행 결과 | 기각, 로그인 완료 |
| tool 호출 경로가 깨짐 | 동의한 사용자의 같은 호출 확인 | 호출 결과 | 기각, 호출 성공 |
| url mode 선언이 없음 | local mock에서 `initialize` 캡처 | 요청 실측 | 확인, 빈 객체만 있음 |

운영에서 직접 조회한 것은 OAuth credential provider의 callback URL과 workload identity였다.
`get-gateway`를 실행한 증거는 없다.
Gateway의 supported version은 Terraform code에서 확인했다.

</details>

{: #request-meta }
## 운영 Gateway는 tools/call의 _meta에서 url mode를 확인했다

2026-09-12 공식 문서와 code를 대조했다.
운영 Gateway는 MCP `2026-07-28`만 지원했다.
이 버전은 `initialize`를 쓰지 않고 요청마다 capability를 받는다.
[AgentCore 공식 문서][a]도 `params._meta`에 capability를 두도록 요구한다.

따라서 캡처한 `initialize`만 고쳐서는 운영 요청의 빈자리가 채워지지 않는다.
실제 인터셉터도 `initialize`를 건드리지 않았다.
`tools/call` 요청 본문의 `_meta`만 보충했다.

| 고칠 자리 | 확인한 제약 | 근거 종류 | 판단 |
|---|---|---|---|
| Gateway 설정 | capability는 요청별 값 | 문서·code 확인 | 설정으로 대체할 항목 없음 |
| 클라이언트 | url mode 미선언 | 요청 실측 | 제품 수정 권한 없음 |
| MCP 규격 | url mode 명시 선언 요구 | 공식 문서 확인 | 규격 변경 대상 아님 |
| Gateway 경계 | 요청·응답 interceptor 존재 | 아래 항목 미확인 | 여기서 보충 |

[미확인: MCP-7 · Gateway 경계를 선택한 판단의 근거 종류]

{: #boundary-url-bridge }
## 인터셉터가 url mode를 주입하고 온보딩 앱으로 이었다

이 글의 조건: AgentCore Gateway는 MCP `2026-07-28`, 클라이언트 실측은 Claude Code 2.1.236·2.1.263, 인터셉터 runtime은 Python 3.12다.

요청 시점에는 `tools/call.params._meta` 아래에 url mode 선언을 넣는다.
응답 시점에는 `input_required`나 `-32042`에서 authorization URL을 찾는다.
그 URL을 그대로 넘기지 않고 고정 온보딩 주소가 든 성공 text로 바꾼다.
대리 선언만 넣으면 url mode를 처리하지 못하는 클라이언트에서 다시 막힌다.

온보딩 앱은 사용자 로그인을 받은 뒤 같은 사용자 JWT로 3LO를 시작한다.
대상 시스템이 돌려보내면 앱은 AgentCore Identity SDK를 호출한다.
이때 시작에 쓴 JWT를 `CompleteResourceTokenAuth`에 전달한다.
새 JWT로 완료하던 독립 콜백 모델은 폐기됐다.

<details markdown="1">
<summary>인터셉터를 검토할 사람이 펼치기: 요청 주입과 응답 변환 code 발췌</summary>

요청 발췌는 body와 하위 값이 dict인 정상 `tools/call`만 보여준다.
초기화, 형식 검사와 interceptor 반환은 생략했다.

```python
if transformed.get("method") == "tools/call":
    params = transformed.setdefault("params", {})
    meta = params.setdefault("_meta", {})
    capabilities = meta.setdefault(
        "io.modelcontextprotocol/clientCapabilities", {}
    )
    elicitation = capabilities.setdefault("elicitation", {})
    elicitation.setdefault("url", {})
```

응답 발췌는 authorization URL이 있고 native mode가 아닌 분기만 보여준다.
`returnUrl`이 있는 native 요청의 통과 분기와 형식 검사는 생략했다.

```python
request_id = body.get("id")
text = USER_MESSAGE.format(
    url=os.environ["ONBOARDING_URL"],
    service=os.environ.get("SERVICE_LABEL", "Atlassian"),
)
transformed = {
    "statusCode": 200,
    "body": {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "resultType": "complete",
            "content": [{"type": "text", "text": text}],
        },
    },
}
```

</details>

<details markdown="1">
<summary>동의 왕복을 구현할 사람이 펼치기: 경계와 온보딩 앱의 역할</summary>

2026-09-07 실측 기록에서 독립 콜백 모델의 실패를 확인했다.
31초 안에 `Invalid or expired session`이 돌아왔다.
설계 기록은 새 token의 사용자 ID 일치만으로 충분하다는 가정을 폐기했다.
JWT 값의 차이가 유일한 실패 원인이라고 확정한 것은 아니다.

| 구성 요소 | 맡은 일 | 맡지 않은 일 |
|---|---|---|
| 요청 interceptor | url mode capability 주입 | 사용자 동의 완료 |
| 응답 interceptor | authorization 응답을 온보딩 안내로 변환 | 권한 확대 |
| 온보딩 앱 | 같은 사용자 token으로 동의 시작·완료 | 일반 tool 결과 변환 |

</details>

이 글에서 확인한 범위는 요청·응답 변환 코드와 동의 완료 설계다.
일반 사용자 전체의 성공 관측으로 범위를 넓히지 않는다.

{: #new-constraints }
## 이 중계는 클라이언트 capability를 대신 말한다

인터셉터는 클라이언트가 보내지 않은 url mode 지원을 대신 선언한다.

- 클라이언트가 url mode를 지원하기 시작하면 대리 선언 조건을 다시 본다.
- 온보딩 앱은 시작 token과 완료 요청을 같은 사용자에게 묶는다.
- capability와 응답 형식의 변경을 한 묶음으로 추적한다.

[m]: https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation

[a]: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-mcp-elicitation.html
