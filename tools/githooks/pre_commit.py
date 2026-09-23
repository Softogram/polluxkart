#!/usr/bin/env python3
"""Pre-commit hook: check the staged docs tree, then scan it for secrets.

Both checks always run, so neither hides the other's problems. The secret
scan is never skipped: SKIP_LOCAL_CI only affects the pre-push hook.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile


def repo_root(run=subprocess.run):
    result = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "git rev-parse failed").strip())
    return result.stdout.strip()


def main(argv=None, run=subprocess.run, python=None):
    python = sys.executable if python is None else python
    root = repo_root(run=run)
    temp = tempfile.mkdtemp(prefix="polluxkart-pre-commit-")
    try:
        checkout = run(["git", "checkout-index", "--all", "--prefix=%s/" % temp], cwd=root)
        if checkout.returncode != 0:
            return checkout.returncode or 1
        script = os.path.join(root, "tools", "docslint", "docslint.py")
        docs = run([python, script, "--root", temp])
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    scan = os.path.join(root, "tools", "secrets", "scan.py")
    secrets = run([python, scan, "staged"], cwd=root)
    return docs.returncode or secrets.returncode


if __name__ == "__main__":
    sys.exit(main())
