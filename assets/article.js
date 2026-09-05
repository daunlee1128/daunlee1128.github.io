// 글 본문 보조 — ① 열 4개 이상 표는 모바일에서 행 카드(.stack, th → data-label)
// ② 그림(.fig-scroll · .mermaid)에 「크게」: 원래 크기를 전체 화면 <dialog> 에 연다 ③ 데스크톱 목차 현재 절 표시
(function () {
  var art = document.querySelector('.art');
  if (!art) return;

  art.querySelectorAll('table').forEach(function (t) {
    var ths = t.querySelectorAll('thead th');
    if (ths.length < 4) return;
    t.classList.add('stack');
    t.querySelectorAll('tbody tr').forEach(function (tr) {
      [].forEach.call(tr.children, function (td, i) { if (ths[i]) td.setAttribute('data-label', ths[i].textContent.trim()); });
    });
  });

  var ICON = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9.5 2.5h4v4M13.5 2.5 9 7M6.5 13.5h-4v-4M2.5 13.5 7 9"/></svg>';
  var dlg = null;
  function button(label) {
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'zoom'; b.innerHTML = ICON + label;
    return b;
  }
  function open(box) {
    var svg = box.querySelector('svg');
    if (!svg) return;
    if (!dlg) { dlg = document.createElement('dialog'); dlg.className = 'zoomdlg'; document.body.appendChild(dlg); }
    dlg.innerHTML = '';
    var close = button('닫기'); close.addEventListener('click', function () { dlg.close(); });
    var c = svg.cloneNode(true);
    // 원래 크기로: mermaid 는 useMaxWidth 가 남긴 max-width 가 자연 폭, 인라인 SVG 는 viewBox 폭
    var mw = parseFloat(c.style.maxWidth), vb = c.getAttribute('viewBox');
    if (mw) { c.style.width = mw + 'px'; c.style.maxWidth = 'none'; }
    else if (vb) c.style.width = vb.split(/\s+/)[2] + 'px';
    dlg.appendChild(close); dlg.appendChild(c);
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
    dlg.showModal();
  }
  // mermaid 는 재렌더 때 호스트 내용을 갈아엎으므로 버튼은 바깥 래퍼에 둔다
  art.querySelectorAll('.fig-scroll, .mermaid').forEach(function (box) {
    var w = document.createElement('div'); w.className = 'zoomwrap';
    box.parentNode.insertBefore(w, box); w.appendChild(box);
    var b = button('크게'); b.addEventListener('click', function () { open(box); });
    w.appendChild(b);
  });

  var links = document.querySelectorAll('.qn .toc a');
  if (!links.length || !('IntersectionObserver' in window)) return;
  var byId = {}, cur = null;
  links.forEach(function (a) { byId[a.getAttribute('href').slice(1)] = a; });
  var spy = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      if (cur) cur.classList.remove('on');
      cur = byId[e.target.id]; if (cur) cur.classList.add('on');
    });
  }, { rootMargin: '-72px 0px -70% 0px' });
  art.querySelectorAll('h2[id]').forEach(function (h) { spy.observe(h); });
})();
