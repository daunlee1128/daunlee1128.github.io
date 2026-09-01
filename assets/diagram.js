// 다이어그램 — ```mermaid 펜스 렌더 + 그림 캡션 표시.
// kramdown GFM 은 ```mermaid 를 <pre><code class="language-mermaid"> 로 내보낸다(rouge 가 모르는 언어라 그대로 통과).
// mermaid 는 assets/mermaid.min.js 로 동봉한다 — 이 블로그는 외부 서브리소스를 싣지 않는다.
// 2.7MB 라 그림이 있는 글에서만 주입한다(그림 없는 페이지는 추가 요청 0).
// 인라인 SVG(<figure class="fig">)는 JS 없이 CSS 만으로 그려진다. 여기서는 다루지 않는다.
(function () {
  // 자기 자신의 경로에서 형제 파일을 찾는다 — baseurl 이 붙어도 그대로 맞는다.
  var self = document.currentScript && document.currentScript.src;
  var SRC = self ? self.replace(/diagram\.js(\?.*)?$/, 'mermaid.min.js') : '/assets/mermaid.min.js';
  var root = document.documentElement;

  var codes = document.querySelectorAll('pre > code.language-mermaid');
  if (!codes.length) return;

  // 그림 바로 뒤의 "이탤릭만 있는 한 줄 문단" 이 캡션이다(초안 규약).
  // 초안은 플랫폼 중립 마크다운이라 클래스를 못 붙인다 — 모양으로 찾아 여기서 붙인다.
  function markCaption(el) {
    var p = el.nextElementSibling;
    if (!p || p.tagName !== 'P' || p.children.length !== 1) return;
    var em = p.children[0];
    if (em.tagName !== 'EM') return;
    if (p.textContent.trim() !== em.textContent.trim()) return;
    p.className = 'figcap';
  }

  // 펜스를 mermaid 호스트로 바꾸고 원문을 data-src 에 남긴다(테마 전환 시 재렌더용).
  var hosts = [];
  Array.prototype.forEach.call(codes, function (code) {
    var block = code.parentNode;
    while (block.parentNode && /highlight/.test(block.parentNode.className || '')) {
      block = block.parentNode;
    }
    var host = document.createElement('div');
    host.className = 'mermaid';
    host.setAttribute('data-src', code.textContent);
    block.parentNode.replaceChild(host, block);
    markCaption(host);
    hosts.push(host);
  });

  // mermaid 를 못 받아오거나 문법이 틀렸을 때 — 원문을 코드 블록으로 되돌린다.
  // 그림이 사라지는 것보다 소스라도 보이는 편이 낫다.
  function degrade(host) {
    var pre = document.createElement('pre');
    var code = document.createElement('code');
    code.textContent = host.getAttribute('data-src');
    pre.appendChild(code);
    host.parentNode.replaceChild(pre, host);
  }

  // mermaid 기본 팔레트는 사이트와 따로 논다. base 테마에 사이트 토큰을 그대로 먹여
  // 인라인 SVG(.d-*)와 같은 색·같은 글꼴로 맞춘다 — 두 종류의 그림이 한 시스템으로 보이게.
  function tok(name) {
    return getComputedStyle(root).getPropertyValue(name).trim();
  }

  function render(mermaid) {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'base',
      securityLevel: 'strict',
      fontFamily: tok('--mono'),
      themeVariables: {
        fontFamily: tok('--mono'),
        fontSize: '13px',
        background: tok('--gray-1'),
        primaryColor: tok('--color-panel'),
        primaryBorderColor: tok('--gray-11'),
        primaryTextColor: tok('--gray-12'),
        secondaryColor: tok('--gray-3'),
        tertiaryColor: tok('--gray-2'),
        lineColor: tok('--gray-11'),
        textColor: tok('--gray-12'),
        edgeLabelBackground: tok('--gray-1'),
        clusterBkg: tok('--gray-2'),
        clusterBorder: tok('--gray-7'),
        titleColor: tok('--gray-12'),
        nodeBorder: tok('--gray-11')
      },
      // 축소되면 글자가 같이 작아진다. 자연 크기로 두고 넘치면 컨테이너가 가로 스크롤한다
      // — 이 블로그의 표(.art table)·코드(.art pre)와 같은 규칙이다.
      flowchart: { htmlLabels: false, curve: 'linear', useMaxWidth: false, padding: 8, nodeSpacing: 36, rankSpacing: 40 },
      sequence: { useMaxWidth: false },
      gantt: { useMaxWidth: false }
    });
    hosts.forEach(function (h) {
      h.removeAttribute('data-processed');
      h.textContent = h.getAttribute('data-src');
    });
    return mermaid.run({ nodes: hosts, suppressErrors: true });
  }

  var tag = document.createElement('script');
  tag.src = SRC;
  tag.onload = function () {
    var mermaid = window.mermaid;
    if (!mermaid) return hosts.forEach(degrade);
    render(mermaid);
    // 다크 토글은 html.dark 클래스만 바꾼다(theme.js). 그 변화를 보고 다시 그린다.
    var pending = false;
    new MutationObserver(function () {
      if (pending) return;
      pending = true;
      requestAnimationFrame(function () { pending = false; render(mermaid); });
    }).observe(root, { attributes: true, attributeFilter: ['class'] });
  };
  tag.onerror = function () { hosts.forEach(degrade); };
  document.head.appendChild(tag);
})();
