#!/usr/bin/env python3
import importlib.util
import tempfile
import unittest
from pathlib import Path

P = Path(__file__).with_name("check-runtime-memory-boundary.py")
S = importlib.util.spec_from_file_location("boundary", P)
B = importlib.util.module_from_spec(S)
S.loader.exec_module(B)


class RuntimeMemoryBoundaryTest(unittest.TestCase):
    def _tree(self, files):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return root

    # regression ④: D-4 new-writer detection
    def test_current_tree_is_clean(self):
        self.assertEqual(B.find_violations(B.ROOT), [])

    def test_python_mkdir_targeting_runtime_is_rejected(self):
        root = self._tree({
            "utilities/example.py": (
                "from pathlib import Path\n"
                "def scaffold(root):\n"
                "    Path(root / '_runtime/state').mkdir(parents=True)\n"
            ),
        })
        violations = B.find_violations(root)
        self.assertTrue(violations, violations)
        self.assertIn("_runtime", violations[0])

    def test_python_write_text_targeting_notes_md_is_rejected(self):
        root = self._tree({
            "tools/example.py": (
                "def note(root):\n"
                "    (root / 'NOTES.md').write_text('hi')\n"
            ),
        })
        self.assertTrue(B.find_violations(root))

    def test_shell_mkdir_p_targeting_legacy_agent_memory_is_rejected(self):
        root = self._tree({
            "hooks/example.sh": (
                "#!/usr/bin/env sh\n"
                "mkdir -p \"$ROOT/.claude/agent-memory\"\n"
            ),
        })
        self.assertTrue(B.find_violations(root))

    def test_shell_redirect_targeting_memo_md_is_rejected(self):
        root = self._tree({
            "utilities/example.sh": (
                "#!/usr/bin/env sh\n"
                "echo hello >> \"$ROOT/memo.md\"\n"
            ),
        })
        self.assertTrue(B.find_violations(root))

    def test_read_only_mention_is_not_a_violation(self):
        root = self._tree({
            "utilities/example.py": (
                "# legacy _runtime/ is read-only; do not create it\n"
                "def read_legacy(root):\n"
                "    return (root / '_runtime').is_dir()\n"
            ),
        })
        self.assertEqual(B.find_violations(root), [])

    def test_unrelated_identifier_is_not_a_false_positive(self):
        root = self._tree({
            "utilities/example.py": (
                "def f(parent_runtime, product):\n"
                "    return parent_runtime, product.runtimes\n"
            ),
        })
        self.assertEqual(B.find_violations(root), [])

    def test_doc_prose_outside_fenced_code_is_not_scanned(self):
        root = self._tree({
            "skills/example/SKILL.md": (
                "---\nname: example\n---\n"
                "Never create `_runtime/state` or `NOTES.md` by hand.\n"
            ),
        })
        self.assertEqual(B.find_violations(root), [])

    def test_fenced_code_in_skill_doc_is_scanned(self):
        root = self._tree({
            "skills/example/SKILL.md": (
                "---\nname: example\n---\n"
                "```bash\n"
                "mkdir -p \"$ARTIFACT_ROOT/_runtime/state\"\n"
                "```\n"
            ),
        })
        self.assertTrue(B.find_violations(root))

    def test_test_fixture_files_are_never_scanned(self):
        root = self._tree({
            "hooks/example.test.py": (
                "def test_x():\n"
                "    open('NOTES.md', 'w').write('x')\n"
            ),
        })
        self.assertEqual(B.find_violations(root), [])

    def test_allowlisted_file_is_exempt(self):
        root = self._tree({
            "tools/memory/mem.py": (
                "def log(root):\n"
                "    open(root / '_runtime/events.log', 'w').write('x')\n"
            ),
        })
        self.assertEqual(B.find_violations(root), [])


if __name__ == "__main__":
    unittest.main()
