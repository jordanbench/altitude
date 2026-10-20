"""Contract tests for the altitude UserPromptSubmit hook.

Stdlib only, so it runs anywhere: python3 tests/test_user_prompt_submit.py
"""

import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
HOOKS_JSON = PLUGIN_ROOT / "hooks" / "hooks.json"
SCRIPT = PLUGIN_ROOT / "hooks" / "user-prompt-submit.sh"
SESSION_START = PLUGIN_ROOT / "hooks" / "session-start.sh"
PLUGIN_NAME = json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text())["name"]

LONG_PROMPT = "Why does the import job skip members with a renewal date?"


class HookTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def run_hook(self, prompt, session="s1", mode="auto", **extra):
        """Runs the hook. Most tests use auto mode; pass mode=None for the default."""
        payload = {
            "session_id": session,
            "transcript_path": "/tmp/t.jsonl",
            "cwd": "/repo",
            "hook_event_name": "UserPromptSubmit",
            "prompt": prompt,
            **extra,
        }
        env = {**os.environ, "TMPDIR": self.tmp.name, "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)}
        env.pop("ALTITUDE_MODE", None)
        if mode:
            env["ALTITUDE_MODE"] = mode
        result = subprocess.run(
            [str(SCRIPT)], input=json.dumps(payload), capture_output=True, text=True, env=env, timeout=5
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return result.stdout

    def context(self, stdout):
        output = json.loads(stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "UserPromptSubmit")
        return output["additionalContext"]

    # Registration

    def test_hooks_json_registers_the_script_on_user_prompt_submit(self):
        config = json.loads(HOOKS_JSON.read_text())
        self.assertEqual(set(config["hooks"]), {"SessionStart", "UserPromptSubmit"})
        commands = [h["command"] for e in config["hooks"]["UserPromptSubmit"] for h in e["hooks"]]
        self.assertEqual(commands, ['"${CLAUDE_PLUGIN_ROOT}/hooks/user-prompt-submit.sh"'])

    def test_script_is_executable(self):
        self.assertTrue(os.access(SCRIPT, os.X_OK), f"{SCRIPT} is not executable")

    def test_named_skill_exists_in_this_plugin(self):
        context = self.context(self.run_hook(LONG_PROMPT))
        self.assertIn(f"`{PLUGIN_NAME}:altitude`", context)
        skill_md = PLUGIN_ROOT / "skills" / "altitude" / "SKILL.md"
        self.assertIn("name: altitude\n", skill_md.read_text())

    # When it runs

    def test_first_prompt_gets_views(self):
        context = self.context(self.run_hook(LONG_PROMPT))
        self.assertIn("four tabs", context)
        self.assertIn("opens on the 10k view", context)

    def test_follow_up_in_same_session_is_skipped(self):
        self.run_hook(LONG_PROMPT)
        self.assertEqual(self.run_hook("And what about the accounts that renewed last month?"), "")

    def test_follow_up_that_asks_for_altitude_gets_views(self):
        self.run_hook(LONG_PROMPT)
        self.assertIn("four tabs", self.context(self.run_hook("Give me the altitude on that")))
        self.assertIn("four tabs", self.context(self.run_hook("show me the 10k view")))

    def test_each_session_has_its_own_first_prompt(self):
        self.run_hook(LONG_PROMPT, session="a")
        self.assertNotEqual(self.run_hook(LONG_PROMPT, session="b"), "")

    def test_short_first_prompt_is_skipped(self):
        self.assertEqual(self.run_hook("merge it"), "")
        self.assertEqual(self.run_hook("what's next", session="s2"), "")

    def test_slash_command_is_skipped(self):
        self.assertEqual(self.run_hook("/investigate the failing import job for this org"), "")

    def test_short_first_prompt_does_not_use_up_the_first_prompt(self):
        self.assertEqual(self.run_hook("hey there"), "")
        self.assertIn("four tabs", self.context(self.run_hook(LONG_PROMPT)))
        self.assertEqual(self.run_hook(LONG_PROMPT), "")

    def test_slash_command_does_not_use_up_the_first_prompt(self):
        self.assertEqual(self.run_hook("/investigate the failing import job for this org"), "")
        self.assertIn("four tabs", self.context(self.run_hook(LONG_PROMPT)))

    def test_suggest_offer_uses_up_the_first_prompt(self):
        self.run_hook(LONG_PROMPT, mode="suggest")
        self.assertEqual(self.run_hook(LONG_PROMPT, mode="suggest"), "")

    def test_no_views_opts_out_and_uses_up_the_first_prompt(self):
        self.assertEqual(self.run_hook("No views, just tell me why the import job failed"), "")
        self.assertEqual(self.run_hook(LONG_PROMPT), "")

    def test_no_altitude_opts_out_even_though_it_says_altitude(self):
        self.assertEqual(self.run_hook("no altitude please, just fix the importer bug"), "")

    def test_altitude_in_cwd_or_paths_does_not_count_as_asking(self):
        self.run_hook(LONG_PROMPT)
        out = self.run_hook("fix the failing test again please", cwd="/repo/altitude")
        self.assertEqual(out, "")

    def test_prompt_with_escaped_quotes_and_newlines_parses(self):
        prompt = 'The "next bill" date is wrong.\nCustomer said:\n"it shows altitude"'
        self.run_hook(LONG_PROMPT)
        self.assertIn("four tabs", self.context(self.run_hook(prompt)))

    def test_missing_session_id_only_runs_when_asked(self):
        env = {**os.environ, "TMPDIR": self.tmp.name}
        env.pop("ALTITUDE_MODE", None)
        quiet = subprocess.run([str(SCRIPT)], input=json.dumps({"prompt": LONG_PROMPT}), capture_output=True, text=True, env=env)
        self.assertEqual(quiet.stdout, "")
        asked = subprocess.run([str(SCRIPT)], input=json.dumps({"prompt": "altitude for this please"}), capture_output=True, text=True, env=env)
        self.assertIn("four tabs", asked.stdout)

    # Modes

    def test_default_mode_is_manual_and_skips_the_first_prompt(self):
        self.assertEqual(self.run_hook(LONG_PROMPT, mode=None), "")

    def test_manual_mode_builds_when_asked(self):
        self.assertIn("four tabs", self.context(self.run_hook("altitude on the import job", mode=None)))
        self.assertIn("four tabs", self.context(self.run_hook("/altitude", mode="manual")))

    def test_manual_mode_respects_no_views(self):
        self.assertEqual(self.run_hook("no altitude, just fix the importer bug", mode="manual"), "")

    def test_suggest_mode_offers_views_in_one_line(self):
        context = self.context(self.run_hook(LONG_PROMPT, mode="suggest"))
        self.assertIn("Want this as altitude views", context)
        self.assertNotIn("four tabs", context)

    def test_suggest_mode_still_builds_when_asked(self):
        self.assertIn("four tabs", self.context(self.run_hook("altitude on the import job", mode="suggest")))

    def test_off_mode_does_nothing(self):
        self.assertEqual(self.run_hook(LONG_PROMPT, mode="off"), "")

    # Session start tip

    def run_session_start(self, mode=None):
        env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)}
        env.pop("ALTITUDE_MODE", None)
        if mode:
            env["ALTITUDE_MODE"] = mode
        # Never close stdin early: a shim that waits on stdin would hang here.
        proc = subprocess.Popen([str(SESSION_START)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        proc.wait(timeout=5)
        stdout = proc.stdout.read()
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            stream.close()
        self.assertEqual(proc.returncode, 0)
        return stdout

    def test_session_start_script_is_executable(self):
        self.assertTrue(os.access(SESSION_START, os.X_OK), f"{SESSION_START} is not executable")

    def test_session_start_shows_the_altitude_tip(self):
        message = json.loads(self.run_session_start())["systemMessage"]
        self.assertIn("/altitude", message)

    def test_session_start_tip_is_hidden_when_off(self):
        self.assertEqual(self.run_session_start(mode="off"), "")

    # Speed

    def test_returns_well_under_100ms(self):
        best = float("inf")
        for i in range(5):
            start = time.perf_counter()
            self.run_hook(LONG_PROMPT, session=f"speed{i}")
            best = min(best, time.perf_counter() - start)
        self.assertLess(best, 0.1, f"hook took {best * 1000:.1f}ms")


if __name__ == "__main__":
    unittest.main(verbosity=2)
