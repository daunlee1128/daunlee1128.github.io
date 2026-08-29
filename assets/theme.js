// 다크 토글 — html.dark 클래스 하나만 다룬다. 초기 적용은 head.html 인라인 1줄이 먼저 한다(플래시 방지).
(function () {
  var root = document.documentElement;
  function apply(dark) { root.classList.toggle('dark', dark); }
  document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var dark = !root.classList.contains('dark');
      apply(dark);
      try { localStorage.setItem('theme', dark ? 'dark' : 'light'); } catch (e) {}
    });
  });
})();
