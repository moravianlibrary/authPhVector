#!/usr/bin/env python3
"""Převede MediaWiki redirect SQL dump (stdin) na TSV redirect.txt (stdout).
Formát výstupu: page_id<TAB>ns<TAB>'title'
"""
import re
import sys

TUPLE_RE = re.compile(r"\((\d+),(\d+),(\'(?:[^\'\\]|\\.)*\'|NULL)")

try:
    for line in sys.stdin:
        if "INSERT INTO `redirect` VALUES" not in line:
            continue
        for m in TUPLE_RE.finditer(line):
            page_id, ns, title = m.group(1), m.group(2), m.group(3)
            if title != "NULL" and ns == "0":
                print(f"{page_id}\t{ns}\t{title}")
except BrokenPipeError:
    sys.exit(0)
