import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "scripts" / "gen-stack-stubs.py"

STACKS = """\
- group: G1
  items:
    - { slug: kong, name: Kong }
    - { slug: aws-iam, name: AWS IAM · IRSA · SigV4 }
"""


def run(root):
    return subprocess.run([sys.executable, str(GEN), "--root", str(root)], capture_output=True, text=True)


class GenStackStubs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "_data").mkdir()
        (self.root / "_data" / "stacks.yml").write_text(STACKS, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_creates_one_stub_per_slug_with_contract(self):
        r = run(self.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "wrote 2, removed 0")
        stub = (self.root / "stack" / "aws-iam.md").read_text(encoding="utf-8")
        self.assertEqual(stub, "---\nlayout: stack\nstack: aws-iam\ntitle: AWS IAM · IRSA · SigV4\npermalink: /stack/aws-iam/\n---\n")

    def test_removes_orphan_and_is_idempotent(self):
        (self.root / "stack").mkdir()
        (self.root / "stack" / "old.md").write_text("---\nlayout: stack\nstack: old\n---\n", encoding="utf-8")
        r1 = run(self.root)
        self.assertEqual(r1.stdout.strip(), "wrote 2, removed 1")
        self.assertFalse((self.root / "stack" / "old.md").exists())
        r2 = run(self.root)
        self.assertEqual(r2.stdout.strip(), "wrote 0, removed 0")

    def test_rejects_non_ascii_slug(self):
        (self.root / "_data" / "stacks.yml").write_text("- group: G\n  items:\n    - { slug: 콩, name: Kong }\n", encoding="utf-8")
        r = run(self.root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("slug", r.stderr)


if __name__ == "__main__":
    unittest.main()
