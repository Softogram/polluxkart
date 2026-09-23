"""Tests for the pin check, dependabot.yml and the CodeQL configuration.

Test plan: docs/design/test/issue-38-dependabot-codeql.md

Two rows of that plan are not implemented as written, because a later owner
decision replaced them. The plan was written on 2026-09-14, when CodeQL was
to run on every pull request and block a merge on a high finding. On
2026-09-16 the owner decided the local `make ci` is the pull-request gate,
so CodeQL runs at release, weekly and by hand, and cannot block a merge
(decisions.md, "Dependabot and CodeQL", revised 2026-09-16). Q3.1 and Q3.2
are therefore written against the triggers the design actually specifies,
and Q3.6 and Q3.7, which require a code scanning merge rule, are replaced
by a test that there is no such rule.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import miniyaml  # noqa: E402
import workflow_pins  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "3d3c42e5aac5ba805825da76410c181273ba90b1"
DEPENDABOT = ROOT / ".github" / "dependabot.yml"
CODEQL = ROOT / ".github" / "workflows" / "codeql.yml"
CODEQL_CONFIG = ROOT / ".github" / "codeql" / "codeql-config.yml"

# Ecosystems whose major updates go through a planned ticket instead of a
# Dependabot pull request (owner decision, 2026-09-14). GitHub Actions is
# deliberately not here: its majors are still proposed.
MAJORS_SKIPPED = ("maven", "npm", "docker")
MAJOR_IGNORE = "version-update:semver-major"

# A language CodeQL should analyse once the folder it covers exists.
LANGUAGE_FOLDERS = {"java-kotlin": "api", "javascript-typescript": "web"}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _workflow(body):
    return "name: t\non: push\njobs:\n  j:\n    runs-on: ubuntu-24.04\n    steps:\n%s" % body


# ------------------------------------------------------- Flow 1: the pin check


class PinCheckTest(unittest.TestCase):
    def test_p1_1_the_real_workflows_pass(self):
        self.assertEqual(workflow_pins.check_all(str(ROOT)), [])

    def test_p1_2_commit_with_a_version_comment_passes(self):
        text = _workflow("      - uses: actions/checkout@%s # v7.0.1\n" % COMMIT)
        self.assertEqual(workflow_pins.check_text(text, "t.yml"), [])

    def test_p1_3_a_version_tag_fails(self):
        problems = workflow_pins.check_text(_workflow("      - uses: actions/checkout@v7\n"), "t.yml")
        self.assertEqual(len(problems), 1)
        self.assertIn("t.yml:7", problems[0])
        self.assertIn("not pinned to a commit", problems[0])

    def test_p1_4_a_branch_name_fails(self):
        problems = workflow_pins.check_text(_workflow("      - uses: actions/checkout@main\n"), "t.yml")
        self.assertEqual(len(problems), 1)
        self.assertIn("not pinned to a commit", problems[0])

    def test_p1_5_a_short_commit_fails(self):
        text = _workflow("      - uses: actions/checkout@%s # v7.0.1\n" % COMMIT[:39])
        problems = workflow_pins.check_text(text, "t.yml")
        self.assertEqual(len(problems), 1)
        self.assertIn("not pinned to a commit", problems[0])

    def test_p1_6_a_commit_without_a_version_comment_fails(self):
        problems = workflow_pins.check_text(
            _workflow("      - uses: actions/checkout@%s\n" % COMMIT), "t.yml"
        )
        self.assertEqual(len(problems), 1)
        self.assertIn("add the version as a comment", problems[0])

    def test_p1_7_an_action_in_a_subfolder_passes(self):
        text = _workflow("      - uses: github/codeql-action/init@%s # v4.38.1\n" % COMMIT)
        self.assertEqual(workflow_pins.check_text(text, "t.yml"), [])

    def test_p1_8_a_local_action_passes(self):
        text = _workflow("      - uses: ./.github/actions/local\n")
        self.assertEqual(workflow_pins.check_text(text, "t.yml"), [])

    def test_p1_9_a_docker_digest_passes(self):
        text = _workflow("      - uses: docker://alpine@sha256:%s\n" % ("a" * 64))
        self.assertEqual(workflow_pins.check_text(text, "t.yml"), [])

    def test_p1_10_a_docker_tag_fails(self):
        problems = workflow_pins.check_text(_workflow("      - uses: docker://alpine:3.20\n"), "t.yml")
        self.assertEqual(len(problems), 1)
        self.assertIn("sha256", problems[0])

    def test_p1_11_a_commented_out_uses_line_is_ignored(self):
        text = _workflow("      # - uses: actions/checkout@v7\n      - run: echo hello\n")
        self.assertEqual(workflow_pins.check_text(text, "t.yml"), [])

    def test_p1_12_make_ci_runs_this_check(self):
        """The `workflow-pins` check in make ci runs exactly this command.

        The whole of make ci is not run here because it takes minutes; the
        pull request records a real run. This runs the very argv make ci
        builds, against a copy carrying an unpinned action.
        """
        checks = _load("checks_module", ROOT / "tools" / "checks" / "checks.py")
        entry = [item for item in checks.CHECKS if item[0] == "workflow-pins"]
        self.assertEqual(len(entry), 1, "make ci has no workflow-pins check")
        self.assertEqual(entry[0][1], "tooling")
        argv = checks._python_command(entry[0], sys.executable)
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "repo"
            (copy / ".github" / "workflows").mkdir(parents=True)
            (copy / "tools" / "checks").mkdir(parents=True)
            for name in ("workflow_pins.py",):
                (copy / "tools" / "checks" / name).write_text(
                    (ROOT / "tools" / "checks" / name).read_text()
                )
            (copy / ".github" / "workflows" / "bad.yml").write_text(
                _workflow("      - uses: actions/checkout@v7\n")
            )
            result = subprocess.run(argv, cwd=str(copy), capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("not pinned to a commit", result.stdout)


# ------------------------------------------------------ Flow 2: dependabot.yml


class DependabotTest(unittest.TestCase):
    def setUp(self):
        self.config = miniyaml.load_file(str(DEPENDABOT))

    def _problems(self, config):
        """The rules every dependabot.yml in this repository must follow."""
        problems = []
        if config.get("version") != 2:
            problems.append("dependabot.yml must say version: 2")
        for entry in config.get("updates") or []:
            eco = entry.get("package-ecosystem")
            where = "the %s entry" % eco
            if entry.get("target-branch") != "development":
                problems.append("%s must target development" % where)
            folder = (entry.get("directory") or "").lstrip("/")
            if not (ROOT / folder).is_dir():
                problems.append("%s points at %s, which does not exist" % (where, entry.get("directory")))
            if entry.get("open-pull-requests-limit") == 0:
                problems.append("%s must not stop updates being proposed" % where)
            for key in ("auto-merge", "automerge"):
                if key in entry:
                    problems.append("%s must not auto-merge; only the owner merges" % where)
            groups = entry.get("groups") or {}
            if not groups:
                problems.append("%s must group its updates into one pull request" % where)
            ignores = [
                item
                for item in (entry.get("ignore") or [])
                if MAJOR_IGNORE in (item.get("update-types") or [])
            ]
            if eco in MAJORS_SKIPPED and not ignores:
                problems.append("%s must ignore major updates; a ticket plans those" % where)
            if eco == "github-actions" and ignores:
                problems.append("%s must still propose major updates" % where)
        return problems

    def test_d2_1_the_real_file_passes(self):
        self.assertEqual(self._problems(self.config), [])
        entries = self.config["updates"]
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["package-ecosystem"], "github-actions")
        self.assertEqual(entry["directory"], "/")
        self.assertEqual(
            entry["schedule"],
            {"interval": "weekly", "day": "monday", "time": "09:00", "timezone": "Asia/Kolkata"},
        )
        group = entry["groups"]["github-actions"]
        self.assertEqual(group["patterns"], ["*"])
        self.assertEqual(sorted(group["update-types"]), ["major", "minor", "patch"])

    def _with(self, entry):
        return {"version": 2, "updates": [entry]}

    def _maven(self, **changes):
        entry = {
            "package-ecosystem": "maven",
            "directory": "/",
            "target-branch": "development",
            "groups": {"maven": {"patterns": ["*"], "update-types": ["minor", "patch"]}},
            "ignore": [{"dependency-name": "*", "update-types": [MAJOR_IGNORE]}],
        }
        entry.update(changes)
        return entry

    def test_d2_2_a_complete_maven_entry_passes(self):
        self.assertEqual(self._problems(self._with(self._maven())), [])

    def test_d2_3_a_maven_entry_without_the_major_ignore_fails(self):
        problems = self._problems(self._with(self._maven(ignore=[])))
        self.assertEqual(len(problems), 1)
        self.assertIn("must ignore major updates", problems[0])

    def test_d2_4_an_entry_without_a_group_fails(self):
        problems = self._problems(self._with(self._maven(groups={})))
        self.assertTrue(any("must group its updates" in item for item in problems))

    def test_d2_5_an_entry_targeting_main_fails(self):
        problems = self._problems(self._with(self._maven(**{"target-branch": "main"})))
        self.assertTrue(any("must target development" in item for item in problems))

    def test_d2_6_actions_ignoring_majors_fails(self):
        entry = {
            "package-ecosystem": "github-actions",
            "directory": "/",
            "target-branch": "development",
            "groups": {"github-actions": {"patterns": ["*"]}},
            "ignore": [{"dependency-name": "*", "update-types": [MAJOR_IGNORE]}],
        }
        problems = self._problems(self._with(entry))
        self.assertTrue(any("must still propose major updates" in item for item in problems))

    def test_d2_7_an_entry_for_a_missing_folder_fails(self):
        problems = self._problems(self._with(self._maven(directory="/api")))
        self.assertTrue(any("does not exist" in item for item in problems))

    def test_d2_8_stopping_or_auto_merging_updates_fails(self):
        stopped = self._problems(self._with(self._maven(**{"open-pull-requests-limit": 0})))
        self.assertTrue(any("must not stop updates" in item for item in stopped))
        merged = self._problems(self._with(self._maven(**{"auto-merge": True})))
        self.assertTrue(any("must not auto-merge" in item for item in merged))


# --------------------------------------------------- Flow 3: CodeQL settings


class CodeqlTest(unittest.TestCase):
    def setUp(self):
        self.workflow = miniyaml.load_file(str(CODEQL))
        self.job = self.workflow["jobs"]["analyze"]

    def test_q3_1_the_real_workflow_runs_at_release_weekly_and_by_hand(self):
        triggers = self.workflow["on"]
        self.assertEqual(triggers["push"]["branches"], ["main"])
        self.assertIn("workflow_dispatch", triggers)
        self.assertTrue(triggers["schedule"][0]["cron"])
        # Owner decision, 2026-09-16: CodeQL does not run on pull requests.
        self.assertNotIn("pull_request", triggers)
        self.assertEqual(self.workflow["permissions"], {"contents": "read"})
        self.assertEqual(
            self.job["permissions"], {"contents": "read", "security-events": "write"}
        )
        self.assertEqual(self.job["strategy"]["matrix"]["language"], ["actions", "python"])

    def test_q3_2_a_path_filter_on_the_triggers_is_refused(self):
        """A path filter would silently skip runs that the owner expects."""
        problems = self._trigger_problems(
            {"push": {"branches": ["main"], "paths": ["tools/**"]}, "workflow_dispatch": None}
        )
        self.assertTrue(any("path filter" in item for item in problems))
        self.assertEqual(self._trigger_problems(self.workflow["on"]), [])

    def _trigger_problems(self, triggers):
        problems = []
        for name, body in (triggers or {}).items():
            if isinstance(body, dict) and ("paths" in body or "paths-ignore" in body):
                problems.append("the %s trigger has a path filter, so runs would be skipped" % name)
        return problems

    def test_q3_3_the_config_skips_legacy(self):
        config = miniyaml.load_file(str(CODEQL_CONFIG))
        self.assertIn("legacy/**", config["paths-ignore"])

    def test_q3_4_a_language_without_its_folder_is_refused(self):
        problems = self._language_problems(["actions", "python", "java-kotlin"])
        self.assertEqual(len(problems), 1)
        self.assertIn("java-kotlin", problems[0])

    def test_q3_5_a_folder_without_its_language_is_refused(self):
        problems = self._language_problems(
            ["actions", "python"], folders={"java-kotlin": "tools"}
        )
        self.assertEqual(len(problems), 1)
        self.assertIn("java-kotlin", problems[0])

    def test_q3_5_the_real_matrix_matches_the_folders_that_exist(self):
        self.assertEqual(self._language_problems(self.job["strategy"]["matrix"]["language"]), [])

    def _language_problems(self, languages, folders=None):
        folders = LANGUAGE_FOLDERS if folders is None else folders
        problems = []
        for language, folder in folders.items():
            exists = (ROOT / folder).is_dir()
            listed = language in languages
            if listed and not exists:
                problems.append("%s is analysed but %s/ does not exist" % (language, folder))
            if exists and not listed:
                problems.append("%s/ exists but %s is not analysed" % (folder, language))
        return problems

    def test_q3_6_there_is_no_code_scanning_merge_rule(self):
        """Replaces Q3.6 and Q3.7 of the test plan.

        Those rows expect a code scanning rule on development that blocks a
        merge on a high finding. The owner revised that on 2026-09-16:
        CodeQL does not run on pull requests, so such a rule would wait for
        a result that never arrives.
        """
        rulesets = _load("rulesets_module", ROOT / "tools" / "rulesets" / "rulesets.py")
        files = rulesets.load_files()
        development = [item for item in files["rulesets"] if item["name"] == "development"][0]
        types = [rule["type"] for rule in development["rules"]]
        self.assertNotIn("code_scanning", types)
        self.assertEqual(rulesets.validate(files), [])

    def test_q3_8_settings_require_security_updates_and_no_default_setup(self):
        rulesets = _load("rulesets_module", ROOT / "tools" / "rulesets" / "rulesets.py")
        files = rulesets.load_files()
        self.assertIs(files["repository"]["dependabot_security_updates"], True)
        self.assertIs(files["repository"][rulesets.DEFAULT_SETUP_KEY], False)
        weakened = rulesets.load_files()
        weakened["repository"][rulesets.DEFAULT_SETUP_KEY] = True
        self.assertTrue(
            any("default setup off" in problem for problem in rulesets.validate(weakened))
        )
        without = rulesets.load_files()
        without["repository"]["dependabot_security_updates"] = False
        self.assertTrue(
            any("dependabot security updates" in problem for problem in rulesets.validate(without))
        )


if __name__ == "__main__":
    unittest.main()
