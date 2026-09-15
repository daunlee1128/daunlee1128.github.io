---
type: tech
kind: troubleshooting
title: WebFilter에서 암복호화하는 body가 잘린다
date: 2026-09-07
stack: [spring-boot]
summary: 게임 서버 API에서 요청·응답 body를 암복호화하는 공통 WebFilter를 뒀는데 body가 잘렸다. reactive 스트림 조각을 한 개만 읽고 전체로 간주한 게 원인이었다.
---

게임 서버 API에서 요청·응답 body를 암복호화하는 공통 WebFilter를 뒀는데, body가 중간에서 잘렸다. reactive
스트림으로 오는 body 조각을 모두 합친 뒤 처리하도록 고쳤다. 전체가 있어야 성립하는 연산을 스트림 위에 얹을 때
무엇부터 의심할지가 남는다.

이 글은 reactive 스트림으로 요청·응답 body를 직접 다루는(암복호화·압축·서명) WebFilter를 운영하는 사람을
대상으로 한다. 답은 [조치를 정리한 절](#fix)에 있다.

{: #situation data-k="SITUATION"}
## 어디서, 무엇을 하다가

Java 17, Spring Boot 3.2 위에서 짠 게임 서버 API다. 인증·암복호화·압축은 요청마다 되풀이되는 관심사라,
개별 API가 아니라 WebFilter 한 자리로 올렸다. 플랫폼 인증 연동과 RSA/AES 암복호화, Protobuf·gzip 압축이
여기 모여 있다.

{: #symptom data-k="SYMPTOM"}
## 보이는 것

- body가 잘렸다.
- 에러 없이 진행됐다.
- 그 탓에 짧은 payload에서는 문제가 드러나지 않았다.

{: #fix data-k="FIX"}
## 조각을 모두 합친 뒤 처리하도록 고쳤다

reactive 스트림으로 오는 body는 여러 조각으로 나뉘어 도착한다. filter는 그중 한 조각만 읽고 전체로 간주하고
있었다.

서명, 암복호화, 파싱처럼 전체가 필요한 연산은 완결을 명시적으로 기다려야 한다는 게 이때 세운 규칙이다. 그런
연산을 스트림 위에서 하고 있다면, 조각 하나만 꺼내 쓰고 있지 않은지부터 본다.

스트리밍 프레임 경계에서 조각을 잇지 못해 응답이 잘린 문제도 같은 계열이었다.
