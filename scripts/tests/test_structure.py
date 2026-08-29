import re
import unittest
from pathlib import Path

import yaml

from external_re import EXTERNAL_SUBRESOURCE

ROOT = Path(__file__).resolve().parents[2]

EXTERNAL_RESOURCE = re.compile(r'<(link|script|img|iframe)[^>]*(src|href)="https?://', re.I)
GROUPS = ["Gateway · Identity", "AI · LLM", "Observability · Eval", "Backend · Data", "Infra · CI"]
KINDS = ["design", "config", "impl", "ops", "troubleshooting"]
SLUG = re.compile(r"^[a-z0-9-]+$")


def load_yaml(rel):
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


class ConfigAndData(unittest.TestCase):
    def test_gitignore_hides_drafts_denylist_and_build_output(self):
        ig = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        for line in ["drafts/", ".denylist", "_site/", ".jekyll-cache/", "Gemfile.lock"]:
            self.assertIn(line, ig)

    def test_config_collections_and_defaults(self):
        cfg = load_yaml("_config.yml")
        self.assertEqual(cfg["collections"]["tech"], {"output": True, "permalink": "/tech/:name/"})
        self.assertEqual(cfg["collections"]["insights"], {"output": True, "permalink": "/insights/:name/"})
        scopes = {(d["scope"].get("type"), d["values"].get("type"), d["values"].get("layout")) for d in cfg["defaults"]}
        self.assertIn(("tech", "tech", "post"), scopes)
        self.assertIn(("insights", "insights", "post"), scopes)
        self.assertIn({"path": "stack"}, [d["scope"] for d in cfg["defaults"]], "stack/ 페이지는 section: stack — 어떤 탭도 활성 아님")
        stack_default = [d for d in cfg["defaults"] if d["scope"] == {"path": "stack"}][0]
        self.assertEqual(stack_default["values"]["section"], "stack")
        self.assertEqual(sorted(cfg["plugins"]), ["jekyll-seo-tag", "jekyll-sitemap"])
        for key in ["handle", "tagline", "description", "github_url", "url"]:
            self.assertIn(key, cfg, f"_config.yml에 {key} 없음")
        for ex in ["drafts", "scripts", "Gemfile", "README.md", ".githooks"]:
            self.assertIn(ex, cfg["exclude"])

    def test_stacks_yml_has_five_groups_with_ascii_slugs(self):
        stacks = load_yaml("_data/stacks.yml")
        self.assertEqual([g["group"] for g in stacks], GROUPS)
        slugs = [it["slug"] for g in stacks for it in g["items"]]
        self.assertEqual(len(slugs), len(set(slugs)), "슬러그 중복")
        for s in slugs:
            self.assertRegex(s, SLUG)
        for it in (it for g in stacks for it in g["items"]):
            self.assertTrue(it.get("name"), f"{it['slug']} 표시명 없음")
        for must in ["kong", "keycloak", "bedrock", "langfuse", "claude-code", "mitmproxy", "grafana"]:
            self.assertIn(must, slugs)

    def test_kinds_yml(self):
        kinds = load_yaml("_data/kinds.yml")
        self.assertEqual([k["slug"] for k in kinds], KINDS)
        for k in kinds:
            for key in ["name", "label", "bg", "fg"]:
                self.assertTrue(k.get(key), f"{k['slug']}.{key} 없음")
            self.assertTrue(k["bg"].startswith("--") and k["fg"].startswith("--"))


class StackStubs(unittest.TestCase):
    def test_stubs_match_stacks_yml_exactly(self):
        slugs = {it["slug"] for g in load_yaml("_data/stacks.yml") for it in g["items"]}
        files = {p.stem for p in (ROOT / "stack").glob("*.md")}
        self.assertEqual(files, slugs, "scripts/gen-stack-stubs.py 를 다시 실행할 것")
        for p in (ROOT / "stack").glob("*.md"):
            fm = yaml.safe_load(p.read_text(encoding="utf-8").split("---")[1])
            self.assertEqual(fm["layout"], "stack")
            self.assertEqual(fm["stack"], p.stem)
            self.assertEqual(fm["permalink"], f"/stack/{p.stem}/")


class Assets(unittest.TestCase):
    def read(self, rel):
        p = ROOT / rel
        self.assertTrue(p.is_file(), f"{rel} 없음")
        return p.read_text(encoding="utf-8")

    def test_tokens_css_has_light_and_dark_scales(self):
        css = self.read("assets/tokens.css")
        self.assertIn(":root{", css.replace(" ", ""))
        self.assertIn("html.dark{", css.replace(" ", ""))
        for tok in ["--gray-1:#fcfcfd", "--gray-12:#1c2024", "--accent-9:#f76b15", "--accent-11:#cc4e00",
                    "--blue-3:#e6f4fe", "--grass-11:#2a7e3b", "--violet-3:#f4f0fe", "--amber-11:#ab6400",
                    "--fs-8:35px", "--lh-8:40px", "--sp-9:64px", "--r-4:8px"]:
            self.assertIn(tok, css.replace(" ", ""), tok)
        self.assertIn("--gray-1:#111113", css.replace(" ", ""), "다크 gray-1")
        self.assertIn("--accent-11:#ffa057", css.replace(" ", ""), "다크 accent-11")
        self.assertNotIn("url(", css, "외부 요청 0 — 폰트/이미지 url 금지")

    def test_site_css_has_components_responsive_and_print(self):
        css = self.read("assets/site.css")
        for sel in [".hd", ".sb", ".qn", ".ct", ".row", ".badge.soft", ".badge.outline", ".callout", ".pn",
                    ".rg", ".toc", ".chips", ".seg", ".mhd", ".mtabs", ".layout", ".desktop-only", ".mobile-only"]:
            self.assertIn(sel, css, sel)
        self.assertIn("@media(max-width:768px)", css.replace(" ", ""))
        self.assertIn("@media print", css)
        self.assertNotIn("url(", css)

    def test_js_files_are_small_and_self_contained(self):
        for rel, must in [("assets/theme.js", "localStorage"), ("assets/filter.js", "data-kind")]:
            js = self.read(rel)
            self.assertIn(must, js)
            self.assertNotIn("http", js)
            self.assertLess(len(js), 2500, f"{rel} 는 최소 JS — 2.5KB 이하")


class BuildTestRegex(unittest.TestCase):
    """빌드 검사가 쓰는 '외부 서브리소스' 정규식 — seo-tag 의 canonical/alternate 는 요청이 아니다."""

    def test_matches_real_subresources(self):
        for html in ['<script src="https://cdn.x/a.js">',
                     '<link rel="stylesheet" href="https://f.x/a.css">',
                     '<img src="https://i.x/a.png">',
                     '<link href="https://f.x/a.css" rel="preload">']:
            with self.subTest(html=html):
                self.assertIsNotNone(EXTERNAL_SUBRESOURCE.search(html))

    def test_ignores_metadata_links(self):
        for html in ['<link rel="canonical" href="https://hong.gildong.github.io/" />',
                     '<link rel="alternate" type="application/atom+xml" href="https://x/feed.xml">',
                     '<a href="https://github.com/Kong/kong">Kong</a>']:
            with self.subTest(html=html):
                self.assertIsNone(EXTERNAL_SUBRESOURCE.search(html))


INCLUDES = ["head.html", "header.html", "footer.html", "kind-badge.html", "post-row.html",
            "sidebar-stacks.html", "quicknav-filter.html", "quicknav-toc.html"]


class IncludesAndDefaultLayout(unittest.TestCase):
    def read(self, rel):
        p = ROOT / rel
        self.assertTrue(p.is_file(), f"{rel} 없음")
        return p.read_text(encoding="utf-8")

    def test_all_includes_exist_and_load_no_external_resources(self):
        for name in INCLUDES:
            with self.subTest(include=name):
                html = self.read(f"_includes/{name}")
                self.assertIsNone(EXTERNAL_RESOURCE.search(html), "외부 리소스 로드 금지")

    def test_kind_badge_falls_back_on_unknown_kind(self):
        b = self.read("_includes/kind-badge.html")
        self.assertIn("var(--gray-4)", b, "알 수 없는 종류에도 배경 토큰 fallback")
        self.assertIn("var(--gray-11)", b)
        self.assertIn("default:", b, "k.name 이 없으면 p.kind 를 그대로 보여준다")

    def test_collection_dirs_are_tracked_with_gitkeep(self):
        for rel in ["_tech/.gitkeep", "_insights/.gitkeep"]:
            with self.subTest(path=rel):
                self.assertTrue((ROOT / rel).is_file(), f"{rel} 없음 — 빈 컬렉션 디렉터리가 클론에 없다")

    def test_head_orders_theme_script_before_css_and_links_feed(self):
        head = self.read("_includes/head.html")
        self.assertLess(head.index("localStorage.getItem('theme')"), head.index("tokens.css"), "플래시 방지 스크립트는 CSS 앞")
        self.assertIn("{% seo %}", head)
        self.assertIn("application/atom+xml", head)
        for a in ["tokens.css", "site.css", "theme.js", "filter.js"]:
            self.assertIn(a, head)
        self.assertEqual(head.count("<script"), 3, "인라인 1 + defer 2")

    def test_header_has_tabs_github_rss_toggle_and_no_real_name(self):
        h = self.read("_includes/header.html")
        for s in ["site.handle", "site.tagline", "site.github_url", "/feed.xml", "data-theme-toggle", "icon-sun", "icon-moon",
                  'page.section == "tech"', 'page.section == "insights"', 'page.section == "about"']:
            self.assertIn(s, h, s)
        self.assertIn('class="mhd mobile-only"', h)
        self.assertIn('class="mtabs mobile-only"', h)

    def test_post_row_contract(self):
        r = self.read("_includes/post-row.html")
        for s in ['data-kind="', "include.show_type", "kind-badge.html", "p.summary", "p.stack", "p.explain", "인터랙티브 설명"]:
            self.assertIn(s, r, s)

    def test_sidebar_renders_only_stacks_with_posts_and_mobile_chips(self):
        s = self.read("_includes/sidebar-stacks.html")
        self.assertIn("site.tech | concat: site.insights", s)
        self.assertIn("where_exp", s)
        self.assertIn('class="sb desktop-only"', s)
        self.assertIn('class="strip mobile-only"', s)
        self.assertIn("active contains", s)
        self.assertIn("rendered", s, "연결선은 실제로 렌더된 그룹 사이에만 — rendered 카운터")

    def test_filter_and_toc_have_parts(self):
        f = self.read("_includes/quicknav-filter.html")
        self.assertIn('include.part == "desktop"', f)
        self.assertIn('include.part == "mobile"', f)
        self.assertIn('name="kind"', f)
        t = self.read("_includes/quicknav-toc.html")
        self.assertIn("'<h2 '", t)
        self.assertIn("strip_html", t)
        self.assertIn("entries.size > 0", t, "<h2 id> 이 없으면 목차 자체를 렌더하지 않는다")

    def test_default_layout(self):
        d = self.read("_layouts/default.html")
        self.assertIn('<html lang="{{ site.lang }}">', d)
        for inc in ["head.html", "header.html", "footer.html"]:
            self.assertIn(f"{{% include {inc} %}}", d)
        self.assertIn("{{ content }}", d)


class ListPages(unittest.TestCase):
    def read(self, rel):
        p = ROOT / rel
        self.assertTrue(p.is_file(), f"{rel} 없음")
        return p.read_text(encoding="utf-8")

    def fm(self, rel):
        return yaml.safe_load(self.read(rel).split("---")[1])

    def test_list_layout_wires_includes_and_filters(self):
        l = self.read("_layouts/list.html")
        self.assertTrue(l.startswith("---\nlayout: default\n---"))
        for s in ["site.tech | concat: site.insights | sort: \"date\" | reverse", "page.posts_filter", "page.stack",
                  "sidebar-stacks.html active=", "post-row.html post=", 'quicknav-filter.html posts=posts part="mobile"',
                  'quicknav-filter.html posts=posts part="desktop"', 'class="layout"', 'class="rows"', 'class="empty" hidden']:
            self.assertIn(s, l, s)

    def test_stack_layout_wraps_list(self):
        self.assertTrue(self.read("_layouts/stack.html").startswith("---\nlayout: list\n---"))

    def test_index_pages_front_matter(self):
        home = self.fm("index.md")
        self.assertEqual((home["layout"], home["permalink"], home["posts_filter"], home["show_type"]), ("list", "/", "all", True))
        tech = self.fm("tech/index.md")
        self.assertEqual((tech["layout"], tech["permalink"], tech["posts_filter"], tech["section"]), ("list", "/tech/", "tech", "tech"))
        ins = self.fm("insights/index.md")
        self.assertEqual((ins["layout"], ins["permalink"], ins["posts_filter"], ins["section"]), ("list", "/insights/", "insights", "insights"))

    def test_dev_build_script_exists_and_is_executable(self):
        p = ROOT / "scripts" / "dev-build.sh"
        self.assertTrue(p.is_file())
        self.assertTrue(p.stat().st_mode & 0o111, "chmod +x")


class PostAndPage(unittest.TestCase):
    def read(self, rel):
        p = ROOT / rel
        self.assertTrue(p.is_file(), f"{rel} 없음")
        return p.read_text(encoding="utf-8")

    def test_post_layout(self):
        p = self.read("_layouts/post.html")
        self.assertTrue(p.startswith("---\nlayout: default\n---"))
        for s in ["sidebar-stacks.html active=page.stack", 'quicknav-toc.html html=content part="desktop"',
                  'quicknav-toc.html html=content part="mobile"', 'class="crumb"', 'class="dl card desktop-only"',
                  'class="meta-row mobile-only"', "page.explain", 'class="pn"', "prev", "next", 'class="ct art"']:
            self.assertIn(s, p, s)
        self.assertEqual(p.count("<time datetime="), 2, "데스크톱 메타 카드와 모바일 메타 줄 모두 <time>")

    def test_page_layout_is_solo_column(self):
        p = self.read("_layouts/page.html")
        self.assertTrue(p.startswith("---\nlayout: default\n---"))
        self.assertIn('class="ct art solo"', p)
        self.assertNotIn("sidebar-stacks", p)

    def test_about_matches_d1_scope(self):
        a = self.read("about.md")
        fm = yaml.safe_load(a.split("---")[1])
        self.assertEqual((fm["layout"], fm["section"], fm["permalink"]), ("page", "about", "/about/"))
        for kw in ["AI Gateway", "Agent Runtime", "LLMOps", "site.handle", "site.github_url", "/feed.xml"]:
            self.assertIn(kw, a, kw)
        self.assertNotRegex(a, r"[\w.+-]+@[\w-]+\.[\w.]+", "이메일 금지")
        self.assertNotRegex(a, r"01[016789]-?\d{3,4}-?\d{4}", "전화번호 금지")
        for banned in ["대학", "University", "년 ~", "재직", "경력 "]:
            self.assertNotIn(banned, a, f"About에 {banned!r} 금지(D1)")

    def test_callout_and_meta_row_css(self):
        css = self.read("assets/site.css")
        self.assertIn(".callout strong", css)
        self.assertIn(".meta-row", css)


class Feed(unittest.TestCase):
    def test_feed_is_atom_over_both_collections(self):
        f = (ROOT / "feed.xml").read_text(encoding="utf-8")
        self.assertTrue(f.startswith("---\npermalink: /feed.xml\nsitemap: false\n---"))
        self.assertIn('<feed xmlns="http://www.w3.org/2005/Atom">', f)
        self.assertIn('site.tech | concat: site.insights | sort: "date" | reverse', f)
        self.assertIn("limit: 20", f)
        for s in ["xml_escape", "date_to_xmlschema", "p.collection", "p.kind", "p.stack", "p.summary", "p.content"]:
            self.assertIn(s, f, s)


if __name__ == "__main__":
    unittest.main()
