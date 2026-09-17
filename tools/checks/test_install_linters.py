"""Unit tests for the Linux-only linter installer. No network."""

from __future__ import annotations

import hashlib
import io
import os
import tarfile
import tempfile
import unittest
import urllib.error
from pathlib import Path

import install_linters
from linters import LINTERS


class InstallLintersTest(unittest.TestCase):
    def test_i1_1_happy_path_extracts_and_appends_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "bin"
            dest.mkdir()
            github_path = Path(tmp) / "github_path"
            github_path.write_text("")
            blobs = {}
            for item in LINTERS:
                archive_path = Path(tmp) / os.path.basename(item["url"])
                mode = "w:xz" if item["archive"] == "tar.xz" else "w:gz"
                member = item.get("member") or item["binary"]
                inner = Path(tmp) / "inner"
                inner.mkdir(exist_ok=True)
                binary = inner / Path(member).name
                binary.write_text("#!/bin/sh\necho ok\n")
                with tarfile.open(archive_path, mode) as archive:
                    archive.add(str(binary), arcname=member)
                data = archive_path.read_bytes()
                blobs[item["url"]] = data
                item_copy = dict(item)
                item_copy["sha256"] = hashlib.sha256(data).hexdigest()
                blobs[item["url"] + "#meta"] = item_copy

            linters = [blobs[item["url"] + "#meta"] for item in LINTERS]

            def fetch(url):
                return blobs[url]

            code = install_linters.install(
                linters=linters,
                fetch=fetch,
                dest=str(dest),
                environ={"GITHUB_PATH": str(github_path)},
                platform="linux",
            )
            self.assertEqual(code, 0)
            self.assertIn(str(dest), github_path.read_text())
            for item in linters:
                binary = dest / item["binary"]
                self.assertTrue(binary.exists())
                self.assertTrue(os.access(binary, os.X_OK))

    def test_i1_2_wrong_checksum_does_not_extract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "bin"
            dest.mkdir()
            github_path = Path(tmp) / "github_path"
            github_path.write_text("")
            linters = [dict(LINTERS[0], sha256="0" * 64)]

            def fetch(url):
                return b"not-the-archive"

            buf = io.StringIO()
            old = __import__("sys").stderr
            __import__("sys").stderr = buf
            try:
                code = install_linters.install(
                    linters=linters,
                    fetch=fetch,
                    dest=str(dest),
                    environ={"GITHUB_PATH": str(github_path)},
                    platform="linux",
                )
            finally:
                __import__("sys").stderr = old
            self.assertEqual(code, 1)
            self.assertIn("checksum", buf.getvalue())
            self.assertFalse((dest / linters[0]["binary"]).exists())

    def test_i1_3_macos_exits_1(self) -> None:
        buf = io.StringIO()
        old = __import__("sys").stderr
        __import__("sys").stderr = buf
        try:
            code = install_linters.install(environ={"GITHUB_PATH": "/tmp/x"}, platform="darwin")
        finally:
            __import__("sys").stderr = old
        self.assertEqual(code, 1)
        self.assertIn("Homebrew", buf.getvalue())

    def test_i1_4_linux_without_github_path_exits_1(self) -> None:
        buf = io.StringIO()
        old = __import__("sys").stderr
        __import__("sys").stderr = buf
        try:
            code = install_linters.install(environ={}, platform="linux")
        finally:
            __import__("sys").stderr = old
        self.assertEqual(code, 1)

    def test_i4_6_pinned_table_shape(self) -> None:
        for item in LINTERS:
            self.assertTrue(item["version"])
            self.assertTrue(item["url"].startswith("https://github.com/"))
            self.assertRegex(item["sha256"], r"^[0-9a-f]{64}$")
            self.assertIn(item["archive"], ("tar.gz", "tar.xz"))
            self.assertTrue(item["binary"])

    def test_i1_5_download_error(self) -> None:
        buf = io.StringIO()
        old = __import__("sys").stderr
        __import__("sys").stderr = buf

        def fetch(url):
            raise urllib.error.URLError("offline")

        try:
            code = install_linters.install(
                linters=LINTERS[:1],
                fetch=fetch,
                dest="/tmp",
                environ={"GITHUB_PATH": "/tmp/github_path"},
                platform="linux",
            )
        finally:
            __import__("sys").stderr = old
        self.assertEqual(code, 1)
        self.assertIn("download failed", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
