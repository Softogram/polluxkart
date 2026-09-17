#!/usr/bin/env python3
"""Apply and check GitHub branch rulesets from files in .github/rulesets/.

Accounts and apps are stored by name. Numbers are looked up at apply time
so they never land in this public repository.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

FOLDER = Path(__file__).resolve().parents[2] / ".github" / "rulesets"
WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"
REPO = os.environ.get("GITHUB_REPOSITORY") or "Softogram/polluxkart"
FORBIDDEN_CHECKS = {"docslint", "tooling-tests"}
OWNER_LOGIN = "CosmicSaaurabh"


class GhError(Exception):
    pass


class Difference:
    def __init__(self, message: str) -> None:
        self.message = message

    def __repr__(self) -> str:
        return "Difference(%r)" % self.message


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
        data = json.loads(path.read_text())
        if path.name == "repository.json":
            repository = data
            continue
        data["_file"] = path.name
        rulesets.append(data)
    return {"rulesets": rulesets, "repository": repository}


def _workflow_jobs(workflows: Path) -> dict:
    """job name -> {on, branches, paths} parsed enough for validate."""
    import re

    jobs = {}
    for path in sorted(workflows.glob("*.yml")):
        text = path.read_text()
        on_pr = bool(re.search(r"^on:\s*$", text, re.M)) and (
            "pull_request" in text or "pull_request_target" in text
        )
        has_path_filter = bool(re.search(r"^\s+paths:\s*$", text, re.M))
        for match in re.finditer(r"^  ([A-Za-z0-9_-]+):\s*$", text, re.M):
            name = match.group(1)
            if name in ("permissions", "concurrency", "env", "defaults"):
                continue
            # job names sit under jobs:
            jobs[name] = {"file": path.name, "on_pull_request": on_pr, "path_filter": has_path_filter, "text": text}
    # Only treat keys that appear under a jobs: block. Re-parse more carefully.
    parsed = {}
    for path in sorted(workflows.glob("*.yml")):
        text = path.read_text()
        on_pr = "pull_request" in text or "pull_request_target" in text
        has_path_filter = bool(re.search(r"(?m)^\s+paths:", text))
        in_jobs = False
        for line in text.splitlines():
            if line.startswith("jobs:"):
                in_jobs = True
                continue
            if in_jobs and line[:2] == "  " and line[2:3] != " " and line.rstrip().endswith(":"):
                name = line.strip().rstrip(":")
                parsed[name] = {
                    "file": path.name,
                    "on_pull_request": on_pr,
                    "path_filter": has_path_filter,
                }
            elif in_jobs and line and not line.startswith(" "):
                in_jobs = False
    return parsed


def validate(files, workflows=WORKFLOWS) -> list[str]:
    problems = []
    rulesets = files.get("rulesets") or []
    names = [item.get("name") for item in rulesets]
    if len(names) != len(set(names)):
        problems.append("ruleset names are not unique: %s" % names)
    jobs = _workflow_jobs(Path(workflows))
    by_name = {item.get("name"): item for item in rulesets}
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
                problems.append("development must allow only squash merges")
            reviews = (pr_rule or {}).get("parameters", {}).get("required_approving_review_count")
            if reviews != 0:
                problems.append("development must not require approvals")
            if not (checks_rule or {}).get("parameters", {}).get("strict_required_status_checks_policy"):
                problems.append("development must require an up-to-date branch")
        if name == "main":
            methods = (pr_rule or {}).get("parameters", {}).get("allowed_merge_methods")
            if methods != ["merge"]:
                problems.append("main must allow only merge commits")
            reviews = (pr_rule or {}).get("parameters", {}).get("required_approving_review_count")
            if reviews != 0:
                problems.append("main must not require approvals")
            if not (checks_rule or {}).get("parameters", {}).get("strict_required_status_checks_policy"):
                problems.append("main must require an up-to-date branch")
        if checks_rule:
            for check in (checks_rule.get("parameters") or {}).get("required_status_checks") or []:
                context = check.get("context")
                if context in FORBIDDEN_CHECKS:
                    problems.append("%s must not require %s (that workflow does not run on pull requests)" % (name, context))
                job = jobs.get(context)
                if job is None:
                    problems.append("%s required check %s is not a workflow job" % (name, context))
                else:
                    if not job.get("on_pull_request"):
                        problems.append("%s required check %s does not run on pull requests" % (name, context))
                    if job.get("path_filter"):
                        problems.append("%s required check %s has a path filter" % (name, context))
    repo = files.get("repository") or {}
    if repo.get("allow_rebase_merge") is not False:
        problems.append("repository must turn rebase merging off")
    if repo.get("allow_update_branch") is not True:
        problems.append("repository must suggest updating pull request branches")
    return problems


def _payload(item: dict, resolved: dict) -> dict:
    body = {key: value for key, value in item.items() if not key.startswith("_")}
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
        checks = []
        for check in (rule.get("parameters") or {}).get("required_status_checks") or []:
            app = check.get("app")
            converted = {"context": check["context"]}
            if app:
                converted["integration_id"] = resolved["apps"][app]
            checks.append(converted)
        rule["parameters"]["required_status_checks"] = checks
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
                    # GitHub Apps slug lookup.
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
        repository = {
            "allow_squash_merge": repo.get("allow_squash_merge"),
            "allow_merge_commit": repo.get("allow_merge_commit"),
            "allow_rebase_merge": repo.get("allow_rebase_merge"),
            "allow_update_branch": repo.get("allow_update_branch"),
        }
    except GhError as error:
        repository = {"error": str(error)}
    return {"rulesets": rulesets, "repository": repository}


def diff(expected, live) -> list[Difference]:
    differences = []
    want = {item["name"]: item for item in expected.get("rulesets") or []}
    have = {item.get("name"): item for item in live.get("rulesets") or []}
    for name in sorted(set(want) | set(have)):
        if name not in have:
            differences.append(Difference("ruleset %s is missing on GitHub" % name))
            continue
        if name not in want:
            differences.append(Difference("ruleset %s exists on GitHub but not in the files" % name))
            continue
        # Compare enforcement and rule types; bypass may be hidden.
        if want[name].get("enforcement") != have[name].get("enforcement"):
            if have[name].get("enforcement") is None:
                differences.append(Difference("ruleset %s enforcement is not visible with this login" % name))
            else:
                differences.append(
                    Difference(
                        "ruleset %s enforcement is %s, expected %s"
                        % (name, have[name].get("enforcement"), want[name].get("enforcement"))
                    )
                )
    repo_want = expected.get("repository") or {}
    repo_have = live.get("repository") or {}
    if repo_have.get("error"):
        differences.append(Difference("repository settings are not visible with this login"))
    else:
        for key, value in repo_want.items():
            if key not in repo_have or repo_have.get(key) is None:
                differences.append(Difference("%s is not visible with this login" % key))
            elif repo_have.get(key) != value:
                differences.append(Difference("%s is %s, expected %s" % (key, repo_have.get(key), value)))
    return differences


def apply(files, gh, dry_run=False, owner_repo=REPO) -> list[str]:
    notes = []
    owner, name = owner_repo.split("/")
    resolved = resolve_names(files, gh)
    live = live_state(gh, owner_repo)
    have = {item.get("name"): item for item in live.get("rulesets") or []}
    for item in files.get("rulesets") or []:
        payload = _payload(item, resolved)
        existing = have.get(item["name"])
        if dry_run:
            notes.append("%s %s" % ("update" if existing else "create", item["name"]))
            continue
        if existing:
            gh.api("PUT", "/repos/%s/%s/rulesets/%s" % (owner, name, existing["id"]), payload)
        else:
            gh.api("POST", "/repos/%s/%s/rulesets" % (owner, name), payload)
    repo = files.get("repository")
    if repo:
        if dry_run:
            notes.append("update repository merge settings")
        else:
            gh.api("PATCH", "/repos/%s/%s" % (owner, name), repo)
    extra = [n for n in have if n not in {item["name"] for item in files.get("rulesets") or []}]
    for name_extra in extra:
        notes.append("warning: ruleset %s exists on GitHub but not in the files; left alone" % name_extra)
    return notes


def main(argv=None, gh=None, folder=FOLDER, workflows=WORKFLOWS, stream=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    stream = sys.stderr if stream is None else stream
    command = argv[0] if argv else "validate"
    dry_run = "--dry-run" in argv
    files = load_files(folder)
    if command == "validate":
        problems = validate(files, workflows)
        for problem in problems:
            stream.write(problem + "\n")
        return 1 if problems else 0
    client = gh if gh is not None else RealGh()
    try:
        if command == "check":
            differences = diff(files, live_state(client))
            for item in differences:
                stream.write(item.message + "\n")
            return 1 if differences else 0
        if command == "apply":
            notes = apply(files, client, dry_run=dry_run)
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
