// 종류 필터 + 「더 보기」 페이징. 목록 HTML 은 전부 내보내고 여기서 20편씩 드러낸다
// (Pages 기본 빌드엔 컬렉션 페이징 플러그인이 없다). 데스크톱 RadioGroup 과 모바일 SegmentedControl 이 같은 name="kind" 를 쓴다.
(function () {
  var rows = [].slice.call(document.querySelectorAll('.row[data-kind]'));
  if (!rows.length) return;
  var PAGE = 20, key = 'list:' + location.pathname, st = { kind: 'all', n: PAGE };
  try { st = JSON.parse(sessionStorage.getItem(key)) || st; } catch (e) {}
  var more = document.querySelector('[data-more]'), empty = document.querySelector('.empty');
  var inputs = document.querySelectorAll('input[name="kind"]');
  function apply() {
    var hits = 0, shown = 0;
    rows.forEach(function (r) {
      var hit = st.kind === 'all' || r.getAttribute('data-kind') === st.kind;
      r.hidden = !(hit && hits < st.n);
      if (hit) hits++;
      if (!r.hidden) shown++;
    });
    // 연도 구분선은 그 아래 보이는 글이 하나라도 있을 때만
    document.querySelectorAll('.ysep').forEach(function (y) {
      var e = y.nextElementSibling, vis = false;
      while (e && !e.classList.contains('ysep')) { if (!e.hidden) { vis = true; break; } e = e.nextElementSibling; }
      y.hidden = !vis;
    });
    inputs.forEach(function (i) { i.checked = (i.value === st.kind); });
    if (empty) empty.hidden = shown > 0;
    if (more) { more.hidden = hits <= shown; more.querySelector('i').textContent = shown + ' / ' + hits; }
    try { sessionStorage.setItem(key, JSON.stringify(st)); } catch (e) {}
  }
  inputs.forEach(function (i) {
    i.addEventListener('change', function () { if (i.checked) { st.kind = i.value; st.n = PAGE; apply(); } });
  });
  if (more) more.addEventListener('click', function () { st.n += PAGE; apply(); });
  apply();
})();
