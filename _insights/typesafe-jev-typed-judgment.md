---
type: insights
title: TypeSafe Jev API를 직접 호출해 본 Choice·Score·Noul 응답과 확률
date: 2026-09-22
stack: [typesafe-jev]
tags: [사용기]
summary: "Jev는 판단을 타입 있는 답과 확률로 돌려주고, 무엇을 할지는 호출하는 코드에 남긴다. 실제 호출 15번에서 한 입력 안의 질문끼리도 확률이 또렷한 것과 갈린 것이 섞여 나왔다."
---

TypeSafe Jev API를 15번 호출해 보니 한 입력 안에서도 확률이 또렷한 질문과 반반으로 갈린 질문이 함께 나왔다.
Jev는 [GitHub Trending 9월 21일 회차](/github-trending/2026-09-21/)에 급상승 이슈로 올라왔다.
자료를 보다 관심이 생겨 설명서와 로컬 playground를 직접 만들어 호출했고 결과는 팀원들에게 공유했다.
코드는 [jev-workshop](https://github.com/daunlee1128/jev-workshop)에 있다.
Jev는 문장 대신 정해 둔 타입의 답과 확률을 돌려준다.
그래서 판단을 확률로 받으면 질문마다 무엇을 할지 정하는 일은 호출하는 코드 몫이 된다.
발표 글과 문서는 응답 모양과 schema 준수를 말한다. 이 글은 실제 호출에서 질문별 확률이 어떻게 갈렸는지를 본다.
전제 독자는 LLM 분류·라우팅 결과를 코드에서 분기 조건으로 쓰고 있거나 Jev 도입을 검토하는 사람이다.
확률이 갈린 사례는 [호출 결과 절](#calls)에, 코드가 맡을 일은 [그다음 절](#code-decides)에 있다.

해 볼 것:

1. 판단 하나를 질문 하나로 쪼갠다. "어느 팀이며 오늘 조치해야 하나"는 Choice 하나와 Noul 하나다.
2. 질문마다 자동 처리와 사람 검토를 가르는 임계값을 따로 둔다.
3. 그 임계값은 정답이 붙은 실제 데이터로 정한다.

{: #typed}
## Jev는 글 대신 타입이 정해진 판단을 돌려준다

Jev는 질문 타입(Choice·Score·Noul)마다 정해진 모양으로 답하고 Noul 답에는 `confidence` 필드가 없다.
응답 모양은 [API reference][api]와 [Confidence 문서][conf]에서 확인했다(2026-09-22).
실제 호출 15번의 Noul 답도 모두 `type`과 `noul` 두 필드뿐이었다(2026-09-22 호출, 응답 모델 `jev-1.13.0`).
"지난달 결제가 두 번 청구된 것 같아요"에 "사람 상담원에게 연결해야 하는가?"를 물은 답은 이랬다.

```json
{"type": "noul", "noul": 0.61}
```

<details markdown="1">
<summary>Jev가 처음이면 펼치기: 세 질문 타입의 응답 모양과 confidence가 뜻하는 것</summary>

요청에는 평가할 `state`와 이름 붙은 `questions`를 보내고, 답은 질문 이름을 키로 돌아온다.

| 질문 타입 | 무엇을 묻나 | 돌려받는 값 | `confidence` 필드 |
|---|---|---|---|
| Choice | 순서 없는 후보 중 하나 | 고른 후보와 후보별 확률 | 있다 |
| Score | 순서 있는 단계의 정도 | 확률 가중 점수와 단계별 확률 | 있다 |
| Noul | 예/아니오 | "예"일 확률 하나(`noul`) | 없다 |

Noul의 0.8은 "강도 80%"가 아니라 "예일 확률 80%"다.
`confidence`는 Choice·Score의 확률 분포가 한곳에 얼마나 모였는지를 0~1로 줄인 값이다.

</details>

<details markdown="1">
<summary>요청을 직접 짜 볼 사람이 펼치기: 세 타입을 한 번에 묻는 요청 예시</summary>

질문 셋은 같은 `state`를 따로 평가한다. 아래 `request.json`을 만든 뒤 호출한다.

```bash
curl -X POST https://api.typesafe.ai/v1/systemone \
  -H "Authorization: Bearer $TYPESAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d @request.json
```

```json
{
  "state": "연동 오류가 3일째 계속돼 주문을 못 받고 있습니다. 오늘 해결해야 합니다.",
  "model": "jev-latest",
  "questions": {
    "department": {
      "type": "choice",
      "instructions": "어느 팀이 처리해야 하나?",
      "criteria": {"billing": "결제·청구·환불", "technical": "오류·연동·장애", "other": "해당 없음"}
    },
    "frustration": {
      "type": "score",
      "instructions": "불만 정도는?",
      "criteria": ["차분함", "불편하지만 정중함", "강한 불만"]
    },
    "urgency": {"type": "noul", "instructions": "오늘 조치가 필요하다고 명시했는가?"}
  }
}
```

</details>

{: #calls}
## 한 입력 안에서도 확률이 갈린 질문과 또렷한 질문이 섞여 나왔다

playground에는 고객 문의·장애 대응·변경 승인 같은 사례 7개를 넣었다.
사례마다 Choice로 경로를, Score로 정도를, Noul로 "사람이 봐야 하나"를 묻는다.
연결 확인 1번을 빼면 나머지 14번은 이 사례들의 입력으로 보냈다.
세 입력에서 같은 요청 안의 질문끼리 확률이 크게 달랐다.

| 입력 | 갈린 질문과 확률 | 또렷한 질문과 확률 |
|---|---|---|
| 결제 요청의 절반이 timeout으로 실패 | 장애 유형: performance 0.52 · availability 0.48 | 당직 호출(Noul) 0.92 |
| 개발 환경 로그 보존 기간 7일→14일 | 처리 경로: 동료 검토 0.56 · 자동 실행 0.42 | 변경 위험 "낮음" 0.91 |
| 지난달 결제가 두 번 청구된 것 같음 | 우선순위: 높음 0.64 · 보통 0.35 | 문의 유형 billing 1.0 |

timeout 입력에서 장애 유형 답의 `confidence`는 0.36이었다.
그래도 당직을 부를지는 0.92로 분명했다.
한 요청의 답을 통째로 믿거나 버리지 말고 질문 단위로 다뤄야 한다고 읽었다.
각 입력은 한두 번씩 보냈을 뿐이라 이 확률이 얼마나 안정적인지는 알 수 없다.

{: #code-decides}
## 무엇을 할지는 모델이 아니라 호출하는 코드가 정한다

Jev가 주는 것은 판단 재료와 확률까지다.
장애 유형이 0.52 대 0.48이면 자동 분류 대신 사람에게 넘기는 규칙은 코드 쪽에 둔다.
Choice 후보에는 `other`나 `unknown`을 둔다.
어디에도 안 맞는 입력이 기존 후보로 억지로 가지 않게 하려는 것이다.
"일부 사용자가 가끔 이상하다고 제보했습니다"는 장애 유형 `unknown` 1.0으로 돌아왔다.
질문을 쪼개면 답끼리 어긋날 수 있다(분류는 `technical`, 긴급도는 낮음).
그 조정도 코드 몫이다(추론).

{: #schema}
## 모양을 지키는 것과 판단이 맞는 것은 따로 확인해야 한다

[발표 글][blog]은 "hallucination 0%"의 근거로 schema 준수 보장을 든다(2026-09-22 확인).
실제 호출 15번의 답은 모두 정해 둔 타입과 후보 이름 안에서 돌아왔다.
그러나 그 답이 맞았는지는 따로 재지 않았다.
Confidence 문서는 `confidence`를 확률 분포에서 계산한 통계로 정의한다(2026-09-22 확인).
이 정의만으로는 높은 값이 곧 정답이라고 읽을 수 없다(추론).
임계값을 정하려면 사례마다 정답이 붙은 입력이 필요한데 이번 실험에는 없었다.

{: #latency}
## 응답 시간은 733–983ms였다

발표는 end-to-end 응답 시간을 70–500ms로 든다(2026-09-22 확인).
내 호출 15번은 733–983ms였고 15번 중 14번이 830ms 아래였다.
로컬 playground 서버 로그에서 요청 기록과 응답 기록 사이 시간을 쟀다.
네트워크 왕복이 들어가 있고 한 요청의 질문 수는 1~5개였다.
측정 위치와 입력 크기가 달라 발표 수치와 바로 비교할 수는 없다.
다음에 확인할 것은 Choice의 `confidence`가 어느 값 아래일 때 오답이 몰리는지다.

[api]: https://docs.typesafe.ai/api
[conf]: https://docs.typesafe.ai/confidence
[blog]: https://typesafe.ai/blog/introducing-system-one-models-and-jev
