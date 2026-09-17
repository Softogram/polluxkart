#!/usr/bin/env python3
"""Pre-commit hook: check the staged docs tree with docslint."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile

ZERO = "0" * 40


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
        check = run([python, script, "--root", temp])
        return check.returncode
    finally:
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
