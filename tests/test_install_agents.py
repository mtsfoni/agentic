"""Isolated installer checks; never write to the user's OpenCode directory."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]


class InstallAgentsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agentic-install-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.checkout = self.root / "checkout with spaces"
        self.checkout.mkdir()
        for name in ("install-agents.sh", "install-agent-profile.py"):
            if (REPO / name).exists():
                shutil.copy2(REPO / name, self.checkout / name)
        shutil.copytree(REPO / "agents", self.checkout / "agents")
        for profile in ("personal", "work"):
            shutil.copy2(REPO / f"models-{profile}.jsonc", self.checkout)
        self.config = self.root / "config with spaces"
        self.target = self.config / "opencode" / "agents"
        self.env = dict(os.environ, HOME=str(self.root / "home"),
                        XDG_CONFIG_HOME=str(self.config))
        self.env.pop("OPENCODE_AGENT_DIR", None)

    def run_install(self, *args, success=True):
        result = subprocess.run(
            [str(self.checkout / "install-agents.sh"), *args],
            cwd=self.root, env=self.env, text=True, capture_output=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def snapshot(self):
        return {path.name: path.read_bytes() for path in self.target.iterdir()}

    def test_no_profile_preserves_exact_source_and_custom_target(self):
        self.target = self.root / "custom agents"
        self.env["OPENCODE_AGENT_DIR"] = str(self.target)
        self.run_install()
        self.assertEqual(self.snapshot(), {
            path.name: path.read_bytes()
            for path in (self.checkout / "agents").glob("*.md")})

    def test_profiles_repeat_switch_and_remove_pins(self):
        self.config.mkdir()
        global_config = self.config / "opencode.jsonc"
        global_config.write_text('// untouched settings\n{"mcp": {}}\n')
        original_config = global_config.read_bytes()
        originals = {p.name: p.read_bytes()
                     for p in (self.checkout / "agents").glob("*.md")}
        for profile in ("personal", "work"):
            self.run_install("--profile", profile)
            mappings = json.loads((self.checkout / f"models-{profile}.jsonc").read_text())["agent"]
            for name, source in originals.items():
                installed = (self.target / name).read_text()
                model_line = f'model: {json.dumps(mappings[name[:-3]]["model"])}\n'
                self.assertIn(model_line, installed.split("\n---\n", 1)[0])
                self.assertEqual(installed.replace(model_line, "", 1).encode(), source)
            first = self.snapshot()
            self.run_install("--profile", profile)
            self.assertEqual(first, self.snapshot())
        self.run_install()
        self.assertEqual(originals, self.snapshot())
        self.assertEqual(global_config.read_bytes(), original_config)
        self.assertEqual(originals, {p.name: p.read_bytes()
                                    for p in (self.checkout / "agents").glob("*.md")})

    def test_bad_arguments_do_not_create_destination(self):
        for args in (("--profile",), ("--profile", "unknown"),
                     ("--unknown",), ("personal",),
                     ("--profile", "personal", "--profile", "work")):
            with self.subTest(args=args):
                self.run_install(*args, success=False)
                self.assertFalse(self.target.exists())

    def test_invalid_profile_leaves_existing_agents_untouched(self):
        self.run_install()
        original = self.snapshot()
        profile = self.checkout / "models-personal.jsonc"
        for content in ('{invalid', '{"agent": {}}',
                        '{"agent": {"builder": {"model": "bad\\nvalue"}}}'):
            with self.subTest(content=content):
                profile.write_text(content)
                self.run_install("--profile", "personal", success=False)
                self.assertEqual(original, self.snapshot())
        profile.unlink()
        self.run_install("--profile", "personal", success=False)
        self.assertEqual(original, self.snapshot())

    def test_jsonc_comments_and_trailing_commas(self):
        profile = self.checkout / "models-personal.jsonc"
        content = profile.read_text().replace('"agent": {', '// model choices\n  "agent": {')
        content = content.replace('\n  }\n}', '\n  }, /* trailing comma */\n}')
        profile.write_text(content)
        self.run_install("--profile", "personal")

    def test_help_does_not_install(self):
        self.assertIn("--profile", self.run_install("--help").stdout)
        self.assertFalse(self.target.exists())


if __name__ == "__main__":
    unittest.main()
