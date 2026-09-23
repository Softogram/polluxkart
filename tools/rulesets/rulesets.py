#!/usr/bin/env python3
"""Apply and check GitHub branch rulesets from files in .github/rulesets/.

Accounts and apps are stored by name. Numbers are looked up at apply time
so they never land in this public repository.
"""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
from pathlib import Path

FOLDER = Path(__file__).resolve().parents[2] / ".github" / "rulesets"
WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"
REPO = os.environ.get("GITHUB_REPOSITORY") or "Softogram/polluxkart"
FORBIDDEN_CHECKS = {"docslint", "tooling-tests"}
OWNER_LOGIN = "CosmicSaaurabh"
REQUIRED_CHECK_APP = "github-actions"
DECISION_DATE = "2026-09-14"
ADMIN_NEEDED = "an admin login is needed"
BYPASS_NOT_VISIBLE = (
    "bypass lists not visible with this login; run with an admin login for the full check"
)
MATCHES = "GitHub matches the rule files"
NUMERIC_ID_KEYS = {"actor_id", "integration_id"}

# Secret scanning settings live in repository.json as plain true/false, but
# GitHub reads and writes them nested under security_and_analysis (#37).
SECURITY_KEYS = (
    "secret_scanning",
    "secret_scanning_push_protection",
    "secret_scanning_non_provider_patterns",
    "secret_scanning_validity_checks",
)
MERGE_KEYS = (
    "allow_squash_merge",
    "allow_merge_commit",
    "allow_rebase_merge",
    "allow_update_branch",
)


def _security_status(analysis, key):
    """True, False, or None when this login may not see the setting."""
    if not isinstance(analysis, dict):
        return None
    entry = analysis.get(key)
    if not isinstance(entry, dict):
        return None
    status = entry.get("status")
    if status == "enabled":
        return True
    if status == "disabled":
        return False
    return None


def repository_payload(want: dict) -> dict:
    """Split the flat file into the shape GitHub's repository PATCH wants."""
    body = {key: value for key, value in want.items() if key not in SECURITY_KEYS}
    analysis = {}
    for key in SECURITY_KEYS:
        if key in want:
            analysis[key] = {"status": "enabled" if want[key] else "disabled"}
    if analysis:
        body["security_and_analysis"] = analysis
    return body


class GhError(Exception):
    pass


class RulesetFileError(Exception):
    pass


class Difference:
    def __init__(self, message: str, blocking: bool = True) -> None:
        self.message = message
        self.blocking = blocking

    def __repr__(self) -> str:
        return "Difference(%r, blocking=%r)" % (self.message, self.blocking)


class RealGh:
    def __init__(self, run=None) -> None:
        self._run = run or subprocess.run

    def api(self, method: str, path: str, body=None):
        command = ["gh", "api", "-X", method, path]
        if body is not None:
            command.extend(["--input", "-"])
        payload = json.dumps(body) if body is not None else None
        result = self._run(
            command,
            input=payload,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise GhError((result.stderr or result.stdout or "gh api failed").strip())
        if not (result.stdout or "").strip():
            return None
        return json.loads(result.stdout)


def load_files(folder=FOLDER) -> dict:
    folder = Path(folder)
    rulesets = []
    repository = None
    for path in sorted(folder.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as error:
            raise RulesetFileError("%s is not valid JSON" % path.name) from error
        if path.name == "repository.json":
            repository = data
            continue
        data["_file"] = path.name
        rulesets.append(data)
    return {"rulesets": rulesets, "repository": repository}


def _on_block(text: str) -> str:
    lines = []
    capturing = False
    for line in text.splitlines():
        if line.startswith("on:"):
            capturing = True
            lines.append(line)
            continue
        if capturing:
            if line and not line[0].isspace():
                break
            lines.append(line)
    return "\n".join(lines)


def _workflow_jobs(workflows) -> dict:
    """job name -> {on_pull_request, path_filter, has_synchronize}."""
    if isinstance(workflows, dict):
        items = list(workflows.items())
    else:
        items = [(path.name, path.read_text()) for path in sorted(Path(workflows).glob("*.yml"))]
    parsed = {}
    for name, text in items:
        on_block = _on_block(text)
        on_pr = "pull_request" in on_block or "pull_request_target" in on_block
        has_path_filter = bool(re.search(r"(?m)^\s+paths:", on_block))
        types_match = re.search(r"(?m)^\s+types:\s*\[([^\]]*)\]", on_block)
        if types_match:
            has_synchronize = "synchronize" in types_match.group(1)
        else:
            has_synchronize = True
        in_jobs = False
        for line in text.splitlines():
            if line.startswith("jobs:"):
                in_jobs = True
                continue
            if in_jobs and line[:2] == "  " and line[2:3] != " " and line.rstrip().endswith(":"):
                job = line.strip().rstrip(":")
                parsed[job] = {
                    "file": name,
                    "on_pull_request": on_pr,
                    "path_filter": has_path_filter,
                    "has_synchronize": has_synchronize,
                }
            elif in_jobs and line and not line.startswith(" "):
                in_jobs = False
    return parsed


def _numeric_id_problems(value, file_name: str) -> list[str]:
    problems = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in NUMERIC_ID_KEYS:
                problems.append(
                    "%s has %s; accounts and apps are written by name in this public repository"
                    % (file_name, key)
                )
            if key != "_file":
                problems.extend(_numeric_id_problems(child, file_name))
    elif isinstance(value, list):
        for child in value:
            problems.extend(_numeric_id_problems(child, file_name))
    return problems


def validate(files, workflows=WORKFLOWS) -> list[str]:
    problems = []
    rulesets = files.get("rulesets") or []
    seen = {}
    for item in rulesets:
        name = item.get("name")
        file_name = item.get("_file") or name
        if name in seen:
            problems.append("duplicate ruleset name %s in %s and %s" % (name, seen[name], file_name))
        else:
            seen[name] = file_name
        problems.extend(_numeric_id_problems(item, file_name))
    jobs = _workflow_jobs(workflows)
    for item in rulesets:
        name = item.get("name")
        if not item.get("target") == "branch":
            problems.append("%s: target must be branch" % name)
        if item.get("enforcement") != "active":
            problems.append("%s: enforcement must be active" % name)
        bypass = item.get("bypass") or []
        rules = item.get("rules") or []
        types = [rule.get("type") for rule in rules]
        if name == "main-owner-merge":
            if not bypass:
                problems.append("main-owner-merge must have a bypass")
            else:
                entry = bypass[0]
                if entry.get("mode") != "pull_request":
                    problems.append("main-owner-merge bypass must be pull_request only")
                if entry.get("user") != OWNER_LOGIN:
                    problems.append("main-owner-merge bypass user must be %s" % OWNER_LOGIN)
            if types != ["update"]:
                problems.append("main-owner-merge must only restrict updates")
        else:
            if bypass:
                problems.append("%s must not have a bypass" % name)
        pr_rule = next((rule for rule in rules if rule.get("type") == "pull_request"), None)
        checks_rule = next((rule for rule in rules if rule.get("type") == "required_status_checks"), None)
        if name == "development":
            methods = (pr_rule or {}).get("parameters", {}).get("allowed_merge_methods")
            if methods != ["squash"]:
                problems.append(
                    "development must allow only squash merges (owner decision, %s)" % DECISION_DATE
                )
            reviews = (pr_rule or {}).get("parameters", {}).get("required_approving_review_count")
            if reviews != 0:
                problems.append(
                    "development must not require approvals (owner decision, %s)" % DECISION_DATE
                )
            if not (checks_rule or {}).get("parameters", {}).get("strict_required_status_checks_policy"):
                problems.append(
                    "development must require an up-to-date branch (owner decision, %s)" % DECISION_DATE
                )
        if name == "main":
            methods = (pr_rule or {}).get("parameters", {}).get("allowed_merge_methods")
            if methods != ["merge"]:
                problems.append(
                    "main must allow only merge commits (owner decision, %s)" % DECISION_DATE
                )
            reviews = (pr_rule or {}).get("parameters", {}).get("required_approving_review_count")
            if reviews != 0:
                problems.append(
                    "main must not require approvals (owner decision, %s)" % DECISION_DATE
                )
            if not (checks_rule or {}).get("parameters", {}).get("strict_required_status_checks_policy"):
                problems.append(
                    "main must require an up-to-date branch (owner decision, %s)" % DECISION_DATE
                )
        if checks_rule:
            for check in (checks_rule.get("parameters") or {}).get("required_status_checks") or []:
                context = check.get("context")
                branch = name
                if context in FORBIDDEN_CHECKS:
                    problems.append(
                        "%s must not require %s (that workflow does not run on pull requests)"
                        % (name, context)
                    )
                if check.get("app") != REQUIRED_CHECK_APP:
                    problems.append(
                        "%s required check %s must come from the %s app"
                        % (name, context, REQUIRED_CHECK_APP)
                    )
                job = jobs.get(context)
                if job is None:
                    problems.append(
                        "%s required check %s is not a workflow job on branch %s"
                        % (name, context, branch)
                    )
                else:
                    if not job.get("on_pull_request"):
                        problems.append(
                            "%s required check %s does not run on pull requests" % (name, context)
                        )
                    if job.get("path_filter"):
                        problems.append(
                            "%s required check %s has a path filter and could be skipped"
                            % (name, context)
                        )
                    if not job.get("has_synchronize"):
                        problems.append(
                            "%s required check %s would not re-run on new commits (lost synchronize)"
                            % (name, context)
                        )
    repo = files.get("repository") or {}
    if repo.get("allow_rebase_merge") is not False:
        problems.append("repository must turn rebase merging off")
    if repo.get("allow_update_branch") is not True:
        problems.append("repository must suggest updating pull request branches")
    for key in SECURITY_KEYS:
        if repo.get(key) is not True:
            problems.append("repository must turn %s on" % key.replace("_", " "))
    return problems


def _payload(item: dict, resolved: dict) -> dict:
    body = copy.deepcopy({key: value for key, value in item.items() if not key.startswith("_")})
    bypass = []
    for entry in body.get("bypass") or []:
        converted = {"bypass_mode": entry.get("mode")}
        if "user" in entry:
            converted["actor_id"] = resolved["users"][entry["user"]]
            converted["actor_type"] = "User"
        bypass.append(converted)
    body["bypass_actors"] = bypass
    body.pop("bypass", None)
    for rule in body.get("rules") or []:
        if rule.get("type") != "required_status_checks":
            continue
        parameters = rule.setdefault("parameters", {})
        checks = []
        for check in parameters.get("required_status_checks") or []:
            converted = {"context": check["context"]}
            app = check.get("app")
            if app:
                converted["integration_id"] = resolved["apps"][app]
            checks.append(converted)
        parameters["required_status_checks"] = checks
    return body


def resolve_names(files, gh) -> dict:
    users = {}
    apps = {}
    for item in files.get("rulesets") or []:
        for entry in item.get("bypass") or []:
            login = entry.get("user")
            if login and login not in users:
                data = gh.api("GET", "/users/%s" % login)
                if not data or "id" not in data:
                    raise GhError("unknown login %s" % login)
                users[login] = data["id"]
        for rule in item.get("rules") or []:
            if rule.get("type") != "required_status_checks":
                continue
            for check in (rule.get("parameters") or {}).get("required_status_checks") or []:
                app = check.get("app")
                if app and app not in apps:
                    data = gh.api("GET", "/apps/%s" % app)
                    if not data or "id" not in data:
                        raise GhError("unknown app %s" % app)
                    apps[app] = data["id"]
    return {"users": users, "apps": apps}


def live_state(gh, owner_repo=REPO) -> dict:
    owner, name = owner_repo.split("/")
    listed = gh.api("GET", "/repos/%s/%s/rulesets" % (owner, name)) or []
    rulesets = []
    for item in listed:
        detail = gh.api("GET", "/repos/%s/%s/rulesets/%s" % (owner, name, item["id"]))
        rulesets.append(detail)
    try:
        repo = gh.api("GET", "/repos/%s/%s" % (owner, name))
        seen = repo if isinstance(repo, dict) else {}
        analysis = seen.get("security_and_analysis")
        repository = {key: seen.get(key) for key in MERGE_KEYS}
        for key in SECURITY_KEYS:
            repository[key] = _security_status(analysis, key)
    except GhError as error:
        repository = {"error": str(error)}
    return {"rulesets": rulesets, "repository": repository}


def _visible(container, key) -> bool:
    return isinstance(container, dict) and key in container and container.get(key) is not None


def _reverse(mapping: dict) -> dict:
    return {value: key for key, value in mapping.items()}


def _app_label(check: dict, resolved: dict) -> str | None:
    if "app" in check and check.get("app") is not None:
        return check.get("app")
    if not _visible(check, "integration_id"):
        return None
    name = _reverse((resolved or {}).get("apps") or {}).get(check.get("integration_id"))
    if name:
        return name
    return "integration_id:%s" % check.get("integration_id")


def _user_label(actor: dict, resolved: dict) -> str | None:
    if "user" in actor and actor.get("user") is not None:
        return actor.get("user")
    if not _visible(actor, "actor_id"):
        return None
    name = _reverse((resolved or {}).get("users") or {}).get(actor.get("actor_id"))
    if name:
        return name
    return "actor_id:%s" % actor.get("actor_id")


def _bypass_mode(entry: dict) -> str | None:
    if "mode" in entry:
        return entry.get("mode")
    return entry.get("bypass_mode")


def _file_bypass(item: dict) -> list[dict]:
    return [
        {"user": entry.get("user"), "mode": entry.get("mode")}
        for entry in item.get("bypass") or []
    ]


def _live_bypass(item: dict, resolved: dict) -> list[dict]:
    actors = item.get("bypass_actors") or []
    return [
        {"user": _user_label(actor, resolved), "mode": _bypass_mode(actor)}
        for actor in actors
    ]


def _sorted_bypass(entries: list[dict]) -> list[dict]:
    return sorted(entries, key=lambda entry: (entry.get("user") or "", entry.get("mode") or ""))


def _rule_by_type(rules, rule_type: str):
    return next((rule for rule in rules or [] if rule.get("type") == rule_type), None)


def _compare_value(path: str, want, have) -> list[Difference]:
    if want != have:
        return [Difference("%s is %s, expected %s" % (path, have, want))]
    return []


def _ruleset_differences(name: str, want: dict, have: dict, resolved: dict) -> tuple[list[Difference], bool]:
    """Return (differences, bypass_hidden)."""
    differences: list[Difference] = []
    bypass_hidden = False

    if _visible(have, "enforcement"):
        differences.extend(
            _compare_value(
                "ruleset %s enforcement" % name,
                want.get("enforcement"),
                have.get("enforcement"),
            )
        )
    elif "enforcement" in have and have.get("enforcement") is None:
        differences.append(
            Difference("ruleset %s enforcement is not visible with this login" % name, blocking=False)
        )
    elif "enforcement" not in have:
        differences.append(
            Difference("ruleset %s enforcement is not visible with this login" % name, blocking=False)
        )

    if _visible(have, "target"):
        differences.extend(_compare_value("ruleset %s target" % name, want.get("target"), have.get("target")))
    elif "target" not in have or have.get("target") is None:
        differences.append(
            Difference("ruleset %s target is not visible with this login" % name, blocking=False)
        )

    if _visible(have, "conditions"):
        want_ref = ((want.get("conditions") or {}).get("ref_name") or {})
        have_ref = ((have.get("conditions") or {}).get("ref_name") or {})
        if "include" not in have_ref and "exclude" not in have_ref:
            differences.append(
                Difference("ruleset %s branch target is not visible with this login" % name, blocking=False)
            )
        else:
            want_include = sorted(want_ref.get("include") or [])
            have_include = sorted(have_ref.get("include") or [])
            want_exclude = sorted(want_ref.get("exclude") or [])
            have_exclude = sorted(have_ref.get("exclude") or [])
            if want_include != have_include or want_exclude != have_exclude:
                differences.append(
                    Difference(
                        "ruleset %s branch target is include=%s exclude=%s, expected include=%s exclude=%s"
                        % (name, have_include, have_exclude, want_include, want_exclude)
                    )
                )
    elif "conditions" not in have or have.get("conditions") is None:
        differences.append(
            Difference("ruleset %s branch target is not visible with this login" % name, blocking=False)
        )

    if "bypass_actors" not in have or have.get("bypass_actors") is None:
        bypass_hidden = True
    else:
        want_bypass = _sorted_bypass(_file_bypass(want))
        have_bypass = _sorted_bypass(_live_bypass(have, resolved))
        if want_bypass != have_bypass:
            differences.append(
                Difference(
                    "ruleset %s bypass is %s, expected %s" % (name, have_bypass, want_bypass)
                )
            )

    if "rules" not in have or have.get("rules") is None:
        differences.append(
            Difference("ruleset %s rules are not visible with this login" % name, blocking=False)
        )
        return differences, bypass_hidden

    want_rules = want.get("rules") or []
    have_rules = have.get("rules") or []
    want_types = [rule.get("type") for rule in want_rules]
    have_types = [rule.get("type") for rule in have_rules]
    for rule_type in want_types:
        if rule_type not in have_types:
            differences.append(Difference("ruleset %s is missing rule %s" % (name, rule_type)))
    for rule_type in have_types:
        if rule_type not in want_types:
            differences.append(
                Difference("ruleset %s has extra rule %s" % (name, rule_type))
            )

    want_pr = _rule_by_type(want_rules, "pull_request")
    have_pr = _rule_by_type(have_rules, "pull_request")
    if want_pr and have_pr:
        want_params = want_pr.get("parameters") or {}
        have_params = have_pr.get("parameters") or {}
        for key, value in want_params.items():
            if key not in have_params or have_params.get(key) is None:
                differences.append(
                    Difference(
                        "ruleset %s rule pull_request %s is not visible with this login" % (name, key),
                        blocking=False,
                    )
                )
            elif have_params.get(key) != value:
                differences.append(
                    Difference(
                        "ruleset %s rule pull_request %s is %s, expected %s"
                        % (name, key, have_params.get(key), value)
                    )
                )

    want_checks_rule = _rule_by_type(want_rules, "required_status_checks")
    have_checks_rule = _rule_by_type(have_rules, "required_status_checks")
    if want_checks_rule and have_checks_rule:
        want_params = want_checks_rule.get("parameters") or {}
        have_params = have_checks_rule.get("parameters") or {}
        for key, value in want_params.items():
            if key == "required_status_checks":
                continue
            if key not in have_params or have_params.get(key) is None:
                differences.append(
                    Difference(
                        "ruleset %s rule required_status_checks %s is not visible with this login"
                        % (name, key),
                        blocking=False,
                    )
                )
            elif have_params.get(key) != value:
                differences.append(
                    Difference(
                        "ruleset %s rule required_status_checks %s is %s, expected %s"
                        % (name, key, have_params.get(key), value)
                    )
                )
        if "required_status_checks" not in have_params or have_params.get("required_status_checks") is None:
            differences.append(
                Difference(
                    "ruleset %s rule required_status_checks checks are not visible with this login" % name,
                    blocking=False,
                )
            )
        else:
            want_checks = []
            hidden_app = False
            for check in want_params.get("required_status_checks") or []:
                want_checks.append((check.get("context"), check.get("app")))
            have_checks = []
            for check in have_params.get("required_status_checks") or []:
                app = _app_label(check, resolved)
                if app is None:
                    hidden_app = True
                have_checks.append((check.get("context"), app))
            want_contexts = [context for context, _app in want_checks]
            have_contexts = [context for context, _app in have_checks]
            for context, app in want_checks:
                if context not in have_contexts:
                    differences.append(
                        Difference(
                            "ruleset %s rule required_status_checks is missing check %s"
                            % (name, context)
                        )
                    )
                elif app is not None:
                    have_app = dict(have_checks).get(context)
                    if have_app is None:
                        hidden_app = True
                    elif have_app != app:
                        differences.append(
                            Difference(
                                "ruleset %s rule required_status_checks check %s app is %s, expected %s"
                                % (name, context, have_app, app)
                            )
                        )
            for context, _app in have_checks:
                if context not in want_contexts:
                    differences.append(
                        Difference(
                            "ruleset %s rule required_status_checks has extra check %s" % (name, context)
                        )
                    )
            if hidden_app:
                differences.append(
                    Difference(
                        "ruleset %s required check apps are not visible with this login" % name,
                        blocking=False,
                    )
                )

    want_update = _rule_by_type(want_rules, "update")
    have_update = _rule_by_type(have_rules, "update")
    if want_update and have_update:
        want_params = want_update.get("parameters") or {}
        have_params = have_update.get("parameters") or {}
        for key, value in want_params.items():
            if key not in have_params or have_params.get(key) is None:
                differences.append(
                    Difference(
                        "ruleset %s rule update %s is not visible with this login" % (name, key),
                        blocking=False,
                    )
                )
            elif have_params.get(key) != value:
                differences.append(
                    Difference(
                        "ruleset %s rule update %s is %s, expected %s"
                        % (name, key, have_params.get(key), value)
                    )
                )

    return differences, bypass_hidden


def _canonical_ruleset(body: dict) -> dict:
    rules = []
    for rule in copy.deepcopy(body.get("rules") or []):
        entry = {"type": rule.get("type")}
        if "parameters" in rule:
            params = rule["parameters"]
            checks = params.get("required_status_checks")
            if isinstance(checks, list):
                params["required_status_checks"] = sorted(
                    checks,
                    key=lambda check: (
                        check.get("context") or "",
                        check.get("integration_id") or 0,
                    ),
                )
            entry["parameters"] = params
        rules.append(entry)
    rules.sort(key=lambda rule: json.dumps(rule, sort_keys=True))
    actors = sorted(
        copy.deepcopy(body.get("bypass_actors") or []),
        key=lambda actor: json.dumps(actor, sort_keys=True),
    )
    ref = ((body.get("conditions") or {}).get("ref_name") or {})
    return {
        "name": body.get("name"),
        "target": body.get("target"),
        "enforcement": body.get("enforcement"),
        "conditions": {
            "ref_name": {
                "include": sorted(ref.get("include") or []),
                "exclude": sorted(ref.get("exclude") or []),
            }
        },
        "bypass_actors": actors,
        "rules": rules,
    }


def _ruleset_unchanged(file_item: dict, live_item: dict, resolved: dict) -> bool:
    if "bypass_actors" not in live_item or live_item.get("bypass_actors") is None:
        return False
    if "rules" not in live_item or live_item.get("rules") is None:
        return False
    return _canonical_ruleset(_payload(file_item, resolved)) == _canonical_ruleset(live_item)


def _repository_unchanged(want: dict, have: dict) -> bool:
    if not want:
        return True
    if have.get("error"):
        return False
    for key, value in want.items():
        if have.get(key) != value:
            return False
    return True


def diff(expected, live, resolved=None) -> list[Difference]:
    differences: list[Difference] = []
    resolved = resolved or {"users": {}, "apps": {}}
    want = {item["name"]: item for item in expected.get("rulesets") or []}
    have = {item.get("name"): item for item in live.get("rulesets") or []}
    bypass_hidden = False
    for name in sorted(set(want) | set(have)):
        if name not in have:
            differences.append(Difference("ruleset %s is missing on GitHub" % name))
            continue
        if name not in want:
            differences.append(Difference("ruleset %s is on GitHub but not in the files" % name))
            continue
        item_diffs, hidden = _ruleset_differences(name, want[name], have[name], resolved)
        differences.extend(item_diffs)
        bypass_hidden = bypass_hidden or hidden
    if bypass_hidden:
        differences.append(Difference(BYPASS_NOT_VISIBLE, blocking=False))
    repo_want = expected.get("repository") or {}
    repo_have = live.get("repository") or {}
    if repo_have.get("error"):
        differences.append(Difference("repository settings are not visible with this login", blocking=False))
    else:
        for key, value in repo_want.items():
            if key not in repo_have or repo_have.get(key) is None:
                differences.append(Difference("%s is not visible with this login" % key, blocking=False))
            elif repo_have.get(key) != value:
                differences.append(Difference("%s is %s, expected %s" % (key, repo_have.get(key), value)))
    return differences


def _permission_error(error: GhError) -> bool:
    text = str(error)
    return "403" in text or "404" in text


def _write(gh, method: str, path: str, body):
    try:
        return gh.api(method, path, body)
    except GhError as error:
        if _permission_error(error):
            raise GhError(ADMIN_NEEDED) from error
        raise


def apply(files, gh, dry_run=False, owner_repo=REPO, names=None) -> list[str]:
    notes = []
    owner, repo_name = owner_repo.split("/")
    selected = files.get("rulesets") or []
    if names:
        by_name = {item["name"]: item for item in selected}
        missing = [name for name in names if name not in by_name]
        if missing:
            raise GhError("unknown ruleset name %s" % ", ".join(missing))
        selected = [by_name[name] for name in names]
    resolved = resolve_names(files, gh)
    live = live_state(gh, owner_repo)
    have = {item.get("name"): item for item in live.get("rulesets") or []}
    for item in selected:
        existing = have.get(item["name"])
        if existing and _ruleset_unchanged(item, existing, resolved):
            continue
        payload = _payload(item, resolved)
        action = "update" if existing else "create"
        if dry_run:
            notes.append("%s %s" % (action, item["name"]))
            continue
        if existing:
            _write(gh, "PUT", "/repos/%s/%s/rulesets/%s" % (owner, repo_name, existing["id"]), payload)
        else:
            _write(gh, "POST", "/repos/%s/%s/rulesets" % (owner, repo_name), payload)
    repo = files.get("repository")
    if repo and not _repository_unchanged(repo, live.get("repository") or {}):
        if dry_run:
            notes.append("update repository merge settings")
        else:
            _write(gh, "PATCH", "/repos/%s/%s" % (owner, repo_name), repository_payload(repo))
    extra = [name for name in have if name not in {item["name"] for item in files.get("rulesets") or []}]
    for name_extra in extra:
        notes.append("warning: ruleset %s exists on GitHub but not in the files; left alone" % name_extra)
    return notes


def main(argv=None, gh=None, folder=FOLDER, workflows=WORKFLOWS, stream=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    stream = sys.stderr if stream is None else stream
    dry_run = "--dry-run" in argv
    args = [item for item in argv if item != "--dry-run"]
    command = args[0] if args else "validate"
    names = args[1:]
    try:
        files = load_files(folder)
    except RulesetFileError as error:
        stream.write("%s\n" % error)
        return 1
    if command == "validate":
        problems = validate(files, workflows)
        for problem in problems:
            stream.write(problem + "\n")
        return 1 if problems else 0
    client = gh if gh is not None else RealGh()
    try:
        if command == "check":
            resolved = resolve_names(files, client)
            differences = diff(files, live_state(client), resolved)
            for item in differences:
                stream.write(item.message + "\n")
            blocking = [item for item in differences if item.blocking]
            if blocking:
                return 1
            if not differences:
                stream.write(MATCHES + "\n")
            return 0
        if command == "apply":
            notes = apply(files, client, dry_run=dry_run, names=names or None)
            for note in notes:
                stream.write(note + "\n")
            return 0
    except GhError as error:
        stream.write("%s\n" % error)
        return 1
    stream.write("unknown command %s\n" % command)
    return 2


if __name__ == "__main__":
    sys.exit(main())
