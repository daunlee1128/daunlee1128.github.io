---
type: tech
kind: troubleshooting
title: "Kong 뒤 Bedrock 스트리밍에서 긴 응답만 중간에 끊긴다"
date: 2026-09-07
stack: [kong, bedrock]
summary: "carry-over 패치는 원복했다. 실제 조치는 동기 Converse 우회였다."
---

응답 크기 대신 절단점 위치를 변수로 놓고 파서의 응답 분기끼리 대조했다.
Bedrock `ConverseStream`의 긴 출력은 Kong 뒤에서 도중에 닫혔다.
carry-over 패치는 원복했다.
실제 조치는 동기 `Converse` 우회였다.

독자는 Kong으로 Bedrock 스트리밍 응답을 파싱해 내보내는 사람이다.
답은 [“스트리밍 경로를 동기 Converse 호출로 우회했다” 절](#sync-converse-bypass)에 있다.

바로 할 것:

1. 마지막 SSE event와 Gateway 오류를 같은 요청에서 모은다.
2. Kong version과 AWS eventstream parser 구현을 확인한다.
3. 청크 하나를 완결된 프레임으로 가정하는지 source에서 본다.
4. 해당 version의 수정 release가 있는지 공식 changelog를 확인한다.
5. upgrade가 막히면 동기 `Converse` 경로로 우회한다.

{: #streaming-symptom }
## 스트리밍 route를 만든 뒤 긴 응답이 닫혔다

2026-07-13에 legacy 스트리밍 route를 만들었다.
07-23에 현재 경로로 나눴고, 08-04와 08-12에 route를 하나씩 더했다.

[미확인: STREAM-2 · 최초 발견자와 발견 경로]

짧은 응답은 끝까지 왔다는 기록이 남아 있다.
긴 출력에서는 Lua `body_filter`가 실패하고 chunked 응답이 무너졌다.

[미확인: STREAM-1 · 마지막 SSE event나 로그 원문, 재현 부하 규모, 끊긴 비율]

<details markdown="1">
<summary>parser 오류를 대조할 사람이 펼치기: 기록에 남은 두 nil 지점</summary>

- `count` 산술 연산에서 nil 오류
- nil 값을 함수처럼 호출한 오류

</details>

{: #parser-assumption }
## Kong 3.9.3 파서는 완결된 AWS 프레임을 가정했다

이 경로는 Kong OSS 3.9.3의 내장 Lua/LuaJIT parser를 썼다.
Bedrock API는 `ConverseStream`이고 응답은 SSE로 다시 조립했다.

parser 생성자 주석은 입력을 완결된 AWS response stream chunk라고 적었다.
16바이트보다 짧은 입력만 거절했고 프레임 중간 절단은 지키지 못했다.

<details markdown="1">
<summary>프레임 레이아웃을 대조할 사람이 펼치기: 길이 필드와 CRC 위치</summary>

2026-09-12에 [Smithy Amazon Event Stream 규격][s]을 확인했다.
message는 prelude와 data로 나뉜다.
prelude에는 전체 길이 4바이트와 header 길이 4바이트가 있다.
각 부분 뒤에는 CRC32 4바이트가 붙어 고정 overhead는 16바이트다.
수신자는 이 필드 구조와 payload 길이 식으로 message 경계를 복원한다.

```text
[ total length: 4B ][ headers length: 4B ][ prelude CRC: 4B ]
[ headers ... ][ payload ... ][ message CRC: 4B ]
```

HTTP 청크가 어디서 끝나는지는 이 message 길이와 별개다.
청크 끝이 프레임 중간이면 다음 호출까지 꼬리를 보관해야 한다.

</details>

같은 함수의 표준 SSE와 Gemini 분기는 잘린 꼬리를 보관했다.
나중에 붙은 AWS eventstream 분기만 그 처리가 없었다.

<details markdown="1">
<summary>분기와 공식 문서를 대조할 사람이 펼치기: 꼬리 처리와 정렬 설정</summary>

| 응답 분기 | 잘린 꼬리를 |
|---|---|
| 표준 SSE | 다음 청크에 이어 붙임 |
| Gemini | 다음 청크에 이어 붙임 |
| AWS eventstream | 버림 |

이 파서에서는 방어 로직이 분기마다 따로 관리됐다.
코드 구조는 프레임 절단이 nil 오류로 이어지는 경로를 설명한다.

2026-09-12에 [handler][h]·[Response PDK][p] 등 Kong 공식 문서 11개를 비교했다.
route entity·large payload·3.9.0 route source와 handler·PDK를 포함했다.
AI Proxy 개요·reference·Bedrock provider·parser source·두 changelog도 확인했다.
frame 정렬 설정은 찾지 못했다.
두 대표 문서는 `body_filter`가 도착한 chunk마다 실행되는 계약을 보여준다.

</details>

[미확인: STREAM-4 · 부하 유무에 따라 프레임 절단 위치가 달라진 로그]

{: #discarded-carry-over }
## carry-over 패치는 다음 날 전량 원복됐다

2026-08-13에 AWS 분기의 미소비 bytes를 잇는 임시 patch를 적용했다.
다음 날 관련 patch를 모두 제거하고 원본 image로 돌아갔다.

따라서 carry-over buffer를 운영의 최종 수리로 쓰면 사실과 어긋난다.

{: #upgrade-boundary }
## 수정 release는 있었지만 현재 OSS version에는 없었다

[Kong AI Proxy changelog][k]에는 두 수정 release가 있다.

<details markdown="1">
<summary>upgrade를 검토할 사람이 펼치기: 수정 version과 release date</summary>

| version | release date | 공식 기록 |
|---|---|---|
| 3.11.0.2 | 2025-07-28 | incomplete AWS frame parser 수정 |
| 3.10.0.4 | 2025-08-07 | 같은 수정 backport |

</details>

사건 당시 이 환경은 OSS 3.9.3이었다.
내가 당시 파악한 제약은 OSS 3.9.3 이후에 Enterprise license가 필요하다는 것이었다.
이는 공식 license 정책을 확인한 사실이 아니라 작성자 진술이다.
별도 EE 3.14.0.3 환경은 수정 이후 계열에 해당한다.
[미확인: STREAM-6 후속 · EE 3.14.0.3 환경으로 실제 이전하지 않은 이유]

{: #sync-converse-bypass }
## 스트리밍 경로를 동기 Converse 호출로 우회했다

이 글의 조건: Kong OSS 3.9.3, 내장 Lua/LuaJIT parser, Bedrock `ConverseStream`, client 응답 SSE, 재현 부하 미확인.
이 결론은 한 parser 함수에 응답 분기 셋을 둔 구현에서 확인했다.

임시 carry-over 패치를 유지하지 않고 모델 호출을 동기 `Converse`로 돌렸다.
이 결정을 모델 호출의 과도기 표준으로 문서화했다.
streaming response parser를 지나지 않으므로 확인한 crash 경로를 피한다.

[미확인: STREAM-3 · 우회 구현·운영 반영, 같은 부하의 절단 여부]
[미확인: STREAM-5 · 재현에 사용한 부하 규모]

- 같은 조건에서는 임시 parser patch보다 동기 우회 여부를 먼저 판단한다.
- streaming이 제품 요구라면 수정 parser를 포함한 version으로 옮긴다.

{: #remaining-cost }
## 동기 우회는 스트리밍 전달을 포기하는 선택이다

동기 `Converse`는 frame 재조립 crash를 피하지만 token을 도착 즉시 보내지 못한다.
첫 응답까지 기다리는 시간이 길어질 수 있다.

<details markdown="1">
<summary>같은 판단을 다시 할 사람이 펼치기: 확인된 선택과 남은 구멍</summary>

| 선택 | 확인한 것 | 남은 구멍 |
|---|---|---|
| 정렬 설정 변경 | 설정 전량과 공식 문서 11개 | 해당 항목을 찾지 못함 |
| 수정 version으로 upgrade | 공식 changelog의 parser 수정 | EE 이전 사유 |
| 임시 carry-over patch | 적용 다음 날 전량 원복 | 운영 처방에서 제외 |
| 동기 `Converse` 우회 | crash parser를 지나지 않는 설계 | 구현과 운영 관측 |

</details>

남은 판단은 동기 응답의 대기 비용을 받아들일 수 있는지다.
그 비용을 받을 수 없으면 EE 이전 조건과 운영 검증부터 채워야 한다.

[s]: https://smithy.io/2.0/aws/amazon-eventstream.html

[k]: https://developer.konghq.com/plugins/ai-proxy/changelog/

[h]: https://developer.konghq.com/custom-plugins/handler.lua/

[p]: https://developer.konghq.com/gateway/pdk/reference/kong.response/
