import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "scripts" / "check-publish.sh"
HOOK = ROOT / ".githooks" / "pre-push"


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True)


class TempRepo(unittest.TestCase):
    """임시 repo: 스크립트·훅 복사, 깨끗한 글 1편 커밋, .denylist(무시됨) 작성."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "blog"
        (self.repo / "scripts").mkdir(parents=True)
        (self.repo / ".githooks").mkdir()
        (self.repo / "_tech").mkdir()
        shutil.copy(CHECK, self.repo / "scripts" / "check-publish.sh")
        shutil.copy(HOOK, self.repo / ".githooks" / "pre-push")
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.name", "t")
        git(self.repo, "config", "user.email", "t@" + "users.noreply.github.com")
        git(self.repo, "config", "core.hooksPath", ".githooks")
        (self.repo / ".gitignore").write_text(".denylist\ndrafts/\n", encoding="utf-8")
        (self.repo / ".denylist").write_text("# 회사명\nAcme Corp\tAI 플랫폼 조직\nproj-phoenix\n", encoding="utf-8")
        (self.repo / "_tech" / "clean.md").write_text("---\ntitle: ok\n---\nKong 뒤에서 Bedrock 호출. github.com/Kong/kong 참고.\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, *args, env=None):
        e = dict(os.environ, **(env or {}))
        return subprocess.run([str(self.repo / "scripts" / "check-publish.sh"), *args], cwd=self.repo, capture_output=True, text=True, env=e)

    def commit_file(self, rel, text):
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        git(self.repo, "add", "-f", rel)
        git(self.repo, "commit", "-q", "-m", f"add {rel}")


class CheckPublish(TempRepo):
    def test_a_clean_tree_passes(self):
        r = self.check("--tree", "HEAD")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout.strip(), r"^OK: \d+ files scanned$")
        self.assertNotIn("no-verify", r.stdout + r.stderr)

    def test_b_denylist_pattern_rejected_with_location_case_insensitive(self):
        self.commit_file("_tech/leak.md", "---\ntitle: x\n---\n첫 줄\n우리 acme corp 에서는\n")
        r = self.check("--tree", "HEAD")
        self.assertEqual(r.returncode, 1)
        self.assertIn("_tech/leak.md:5:", r.stderr)
        self.assertNotIn("no-verify", r.stderr)

    def test_c_tracked_denylist_rejected(self):
        git(self.repo, "add", "-f", ".denylist")
        git(self.repo, "commit", "-q", "-m", "oops")
        r = self.check("--tree", "HEAD")
        self.assertEqual(r.returncode, 1)
        self.assertIn(".denylist", r.stderr)

    def test_d_missing_denylist_fails_closed(self):
        (self.repo / ".denylist").unlink()
        r = self.check("--tree", "HEAD")
        self.assertEqual(r.returncode, 1)
        self.assertIn("fail-closed", r.stderr)

    def test_e_builtin_patterns_rejected(self):
        cases = {
            # 문자열을 쪼개 두는 이유: 이 테스트 파일도 트리에 있어 pre-push 검사를 받는다
            "email": "연락: someone@" + "example.com",
            "phone": "010-1234" + "-5678",
            "git-ssh": "git@" + "gitlab.example.com:group/repo.git",
            "gitlab-url": "https://" + "gitlab.example.com/g/r",
            "internal-host": "http://api.payments" + ".internal/v1",
            "private-ip": "curl http://10.20.30" + ".40:8080",
        }
        for name, text in cases.items():
            with self.subTest(case=name):
                (self.repo / "drafts").mkdir(exist_ok=True)
                f = self.repo / "drafts" / f"{name}.md"
                f.write_text(f"---\ntitle: x\n---\n{text}\n", encoding="utf-8")
                r = self.check(f"drafts/{name}.md")
                self.assertEqual(r.returncode, 1, f"{name}: {r.stdout}")
                self.assertIn(f"drafts/{name}.md:4:", r.stderr)

    def test_public_oss_github_links_are_allowed(self):
        r = self.check("_tech/clean.md")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_binary_files_skipped_and_denylist_second_column_ignored(self):
        self.commit_file("assets/x.png", "Acme Corp inside a fake png")
        self.commit_file("_tech/ok.md", "---\ntitle: x\n---\nAI 플랫폼 조직에서\n")  # 2열(치환어)은 패턴이 아니다
        r = self.check("--tree", "HEAD")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_working_tree_default_scans_tracked_files(self):
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OK:", r.stdout)

    def test_invalid_denylist_regex_fails_closed(self):
        (self.repo / ".denylist").write_text("acme(bad\n", encoding="utf-8")
        r = self.check("--tree", "HEAD")
        self.assertEqual(r.returncode, 1)
        self.assertIn("잘못된 정규식", r.stderr)
        self.assertNotIn("OK:", r.stdout)

    def test_builtin_host_patterns_are_case_insensitive(self):
        (self.repo / "drafts").mkdir(exist_ok=True)
        for name, text in {"gitlab-caps": "https://" + "GitLab.example.com/g/r", "internal-caps": "http://payments" + ".Internal/v1"}.items():
            with self.subTest(case=name):
                f = self.repo / "drafts" / f"{name}.md"
                f.write_text(f"---\ntitle: x\n---\n{text}\n", encoding="utf-8")
                r = self.check(f"drafts/{name}.md")
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(f"drafts/{name}.md:4:", r.stderr)


class PrePushHook(TempRepo):
    def setUp(self):
        super().setUp()
        self.remote = Path(self.tmp.name) / "remote.git"
        git(Path(self.tmp.name), "init", "-q", "--bare", str(self.remote))
        git(self.repo, "remote", "add", "origin", str(self.remote))

    def push(self):
        return subprocess.run(["git", "push", "-q", "origin", "main"], cwd=self.repo, capture_output=True, text=True)

    def test_clean_push_succeeds(self):
        r = self.push()
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_push_rejected_when_leak_in_earlier_commit(self):
        self.commit_file("_tech/leak.md", "---\ntitle: x\n---\nproj-phoenix 배포\n")
        self.commit_file("_tech/later.md", "---\ntitle: y\n---\n깨끗한 커밋이 뒤에 와도 트리 전체를 본다\n")
        r = self.push()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("_tech/leak.md:4:", r.stderr)
        self.assertNotIn("no-verify", r.stderr)
        self.assertEqual(git(Path(self.tmp.name), "-C", str(self.remote), "rev-list", "--all", "--count").stdout.strip(), "0")

    def test_push_rejected_without_denylist(self):
        (self.repo / ".denylist").unlink()
        r = self.push()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("fail-closed", r.stderr)


if __name__ == "__main__":
    unittest.main()
