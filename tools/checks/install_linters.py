#!/usr/bin/env python3
"""Install the pinned actionlint and ShellCheck on GitHub's Linux machines."""

from __future__ import annotations

import hashlib
import os
import stat
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request

from linters import LINTERS

MESSAGE = "meant for GitHub's Linux machines; install locally with Homebrew or your package manager"


def _is_github_linux():
    return sys.platform.startswith("linux") and os.environ.get("GITHUB_PATH")


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def install(linters=LINTERS, fetch=None, dest=None, environ=None, platform=None):
    environ = os.environ if environ is None else environ
    platform = sys.platform if platform is None else platform
    if not str(platform).startswith("linux"):
        sys.stderr.write(MESSAGE + "\n")
        return 1
    github_path = environ.get("GITHUB_PATH")
    if not github_path:
        sys.stderr.write(MESSAGE + "\n")
        return 1
    dest = dest or tempfile.mkdtemp(prefix="polluxkart-linters-")
    if fetch is None:
        def fetch(url):
            try:
                with urllib.request.urlopen(url) as response:
                    return response.read()
            except urllib.error.URLError as error:
                raise error
    for item in linters:
        try:
            blob = fetch(item["url"])
        except urllib.error.URLError as error:
            sys.stderr.write("download failed for %s: %s\n" % (item["url"], error))
            return 1
        digest = _sha256(blob)
        if digest != item["sha256"]:
            sys.stderr.write(
                "%s checksum mismatch: expected %s got %s\n" % (item["name"], item["sha256"], digest)
            )
            return 1
        archive_path = os.path.join(dest, os.path.basename(item["url"]))
        with open(archive_path, "wb") as handle:
            handle.write(blob)
        mode = "r:xz" if item["archive"] == "tar.xz" else "r:gz"
        with tarfile.open(archive_path, mode) as archive:
            member_name = item.get("member") or item["binary"]
            member = archive.getmember(member_name)
            member.name = item["binary"]
            archive.extract(member, dest)
        binary = os.path.join(dest, item["binary"])
        os.chmod(binary, os.stat(binary).st_mode | stat.S_IEXEC)
    with open(github_path, "a") as handle:
        handle.write(dest + "\n")
    return 0


def main(argv=None):
    return install()


if __name__ == "__main__":
    sys.exit(main())
