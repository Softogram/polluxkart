#!/usr/bin/env python3
"""A very small YAML reader for the configuration files in this repository.

The checks here use the standard library only, and Python has no YAML
reader built in. A full YAML parser is far more than these files need, so
this reads the handful of shapes `.github/dependabot.yml` and the workflow
files actually use:

- mappings nested by indentation (`key:` then indented keys below)
- lists written as `- item` lines
- lists written inline as `[a, b]`
- mappings written inline as `{a: b, c: d}`
- plain, single-quoted and double-quoted scalars
- `#` comments and blank lines

Anything else raises YamlError rather than guessing, so a file this reader
cannot understand fails the check loudly instead of passing by accident.
"""

from __future__ import annotations

import re

TRUE_WORDS = ("true", "yes", "on")
FALSE_WORDS = ("false", "no", "off")
KEY_RE = re.compile(r"^([A-Za-z_][\w.-]*|\"[^\"]*\"|'[^']*')\s*:(\s.*)?$")


class YamlError(Exception):
    """The reader met something it was not built to understand."""


def _strip_comment(line):
    out = []
    quote = None
    for index, char in enumerate(line):
        if quote:
            out.append(char)
            if char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
            out.append(char)
            continue
        if char == "#" and (index == 0 or line[index - 1] in " \t"):
            break
        out.append(char)
    return "".join(out).rstrip()


def _scalar(text):
    text = text.strip()
    if not text:
        return None
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    lowered = text.lower()
    if lowered in TRUE_WORDS:
        return True
    if lowered in FALSE_WORDS:
        return False
    if lowered in ("null", "~"):
        return None
    if re.match(r"^-?\d+$", text):
        return int(text)
    return text


def _key(text):
    """Keys stay text.

    YAML 1.1 reads a bare `on` as the boolean true, which would turn a
    workflow's `on:` block into a key named true. Keys here are always the
    word that was written.
    """
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    return text


def _split_top_level(text):
    """Split on commas that are not inside quotes, brackets or braces."""
    parts = []
    depth = 0
    quote = None
    current = []
    for char in text:
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
            current.append(char)
            continue
        if char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    if quote:
        raise YamlError("unclosed quote in %r" % text)
    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return [part.strip() for part in parts if part.strip()]


def _inline(text):
    text = text.strip()
    if text.startswith("[") and text.endswith("]"):
        return [_inline(part) for part in _split_top_level(text[1:-1])]
    if text.startswith("{") and text.endswith("}"):
        result = {}
        for part in _split_top_level(text[1:-1]):
            key, sep, value = part.partition(":")
            if not sep:
                raise YamlError("inline mapping entry without a colon: %r" % part)
            result[_key(key)] = _inline(value)
        return result
    return _scalar(text)


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def _rows(text):
    rows = []
    for number, raw in enumerate(text.splitlines(), start=1):
        if "\t" in raw[: _indent(raw) + 1]:
            raise YamlError("line %s is indented with a tab" % number)
        line = _strip_comment(raw)
        if not line.strip():
            continue
        if line.strip() in ("---", "..."):
            continue
        rows.append((_indent(line), line.strip(), number))
    return rows


def _parse_block(rows, start, indent):
    """Read one block at this indent. Returns (value, next index)."""
    if start >= len(rows):
        return None, start
    if rows[start][1].startswith("- "):
        return _parse_list(rows, start, indent)
    return _parse_map(rows, start, indent)


def _parse_list(rows, start, indent):
    items = []
    index = start
    while index < len(rows):
        level, text, number = rows[index]
        if level < indent:
            break
        if level > indent:
            raise YamlError("line %s is indented too far inside a list" % number)
        if not text.startswith("- "):
            if text == "-":
                raise YamlError("line %s has an empty list entry" % number)
            break
        body = text[2:].strip()
        index += 1
        match = KEY_RE.match(body)
        if match:
            # "- key: value" starts a mapping whose later keys sit under the dash.
            inner_rows = [(indent + 2, body, number)]
            while index < len(rows) and rows[index][0] > indent and not rows[index][1].startswith("- "):
                inner_rows.append(rows[index])
                index += 1
            value, _ = _parse_map(inner_rows, 0, inner_rows[0][0])
            items.append(value)
        else:
            items.append(_inline(body))
    return items, index


def _parse_map(rows, start, indent):
    result = {}
    index = start
    while index < len(rows):
        level, text, number = rows[index]
        if level < indent:
            break
        if level > indent:
            raise YamlError("line %s is indented too far" % number)
        if text.startswith("- "):
            break
        match = KEY_RE.match(text)
        if not match:
            raise YamlError("line %s is not a key: %r" % (number, text))
        key = _key(match.group(1))
        rest = (match.group(2) or "").strip()
        index += 1
        if rest:
            result[key] = _inline(rest)
            continue
        if index < len(rows) and rows[index][0] > level:
            value, index = _parse_block(rows, index, rows[index][0])
            result[key] = value
        elif index < len(rows) and rows[index][0] == level and rows[index][1].startswith("- "):
            value, index = _parse_list(rows, index, level)
            result[key] = value
        else:
            result[key] = None
    return result, index


def load(text):
    rows = _rows(text)
    if not rows:
        return None
    value, index = _parse_block(rows, 0, rows[0][0])
    if index != len(rows):
        raise YamlError("line %s was not understood" % rows[index][2])
    return value


def load_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        return load(handle.read())
