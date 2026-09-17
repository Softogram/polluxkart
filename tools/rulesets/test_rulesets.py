"""Tests for branch ruleset files and the apply/check script. Never call GitHub."""

from __future__ import annotations

import io
import json
import unittest
from pathlib import Path

import rulesets

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / ".github" / "rulesets"
WORKFLOWS = ROOT / ".github" / "workflows"


class ValidateTest(unittest.TestCase):
    def test_real_files_pass(self) -> None:
        files = rulesets.load_files(FOLDER)
        self.assertEqual(rulesets.validate(files, WORKFLOWS), [])

    def test_docslint_must_not_be_required(self) -> None:
        files = rulesets.load_files(FOLDER)
        for item in files["rulesets"]:
            for rule in item.get("rules") or []:
                if rule.get("type") != "required_status_checks":
                    continue
                for check in rule["parameters"]["required_status_checks"]:
                    if check["context"] == "approval-gate":
                        check["context"] = "docslint"
        problems = rulesets.validate(files, WORKFLOWS)
        self.assertTrue(any("docslint" in p for p in problems))

    def test_development_must_squash(self) -> None:
        files = rulesets.load_files(FOLDER)
        for item in files["rulesets"]:
            if item["name"] == "development":
                for rule in item["rules"]:
                    if rule.get("type") == "pull_request":
                        rule["parameters"]["allowed_merge_methods"] = ["merge"]
        problems = rulesets.validate(files, WORKFLOWS)
        self.assertTrue(any("squash" in p for p in problems))

    def test_owner_bypass_must_be_pull_request(self) -> None:
        files = rulesets.load_files(FOLDER)
        for item in files["rulesets"]:
            if item["name"] == "main-owner-merge":
                item["bypass"][0]["mode"] = "always"
        problems = rulesets.validate(files, WORKFLOWS)
        self.assertTrue(any("pull_request" in p for p in problems))


class DiffTest(unittest.TestCase):
    def test_missing_ruleset(self) -> None:
        expected = rulesets.load_files(FOLDER)
        live = {"rulesets": [], "repository": expected["repository"]}
        differences = rulesets.diff(expected, live)
        self.assertTrue(any("missing" in d.message for d in differences))

    def test_hidden_field(self) -> None:
        expected = rulesets.load_files(FOLDER)
        live = {
            "rulesets": [{"name": item["name"], "enforcement": item["enforcement"]} for item in expected["rulesets"]],
            "repository": {},
        }
        differences = rulesets.diff(expected, live)
        self.assertTrue(any("not visible" in d.message for d in differences))


class ApplyDryRunTest(unittest.TestCase):
    def test_dry_run_does_not_write(self) -> None:
        class Fake:
            def __init__(self):
                self.calls = []

            def api(self, method, path, body=None):
                self.calls.append((method, path))
                if method == "GET" and path.endswith("/rulesets"):
                    return []
                if method == "GET" and "/users/" in path:
                    return {"id": 1}
                if method == "GET" and "/apps/" in path:
                    return {"id": 15368}
                if method == "GET" and path.count("/") == 2:
                    return {
                        "allow_squash_merge": True,
                        "allow_merge_commit": True,
                        "allow_rebase_merge": False,
                        "allow_update_branch": True,
                    }
                return {}

        fake = Fake()
        files = rulesets.load_files(FOLDER)
        notes = rulesets.apply(files, fake, dry_run=True, owner_repo="Softogram/polluxkart")
        writes = [c for c in fake.calls if c[0] in ("PUT", "POST", "PATCH")]
        self.assertEqual(writes, [])
        self.assertTrue(any("create development" in n or "create" in n for n in notes))


class MainValidateTest(unittest.TestCase):
    def test_validate_command(self) -> None:
        stream = io.StringIO()
        code = rulesets.main(["validate"], folder=FOLDER, workflows=WORKFLOWS, stream=stream)
        self.assertEqual(code, 0, stream.getvalue())


if __name__ == "__main__":
    unittest.main()
