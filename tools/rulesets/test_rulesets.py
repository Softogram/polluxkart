"""Tests for branch ruleset files and the apply/check script. Never call GitHub."""

from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

import rulesets

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / ".github" / "rulesets"
WORKFLOWS = ROOT / ".github" / "workflows"
USER_ID = 1001
APP_ID = 999001
RESOLVED = {"users": {"CosmicSaaurabh": USER_ID}, "apps": {"github-actions": APP_ID}}


def files_copy():
    return copy.deepcopy(rulesets.load_files(FOLDER))


def workflow_texts() -> dict:
    return {path.name: path.read_text() for path in WORKFLOWS.glob("*.yml")}


def matching_repo(files=None) -> dict:
    """The repository as GitHub's API returns it when it matches the files.

    Secret scanning settings come back nested under security_and_analysis,
    not as the plain true/false the file uses (#37).
    """
    wanted = copy.deepcopy((files or files_copy())["repository"])
    live = {
        key: value
        for key, value in wanted.items()
        if key not in rulesets.SECURITY_KEYS and key != rulesets.DEFAULT_SETUP_KEY
    }
    live["security_and_analysis"] = {
        key: {"status": "enabled" if wanted[key] else "disabled"}
        for key in rulesets.SECURITY_KEYS
        if key in wanted
    }
    return live


def matching_default_setup(files=None) -> dict:
    """What GitHub's code scanning default setup endpoint returns.

    Default setup has its own endpoint rather than a field on the
    repository, so the fake answers it separately (#38).
    """
    wanted = (files or files_copy())["repository"]
    return {"state": "configured" if wanted.get(rulesets.DEFAULT_SETUP_KEY) else "not-configured"}


def live_rulesets(files=None, include_bypass=True, extra=None, tweak=None) -> list:
    files = files or files_copy()
    live = []
    for index, item in enumerate(files["rulesets"]):
        payload = rulesets._payload(item, RESOLVED)
        payload["id"] = index + 1
        if not include_bypass:
            payload.pop("bypass_actors", None)
        live.append(payload)
    if tweak:
        tweak(live)
    if extra:
        live.extend(extra)
    return live


class FakeGh:
    def __init__(
        self,
        *,
        rulesets=None,
        repository=None,
        default_setup=None,
        list_error=None,
        write_error=None,
        missing_users=None,
        missing_apps=None,
    ) -> None:
        self.calls = []
        self.rulesets = [] if rulesets is None else list(rulesets)
        self.repository = repository if repository is not None else matching_repo()
        self.default_setup = (
            default_setup if default_setup is not None else matching_default_setup()
        )
        self.list_error = list_error
        self.write_error = write_error
        self.missing_users = set(missing_users or [])
        self.missing_apps = set(missing_apps or [])
        self.users = {"CosmicSaaurabh": USER_ID}
        self.apps = {"github-actions": APP_ID}

    def api(self, method, path, body=None):
        self.calls.append((method, path, body))
        if method in ("POST", "PUT", "PATCH", "DELETE"):
            if self.write_error:
                raise rulesets.GhError(self.write_error)
            return {"ok": True}
        if path.startswith("/users/"):
            login = path.rsplit("/", 1)[-1]
            if login in self.missing_users:
                return {}
            if login in self.users:
                return {"id": self.users[login]}
            return {}
        if path.startswith("/apps/"):
            slug = path.rsplit("/", 1)[-1]
            if slug in self.missing_apps:
                return {}
            if slug in self.apps:
                return {"id": self.apps[slug]}
            return {}
        if path.endswith("/rulesets"):
            if self.list_error:
                raise rulesets.GhError(self.list_error)
            return [{"id": item["id"], "name": item["name"]} for item in self.rulesets]
        if "/rulesets/" in path:
            rid = int(path.rstrip("/").split("/")[-1])
            for item in self.rulesets:
                if item["id"] == rid:
                    return copy.deepcopy(item)
            return {}
        if path.endswith("/code-scanning/default-setup"):
            return copy.deepcopy(self.default_setup)
        return copy.deepcopy(self.repository)

    def writes(self):
        return [call for call in self.calls if call[0] in ("POST", "PUT", "PATCH", "DELETE")]


def run_main(args, fake, folder=FOLDER, workflows=WORKFLOWS):
    stream = io.StringIO()
    code = rulesets.main(args, gh=fake, folder=folder, workflows=workflows, stream=stream)
    return code, stream.getvalue()


class ValidateTest(unittest.TestCase):
    def test_real_files_pass(self) -> None:
        # V2.1
        files = rulesets.load_files(FOLDER)
        self.assertEqual(rulesets.validate(files, WORKFLOWS), [])

    def test_renamed_job_fails(self) -> None:
        # V2.2
        workflows = workflow_texts()
        workflows["approval-gate.yml"] = workflows["approval-gate.yml"].replace(
            "  approval-gate:", "  gate:", 1
        )
        problems = rulesets.validate(files_copy(), workflows)
        self.assertTrue(any("approval-gate" in item and "development" in item for item in problems))

    def test_path_filter_fails(self) -> None:
        # V2.3
        workflows = workflow_texts()
        workflows["approval-gate.yml"] = workflows["approval-gate.yml"].replace(
            "    types: [opened, edited, reopened, synchronize, ready_for_review]\n",
            "    types: [opened, edited, reopened, synchronize, ready_for_review]\n    paths: ['docs/**']\n",
        )
        problems = rulesets.validate(files_copy(), workflows)
        self.assertTrue(any("path filter" in item for item in problems))

    def test_lost_synchronize_fails(self) -> None:
        # V2.4
        workflows = workflow_texts()
        workflows["approval-gate.yml"] = workflows["approval-gate.yml"].replace(
            "types: [opened, edited, reopened, synchronize, ready_for_review]",
            "types: [opened, edited, reopened, ready_for_review]",
        )
        problems = rulesets.validate(files_copy(), workflows)
        self.assertTrue(any("synchronize" in item for item in problems))

    def test_docslint_must_not_be_required(self) -> None:
        files = files_copy()
        for item in files["rulesets"]:
            for rule in item.get("rules") or []:
                if rule.get("type") != "required_status_checks":
                    continue
                for check in rule["parameters"]["required_status_checks"]:
                    if check["context"] == "approval-gate":
                        check["context"] = "docslint"
        problems = rulesets.validate(files, WORKFLOWS)
        self.assertTrue(any("docslint" in item for item in problems))

    def test_development_bypass_forbidden(self) -> None:
        # V2.5
        files = files_copy()
        for item in files["rulesets"]:
            if item["name"] == "development":
                item["bypass"] = [{"user": "CosmicSaaurabh", "mode": "pull_request"}]
        problems = rulesets.validate(files, WORKFLOWS)
        self.assertTrue(any("development must not have a bypass" in item for item in problems))

    def test_owner_bypass_must_be_pull_request(self) -> None:
        # V2.6
        files = files_copy()
        for item in files["rulesets"]:
            if item["name"] == "main-owner-merge":
                item["bypass"][0]["mode"] = "always"
        problems = rulesets.validate(files, WORKFLOWS)
        self.assertTrue(any("pull_request" in item for item in problems))

    def test_second_rule_on_owner_merge_fails(self) -> None:
        # V2.7
        files = files_copy()
        for item in files["rulesets"]:
            if item["name"] == "main-owner-merge":
                item["rules"].append({"type": "deletion"})
        problems = rulesets.validate(files, WORKFLOWS)
        self.assertTrue(any("only restrict updates" in item for item in problems))

    def test_development_must_squash(self) -> None:
        # V2.8
        files = files_copy()
        for item in files["rulesets"]:
            if item["name"] == "development":
                for rule in item["rules"]:
                    if rule.get("type") == "pull_request":
                        rule["parameters"]["allowed_merge_methods"] = ["squash", "merge"]
        problems = rulesets.validate(files, WORKFLOWS)
        self.assertTrue(any("squash" in item and "2026-09-14" in item for item in problems))

    def test_main_must_not_squash(self) -> None:
        # V2.9
        files = files_copy()
        for item in files["rulesets"]:
            if item["name"] == "main":
                for rule in item["rules"]:
                    if rule.get("type") == "pull_request":
                        rule["parameters"]["allowed_merge_methods"] = ["squash"]
        problems = rulesets.validate(files, WORKFLOWS)
        self.assertTrue(any("main must allow only merge" in item and "2026-09-14" in item for item in problems))

    def test_strict_false_fails(self) -> None:
        # V2.10
        files = files_copy()
        for item in files["rulesets"]:
            if item["name"] == "development":
                for rule in item["rules"]:
                    if rule.get("type") == "required_status_checks":
                        rule["parameters"]["strict_required_status_checks_policy"] = False
        problems = rulesets.validate(files, WORKFLOWS)
        self.assertTrue(any("up-to-date" in item and "2026-09-14" in item for item in problems))

    def test_required_review_count_fails(self) -> None:
        # V2.11
        files = files_copy()
        for item in files["rulesets"]:
            if item["name"] == "development":
                for rule in item["rules"]:
                    if rule.get("type") == "pull_request":
                        rule["parameters"]["required_approving_review_count"] = 1
        problems = rulesets.validate(files, WORKFLOWS)
        self.assertTrue(any("approvals" in item and "2026-09-14" in item for item in problems))

    def test_numeric_actor_id_in_files_fails(self) -> None:
        # V2.12
        files = files_copy()
        for item in files["rulesets"]:
            if item["name"] == "main-owner-merge":
                item["bypass"][0]["actor_id"] = 1
        problems = rulesets.validate(files, WORKFLOWS)
        self.assertTrue(any("actor_id" in item for item in problems))

    def test_numeric_integration_id_in_files_fails(self) -> None:
        # V2.12
        files = files_copy()
        for item in files["rulesets"]:
            if item["name"] == "development":
                for rule in item["rules"]:
                    if rule.get("type") == "required_status_checks":
                        rule["parameters"]["required_status_checks"][0]["integration_id"] = APP_ID
        problems = rulesets.validate(files, WORKFLOWS)
        self.assertTrue(any("integration_id" in item for item in problems))

    def test_duplicate_names_and_invalid_json(self) -> None:
        # V2.13
        files = files_copy()
        files["rulesets"].append(copy.deepcopy(files["rulesets"][0]))
        files["rulesets"][-1]["_file"] = "copy.json"
        problems = rulesets.validate(files, WORKFLOWS)
        self.assertTrue(any("duplicate" in item and "development" in item for item in problems))
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "broken.json").write_text("{not json", encoding="utf-8")
            with self.assertRaises(rulesets.RulesetFileError) as ctx:
                rulesets.load_files(folder)
            self.assertIn("broken.json", str(ctx.exception))
            stream = io.StringIO()
            code = rulesets.main(["validate"], folder=folder, workflows=WORKFLOWS, stream=stream)
            self.assertEqual(code, 1)
            self.assertIn("broken.json", stream.getvalue())


class CheckTest(unittest.TestCase):
    def test_live_matches_files(self) -> None:
        # K3.1
        fake = FakeGh(rulesets=live_rulesets(include_bypass=True), repository=matching_repo())
        code, output = run_main(["check"], fake)
        self.assertEqual(code, 0, output)
        self.assertIn("GitHub matches the rule files", output)

    def test_missing_required_check(self) -> None:
        # K3.2
        def drop_check(live):
            for item in live:
                if item["name"] != "development":
                    continue
                for rule in item["rules"]:
                    if rule.get("type") == "required_status_checks":
                        rule["parameters"]["required_status_checks"] = []

        fake = FakeGh(rulesets=live_rulesets(tweak=drop_check), repository=matching_repo())
        code, output = run_main(["check"], fake)
        self.assertEqual(code, 1, output)
        self.assertIn("development", output)
        self.assertIn("required_status_checks", output)
        self.assertIn("approval-gate", output)

    def test_main_missing(self) -> None:
        # K3.3
        live = [item for item in live_rulesets() if item["name"] != "main"]
        fake = FakeGh(rulesets=live, repository=matching_repo())
        code, output = run_main(["check"], fake)
        self.assertEqual(code, 1, output)
        self.assertIn("ruleset main is missing on GitHub", output)

    def test_extra_ruleset(self) -> None:
        # K3.4
        extra = [{"id": 99, "name": "temp", "enforcement": "active", "bypass_actors": [], "rules": []}]
        fake = FakeGh(rulesets=live_rulesets(extra=extra), repository=matching_repo())
        code, output = run_main(["check"], fake)
        self.assertEqual(code, 1, output)
        self.assertIn("ruleset temp is on GitHub but not in the files", output)

    def test_main_enforcement_disabled(self) -> None:
        # K3.5
        def disable_main(live):
            for item in live:
                if item["name"] == "main":
                    item["enforcement"] = "disabled"

        fake = FakeGh(rulesets=live_rulesets(tweak=disable_main), repository=matching_repo())
        code, output = run_main(["check"], fake)
        self.assertEqual(code, 1, output)
        self.assertIn("main", output)
        self.assertIn("disabled", output)

    def test_rebase_merging_on(self) -> None:
        # K3.6
        repo = matching_repo()
        repo["allow_rebase_merge"] = True
        fake = FakeGh(rulesets=live_rulesets(), repository=repo)
        code, output = run_main(["check"], fake)
        self.assertEqual(code, 1, output)
        self.assertIn("allow_rebase_merge", output)

    def test_hidden_bypass_is_not_drift(self) -> None:
        # K3.7
        fake = FakeGh(rulesets=live_rulesets(include_bypass=False), repository=matching_repo())
        code, output = run_main(["check"], fake)
        self.assertEqual(code, 0, output)
        self.assertIn(
            "bypass lists not visible with this login; run with an admin login for the full check",
            output,
        )
        self.assertNotIn("GitHub matches the rule files", output)

    def test_visible_bypass_mismatch_fails(self) -> None:
        # K3.8
        def drop_owner(live):
            for item in live:
                if item["name"] == "main-owner-merge":
                    item["bypass_actors"] = []

        fake = FakeGh(rulesets=live_rulesets(tweak=drop_owner), repository=matching_repo())
        code, output = run_main(["check"], fake)
        self.assertEqual(code, 1, output)
        self.assertIn("main-owner-merge", output)
        self.assertIn("bypass", output)

    def test_gh_failure_never_matches(self) -> None:
        # K3.9
        fake = FakeGh(rulesets=[], repository=matching_repo(), list_error="gh: HTTP 401 not logged in")
        code, output = run_main(["check"], fake)
        self.assertEqual(code, 1, output)
        self.assertIn("not logged in", output)
        self.assertNotIn("matches", output.lower())

    def test_unknown_login_before_compare(self) -> None:
        # K3.10
        fake = FakeGh(rulesets=live_rulesets(), repository=matching_repo(), missing_users=["CosmicSaaurabh"])
        code, output = run_main(["check"], fake)
        self.assertEqual(code, 1, output)
        self.assertIn("CosmicSaaurabh", output)
        self.assertNotIn("matches", output.lower())
        self.assertFalse(any("/rulesets" in call[1] for call in fake.calls))


class DefaultSetupTest(unittest.TestCase):
    """CodeQL default setup must be turned off through its own endpoint (#38)."""

    def _apply(self, state):
        fake = FakeGh(
            rulesets=live_rulesets(include_bypass=True),
            repository=matching_repo(),
            default_setup={"state": state},
        )
        code, output = run_main(["apply"], fake)
        return fake, code, output

    def test_default_setup_is_switched_off_when_github_has_it_on(self) -> None:
        fake, code, _output = self._apply("configured")
        self.assertEqual(code, 0)
        writes = [call for call in fake.writes() if "default-setup" in call[1]]
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0][0], "PATCH")
        self.assertEqual(writes[0][2], {"state": "not-configured"})

    def test_nothing_is_written_when_it_is_already_off(self) -> None:
        fake, code, _output = self._apply("not-configured")
        self.assertEqual(code, 0)
        self.assertEqual([call for call in fake.writes() if "default-setup" in call[1]], [])

    def test_check_reports_default_setup_left_on(self) -> None:
        fake = FakeGh(
            rulesets=live_rulesets(include_bypass=True),
            repository=matching_repo(),
            default_setup={"state": "configured"},
        )
        code, output = run_main(["check"], fake)
        self.assertEqual(code, 1, output)
        self.assertIn("code_scanning_default_setup", output)

    def test_not_visible_without_an_admin_login(self) -> None:
        fake = FakeGh(
            rulesets=live_rulesets(include_bypass=True),
            repository=matching_repo(),
            default_setup={},
        )
        code, output = run_main(["check"], fake)
        self.assertIn("not visible with this login", output)
        self.assertEqual(code, 0, output)


class ApplyTest(unittest.TestCase):
    def test_creates_all_three_with_resolved_names(self) -> None:
        # A4.1
        fake = FakeGh(rulesets=[], repository={"allow_rebase_merge": True})
        code, output = run_main(["apply"], fake)
        self.assertEqual(code, 0, output)
        posts = [call for call in fake.writes() if call[0] == "POST"]
        patches = [call for call in fake.writes() if call[0] == "PATCH"]
        self.assertEqual(len(posts), 3, fake.writes())
        self.assertEqual(len(patches), 1)
        created = {body["name"] for _method, _path, body in posts}
        self.assertEqual(created, {"development", "main", "main-owner-merge"})
        for _method, _path, body in posts:
            blob = json.dumps(body)
            self.assertNotIn('"user"', blob)
            self.assertNotIn('"app"', blob)
            if body["name"] == "main-owner-merge":
                self.assertEqual(body["bypass_actors"][0]["actor_id"], USER_ID)
            if body["name"] in {"development", "main"}:
                checks = [
                    check
                    for rule in body["rules"]
                    if rule.get("type") == "required_status_checks"
                    for check in rule["parameters"]["required_status_checks"]
                ]
                self.assertEqual(checks[0]["integration_id"], APP_ID)
        self.assertEqual(set(patches[0][2]), set(matching_repo()))

    def test_updates_only_development_when_it_differs(self) -> None:
        # A4.2
        def disable_development(live):
            for item in live:
                if item["name"] == "development":
                    item["enforcement"] = "disabled"

        fake = FakeGh(rulesets=live_rulesets(tweak=disable_development), repository=matching_repo())
        code, output = run_main(["apply"], fake)
        self.assertEqual(code, 0, output)
        writes = fake.writes()
        self.assertEqual(len(writes), 1, writes)
        method, path, body = writes[0]
        self.assertEqual(method, "PUT")
        self.assertIn("/rulesets/1", path)
        self.assertEqual(body["name"], "development")

    def test_dry_run_does_not_write(self) -> None:
        # A4.3
        fake = FakeGh(rulesets=[], repository={"allow_rebase_merge": True})
        code, output = run_main(["apply", "--dry-run"], fake)
        self.assertEqual(code, 0, output)
        self.assertEqual(fake.writes(), [])
        self.assertIn("create development", output)
        self.assertIn("create main", output)
        self.assertIn("create main-owner-merge", output)
        self.assertIn("update repository merge settings", output)

    def test_extra_ruleset_is_not_deleted(self) -> None:
        # A4.4
        extra = [{"id": 99, "name": "temp", "enforcement": "active", "bypass_actors": [], "rules": []}]
        fake = FakeGh(rulesets=live_rulesets(extra=extra), repository=matching_repo())
        code, output = run_main(["apply"], fake)
        self.assertEqual(code, 0, output)
        self.assertIn("temp", output)
        self.assertFalse(any(call[0] == "DELETE" for call in fake.calls))

    def test_403_stops_further_writes(self) -> None:
        # A4.5
        fake = FakeGh(rulesets=[], repository={"allow_rebase_merge": True}, write_error="HTTP 403 Forbidden")
        code, output = run_main(["apply"], fake)
        self.assertEqual(code, 1, output)
        self.assertIn("an admin login is needed", output)
        self.assertEqual(len(fake.writes()), 1, fake.writes())

    def test_unresolved_name_before_any_write(self) -> None:
        # A4.6
        fake = FakeGh(rulesets=[], missing_users=["CosmicSaaurabh"])
        code, output = run_main(["apply"], fake)
        self.assertEqual(code, 1, output)
        self.assertIn("CosmicSaaurabh", output)
        self.assertEqual(fake.writes(), [])

    def test_request_bodies_use_github_fields(self) -> None:
        # A4.7
        fake = FakeGh(rulesets=[], repository={"allow_rebase_merge": True})
        run_main(["apply"], fake)
        for method, _path, body in fake.writes():
            if method == "PATCH":
                continue
            dumped = json.dumps(body)
            self.assertNotIn('"user"', dumped)
            self.assertNotIn('"app"', dumped)
            self.assertIn("bypass_actors", body)

    def test_payload_does_not_mutate_loaded_files(self) -> None:
        files = rulesets.load_files(FOLDER)
        original = copy.deepcopy(files)
        rulesets._payload(files["rulesets"][0], RESOLVED)
        self.assertEqual(files, original)
        self.assertEqual(
            files["rulesets"][0]["rules"][-1]["parameters"]["required_status_checks"][0]["app"],
            "github-actions",
        )

    def test_named_apply_only_creates_development(self) -> None:
        fake = FakeGh(rulesets=[], repository={"allow_rebase_merge": True})
        code, output = run_main(["apply", "development"], fake)
        self.assertEqual(code, 0, output)
        posts = [call for call in fake.writes() if call[0] == "POST"]
        self.assertEqual(len(posts), 1, fake.writes())
        self.assertEqual(posts[0][2]["name"], "development")
        self.assertEqual(len([call for call in fake.writes() if call[0] == "PATCH"]), 1)


class MainValidateTest(unittest.TestCase):
    def test_validate_command(self) -> None:
        stream = io.StringIO()
        code = rulesets.main(["validate"], folder=FOLDER, workflows=WORKFLOWS, stream=stream)
        self.assertEqual(code, 0, stream.getvalue())


if __name__ == "__main__":
    unittest.main()
