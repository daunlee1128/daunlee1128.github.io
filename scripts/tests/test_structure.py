import re
import unittest
from pathlib import Path

import yaml

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


if __name__ == "__main__":
    unittest.main()
