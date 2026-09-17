# Pinned linters installed on GitHub's Linux machines.

# Newest releases as of implementation (2026-09-17).
# make doctor uses the same versions as its minimum for actionlint and ShellCheck.

LINTERS = (
    {
        "name": "actionlint",
        "version": "1.7.12",
        "url": "https://github.com/rhysd/actionlint/releases/download/v1.7.12/actionlint_1.7.12_linux_amd64.tar.gz",
        "sha256": "8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8",
        "archive": "tar.gz",
        "binary": "actionlint",
    },
    {
        "name": "shellcheck",
        "version": "0.11.0",
        "url": "https://github.com/koalaman/shellcheck/releases/download/v0.11.0/shellcheck-v0.11.0.linux.x86_64.tar.xz",
        "sha256": "8c3be12b05d5c177a04c29e3c78ce89ac86f1595681cab149b65b97c4e227198",
        "archive": "tar.xz",
        "binary": "shellcheck",
        "member": "shellcheck-v0.11.0/shellcheck",
    },
)
