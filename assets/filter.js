// 종류 필터 — 데스크톱 RadioGroup 과 모바일 SegmentedControl 이 같은 name="kind" 를 쓴다.
(function () {
  var rows = document.querySelectorAll('.row[data-kind]');
  if (!rows.length) return;
  function applyFilter(v) {
    rows.forEach(function (r) { r.hidden = !(v === 'all' || r.getAttribute('data-kind') === v); });
    document.querySelectorAll('input[name="kind"]').forEach(function (i) { i.checked = (i.value === v); });
    var empty = document.querySelector('.empty'); if (empty) empty.hidden = !!document.querySelector('.row[data-kind]:not([hidden])');
  }
  document.querySelectorAll('input[name="kind"]').forEach(function (i) {
    i.addEventListener('change', function () { if (i.checked) applyFilter(i.value); });
  });
})();
