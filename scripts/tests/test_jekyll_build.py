"""실제 Jekyll 빌드 검사. bundle(Task 0)이 없으면 전부 skip."""
import shutil
import subprocess
import unittest
from pathlib import Path

from external_re import EXTERNAL_SUBRESOURCE

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"
HAVE_BUNDLE = shutil.which("bundle") is not None


@unittest.skipUnless(HAVE_BUNDLE, "bundle 없음 — Task 0 참고")
class JekyllBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r = subprocess.run([str(ROOT / "scripts" / "dev-build.sh"), "--with-samples"], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr

    def read(self, rel):
        p = SITE / rel
        self.assertTrue(p.is_file(), f"{rel} 없음")
        return p.read_text(encoding="utf-8")

    def test_urls_from_spec_2_2_exist(self):
        for rel in ["index.html", "tech/index.html", "insights/index.html", "tech/sample-sigv4-403/index.html",
                    "insights/sample-langfuse-two-months/index.html", "stack/kong/index.html", "about/index.html",
                    "explain/sample-sigv4.html", "feed.xml", "sitemap.xml", "assets/tokens.css", "assets/site.css"]:
            with self.subTest(url=rel):
                self.assertTrue((SITE / rel).is_file())

    def test_no_external_resources_and_no_drafts_leak(self):
        for p in SITE.rglob("*.html"):
            with self.subTest(page=p.relative_to(SITE)):
                self.assertIsNone(EXTERNAL_SUBRESOURCE.search(p.read_text(encoding="utf-8")),
                                  "외부 서브리소스(script/img/link rel=stylesheet 등) 로드 금지 — canonical/alternate 는 허용")
        self.assertFalse((SITE / "drafts").exists())
        self.assertFalse((SITE / "scripts").exists())
        self.assertFalse((SITE / "README.md").exists())

    def test_home_lists_all_samples_newest_first_with_kind_and_type(self):
        h = self.read("index.html")
        i1 = h.index("sample-sigv4-403"); i2 = h.index("sample-langfuse-two-months"); i3 = h.index("sample-three-gateways")
        self.assertLess(i1, i2); self.assertLess(i2, i3)
        self.assertIn('data-kind="troubleshooting"', h)
        self.assertIn('data-kind="insights"', h)
        self.assertIn('<span class="tp">tech</span>', h)
        self.assertIn("인터랙티브 설명 ↗", h)

    def test_sidebar_only_stacks_with_posts_and_counts(self):
        h = self.read("index.html")
        self.assertIn("Kong<i>2</i>", h)
        self.assertIn("Langfuse<i>1</i>", h)
        self.assertNotIn("promptfoo", h.split('class="strip')[0].split('class="sb')[1], "글 없는 스택은 사이드바에 없어야")
        self.assertIn('<a class="on" href="/stack/kong/">', self.read("tech/sample-sigv4-403/index.html"))

    def test_filter_counts_on_tech_list(self):
        t = self.read("tech/index.html")
        self.assertEqual(t.count("전체<i>2</i>"), 2, "데스크톱 라디오와 모바일 세그먼트 모두 수를 보여준다")
        self.assertIn("설계<i>1</i>", t)
        self.assertIn("문제 해결<i>1</i>", t)
        self.assertNotIn("인사이트만", t)
        self.assertNotIn('name="kind"', self.read("insights/index.html"), "인사이트 목록은 종류가 하나 — 필터 없음")
        self.assertIn('<div class="ysep">2026</div>', self.read("index.html"))
        self.assertIn('data-more', self.read("index.html"))
        self.assertNotIn('<span class="tp">tech</span>', t)

    def test_post_page_toc_meta_prev_next_and_callout(self):
        p = self.read("tech/sample-sigv4-403/index.html")
        for s in ['href="#situation"', ">어디서, 무엇을 하다가</a>", 'href="#root-cause"', '<h2 id="situation" data-k="SITUATION">',
                  '<div class="callout">', "<strong>재발 방지</strong>", "이전 · kong", "Kong 3종 관문 분리 설계",
                  'href="/explain/sample-sigv4.html"', '<b>문제 해결</b>', '<a class="badge outline" href="/stack/aws-iam/">',
                  "<i>4개 절</i>", "/assets/article.js"]:
            with self.subTest(s=s):
                self.assertIn(s, p)
        self.assertNotIn("다음 · kong", p, "최신 글이므로 다음 없음")
        self.assertNotIn("SITUATION", p.split('class="toc"')[1].split("</div>")[0], "목차 텍스트에 캡션(data-k) 없음")

    def test_explain_html_copied_verbatim(self):
        self.assertIn("{{ 이 중괄호는 Liquid가 건드리지 않아야 한다 }}", self.read("explain/sample-sigv4.html"))

    def test_feed_and_sitemap(self):
        f = self.read("feed.xml")
        published = len(list((ROOT / "_tech").glob("*.md"))) + len(list((ROOT / "_insights").glob("*.md")))
        self.assertEqual(f.count("<entry>"), 3 + published, "샘플 3편 + 게시된 글 전부")
        self.assertIn('<category term="tech"/>', f)
        self.assertIn('<category term="insights"/>', f)
        self.assertIn('<category term="troubleshooting"/>', f)
        self.assertIn('<category term="kong"/>', f)
        s = self.read("sitemap.xml")
        for u in ["/tech/sample-sigv4-403/", "/stack/kong/", "/about/"]:
            self.assertIn(u, s)
        self.assertNotIn("feed.xml", s)

    def test_stack_page_and_about(self):
        k = self.read("stack/kong/index.html")
        self.assertIn("Kong<small>2</small>", k)
        self.assertIn("<b>Kong</b><i>2</i>", k, "모바일 스택 맵 요약줄이 현재 스택을 crumb 으로 보여준다")
        self.assertIn("개 스택 · ", self.read("index.html"))
        self.assertIn('<span class="tp">tech</span>', k)
        a = self.read("about/index.html")
        for u in ["/tech/", "/insights/", "/feed.xml"]:
            self.assertIn(u, a)
        self.assertNotIn('class="sb', a)


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(HAVE_BUNDLE, "bundle 없음 — Task 0 참고")
class Diagrams(unittest.TestCase):
    """그림 계약이 빌드를 살아서 통과하는지 — 규약의 원본은 blog-post 의 references/visuals.md."""

    @classmethod
    def setUpClass(cls):
        cls.html = (SITE / "tech" / "sample-sigv4-403" / "index.html").read_text(encoding="utf-8")

    def test_mermaid_fence_survives_as_language_tagged_code(self):
        """diagram.js 는 pre > code.language-mermaid 를 찾는다. rouge 가 감싸도 이 클래스는 남아야 한다."""
        self.assertIn('class="language-mermaid"', self.html)
        self.assertIn("flowchart TD", self.html)

    def test_caption_paragraph_is_a_lone_italic_line(self):
        """diagram.js 가 p > em 하나짜리 문단을 캡션(p.figcap)으로 승격한다."""
        self.assertRegex(self.html, r"<p><em>서명은 pod 안에서 만들어진다[^<]*</em></p>")

    def test_inline_svg_passes_through_with_class_contract(self):
        for token in ['<figure class="fig">', 'class="fig-scroll"', 'class="d-box"',
                      'class="d-t"', 'class="d-l"', "<figcaption>"]:
            with self.subTest(token=token):
                self.assertIn(token, self.html)

    def test_inline_svg_hardcodes_no_colors(self):
        """색을 박으면 다크모드에서 깨진다 — 색은 d-* 클래스가 준다."""
        svg = self.html[self.html.index("<figure"):self.html.index("</figure>")]
        self.assertNotRegex(svg, r'(fill|stroke)="#')

    def test_mermaid_library_is_served_and_loader_is_wired(self):
        self.assertTrue((SITE / "assets" / "mermaid.min.js").is_file(), "동봉한 mermaid 가 빌드에 없다")
        self.assertIn("/assets/diagram.js", self.html)
