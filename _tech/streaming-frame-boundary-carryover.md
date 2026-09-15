---
type: tech
kind: troubleshooting
title: Kong OSS 3.9.3의 invoke-stream은 200이어도 스트리밍하지 않았다
date: 2026-09-07
stack: [kong, bedrock]
summary: "문서 요약만 보고 설정을 preserve로 바꿨다가 500을 냈다. 재검증에서 invoke·invoke-stream 두 라우트가 계약을 지키지 않고 있다는 것도 드러났다."
---

설정 필드 하나가 어느 버전부터 있는지 문서 요약만 보고 넘겨짚어, native Bedrock 라우트가 연속으로 500을 냈다.
그래서 설정과 나머지 라우트를 전부 스키마와 실제 클라이언트로 다시 확인했다.
그 결과 라우트 두 개가 실제로는 계약을 지키지 않고 있었다는 게 드러났다.

독자는 Kong `ai-proxy`로 Bedrock native passthrough를 구성하고 여러 operation(라우트)을 운영하는 사람이다.
답은 [PDK로 바꾸고 라우트를 둘로 좁힌 절](#fix)에 있다.

{: #situation data-k="SITUATION"}
## 문서 요약만 보고 설정을 preserve로 바꿨다

OSS 전환 과정에서 native Bedrock passthrough 라우트 4종의 설정을 바꿨다. 근거는 "`llm_format`은 Kong
3.10.0.0 도입 → OSS 3.9.3엔 없다"는 전제였다. `route_type`을 `"llm/v1/chat"` + `llm_format:"bedrock"`에서
`"preserve"`로 바꾸고 `llm_format`은 지웠다. 라우트 4종은 invoke·converse·converse-stream·invoke-stream이다.

실 재검증(2026-07-22)에서 native 호출이 연속으로 500을 냈다.

<details markdown="1">
<summary>로그 원문을 볼 사람이 펼치기: 실제로 찍힌 두 에러</summary>

```text
"require 'cjson.safe' not allowed within sandbox"
[ai-proxy] bedrock.lua:629: attempt to index a nil value
```

</details>

{: #root-cause data-k="ROOT CAUSE"}
## 가설 → 확인

드라이버는 upstream URL을 만들 때 route 종류별 템플릿을 담은 `operation_map`이라는 테이블을 찾아 쓴다.

| 가설 | 확인 방법 | 판정 |
|---|---|---|
| pre-function의 JSON 파싱이 막혔다 | Kong 3.9.3 serverless-functions sandbox 동작 확인 | 확인 — sandbox가 `require('cjson.safe')` 자체를 차단한다 |
| `route_type:"preserve"`가 URL 구성에서 죽는다 | `ai-proxy` bedrock 드라이버 소스 확인 | 확인 — `preserve` 아래서 드라이버가 `operation_map["bedrock"]["preserve"]`(존재하지 않음)로 URL을 만들려다 nil index로 죽는다 |
| `llm_format`이 3.10+ 전용이다 | 실제 3.9.3 ai-proxy 스키마 직접 확인 | 기각 — 스키마에 `llm_format`이 있고, `llm/v1/chat` + `llm_format:"bedrock"`을 스키마가 강제한다("native provider options in llm_format can only be used with the 'llm/v1/chat' route_type") |

"3.10+에서 도입됐다"는 문서 요약이 오독이었다. `preserve`는 `llm_format`과 함께 쓸 수 없다. 단독으로 쓰면 드라이버가 bedrock URL을 못 만들어 500이었다.

여기서 멈추지 않고 소스를 더 읽었다. 이 드라이버가 실제로 다루는 upstream operation은 Converse 계열 2종뿐이다.
클라이언트가 어떤 경로로 불렀는지는 upstream에 전달되지 않는다.

<details markdown="1">
<summary>소스를 대조할 사람이 펼치기: driver·adapter가 라우트를 판별하는 방식</summary>

`kong/llm/drivers/bedrock.lua`는 upstream operation을 항상 `stream_mode and "converse-stream" or
"converse"`로 자체 재구성한다 — 파일에 `"invoke"` 문자열 자체가 없다. `kong/llm/adapters/bedrock.lua`는
path의 operation 문자열이 정확히 `converse-stream`일 때만 stream 모드로 판단한다. 이 adapter는 Converse
스키마 기준으로 요청과 응답을 정규화하는 왕복 변환기다.

</details>

{: #fix data-k="FIX"}
## PDK로 바꾸고 라우트를 둘로 좁혔다

이 글의 조건: Kong OSS 3.9.3, `ai-proxy` 플러그인, native Bedrock passthrough(`llm_format:bedrock`).

두 조치를 함께 적용해 500을 없앴다. pre-function의 JSON 파싱을 `require('cjson.safe')` 대신 Kong PDK
(`kong.request.get_body`/`kong.service.request.set_body`)로 바꿔 sandbox 차단을 피했다. `route_type`은
`"llm/v1/chat"`으로, `llm_format`은 `"bedrock"`으로 되돌려 드라이버가 URL을 만들 수 있게 했다.

```yaml
# before (500)
route_type: "preserve"

# after
route_type: "llm/v1/chat"
llm_format: "bedrock"
```

재검증에서 500이 사라졌다. "4라우트가 설정이 거의 같은데 병합 가능한가"라는 질문이 나왔다. boto3
클라이언트로 4라우트를 전부 때려 실제 동작을 확인했다(2026-07-22). 그중 하나는 응답을 eventstream 프레임으로
잘못 해석해 체크섬 불일치 오류(`ChecksumMismatch`)로 클라이언트가 실패했다.

| 라우트 | HTTP | 실제 동작 |
|---|---|---|
| invoke | 200 | silent 계약 위반 — Anthropic native 요청을 보냈는데 Converse 형태 응답이 와 클라이언트가 `stop_reason 없음`으로 실패 |
| converse | 200 | 정상 |
| converse-stream | 200 | 정상 스트리밍(eventstream 파싱 정상) |
| invoke-stream | 200 | 클라이언트가 응답을 eventstream으로 파싱하려다 크래시 — `ChecksumMismatch: expected 0x73223a7b`(ASCII로 `s":{`), 일반 JSON 응답을 eventstream 프레임으로 오독 |

앞서 "4라우트 모두 200"이라고 확인했던 것은 HTTP 상태 코드만 본 것이었다. 응답 스키마가 맞는지, 스트리밍이
실제로 되는지는 이번 클라이언트 검증에서 처음 확인됐다.

native Bedrock 라우트는 `converse`·`converse-stream` 2종만 남기고 `invoke`·`invoke-stream`은 seed에서
제거했다. 제공 못 하는 의미론을 제공하는 척하는 것보다 404가 정직한 계약이라고 봤다. invoke를 Converse 바디를
받는 alias로 유지하는 안도 검토했다. 실제 Bedrock InvokeModel과 양방향 호환이 깨진다. invoke-stream은 그렇게
해도 스트리밍이 안 된다. 두 이유로 기각했다. `route-bedrock-runtime-converse-stream`에는 `response_buffering: false`를
켜 뒀다 — Converse event-stream 청크를 Kong이 버퍼링하지 않고 도착 즉시 클라이언트로 흘려보내기 위해서다.

같은 구성이라면 seed에 `route-bedrock-runtime-invoke`나 `-invoke-stream`이 아직 남아 있는지부터 확인하는 게
먼저다. 남아 있다면 200을 받는다고 안심하지 말고 boto3 native 클라이언트로 실제 응답 스키마와 스트리밍 여부를
직접 때려 봐야 한다.

{: #prevention data-k="PREVENTION"}
## 200은 계약을 지킨다는 뜻이 아니다

converse 계열 2종만 남긴 뒤로는 native Bedrock InvokeModel 스키마 그대로를 이 게이트웨이로 받을 방법이 없다.
boto3 `converse`/`converse_stream`, Strands `BedrockModel`, LangChain `ChatBedrockConverse`처럼 Converse
계열 클라이언트만 대상이다. 순수 InvokeModel 클라이언트는 이 게이트웨이를 못 쓴다.

설정 필드 하나가 어느 버전에 있는지는 문서 요약이 아니라 스키마로 직접 확인해야 했다. 라우트가 동작하는지도
같은 방식으로, 실제 클라이언트로 응답 스키마와 스트리밍 동작까지 확인해야 알 수 있었다. 2026-07-22에 발견한
두 계약 위반은 "4라우트 모두 200"이라는 HTTP 상태 코드만으로는 판별할 수 없었다.
