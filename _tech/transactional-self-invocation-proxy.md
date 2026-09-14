---
type: tech
kind: troubleshooting
title: "@Transactional을 붙였는데 롤백이 안 된다"
date: 2026-09-07
stack: [spring-boot]
summary: 같은 bean 안에서 부른 메서드라 @Transactional 롤백이 예외도 경고도 없이 빠졌고, 뒤에 @Async에서 같은 원인을 다시 겪었다. Spring의 proxy 모드에서 두 애노테이션이 동작하지 않으면 호출이 proxy를 지나는지 본다.
---

`@Transactional` 롤백이 조용히 빠진 일을 고친 뒤, `@Async`에서 같은 원인을 한 번 더 겪었다.
호출이 proxy를 지나도록 호출 구조를 나눴다.
두 애노테이션에 똑같이 쓸 확인 하나를 얻는다.
Spring에서 `@Transactional`·`@Async`를 proxy 모드 그대로 쓰는 사람을 위한 글이다.
답은 [호출 구조를 나눈 절](#fix)에 있다.

{: #symptom data-k="SYMPTOM"}
## 보이는 것

트랜잭션이 걸려 있어야 할 구간에서 롤백이 되지 않았다. 예외도 경고도 없었다.
그래서 롤백이 안 된다는 것을 장애가 날 때까지 몰랐다.

{: #fix data-k="FIX"}
## 호출이 proxy를 지나도록 호출 구조를 나눴다

이 글의 조건: Spring의 proxy 모드(기본값).
인용한 문서는 모두 Spring Framework 7.0.9 reference다(2026-09-14 확인).

원인은 같은 bean 내부 호출이었다. 그 호출이 Spring AOP proxy를 거치지 않아 `@Transactional`이 적용되지 않았다.
proxy 모드가 가로채는 것은 [proxy로 들어온 외부 호출뿐이다][tx].
self-invocation으로 부른 메서드에는 `@Transactional`이 붙어 있어도 트랜잭션 advice가 적용되지 않는다.

같은 증상이면 롤백이 빠진 메서드를 같은 bean 안에서 부르는지부터 본다.

{: #prevention data-k="PREVENTION"}
## `@Async`에서 같은 원인을 다시 만났다

`@Async`도 기본 advice mode가 `proxy`다. 이 모드는 [같은 클래스 안의 local call을 가로채지 못한다][async].

그래서 규칙을 세웠다. Spring의 proxy 모드에서는 `this`로 부른 self-invocation에 [그 메서드의 advice가 적용되지 않는다][proxying].

`@Transactional`이든 `@Async`든 붙인 애노테이션이 동작하지 않으면 물을 것은 그 호출이 proxy를 지나는지다.

[tx]: https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html

[async]: https://docs.spring.io/spring-framework/reference/integration/scheduling.html

[proxying]: https://docs.spring.io/spring-framework/reference/core/aop/proxying.html
