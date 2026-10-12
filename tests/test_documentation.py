# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import re
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]


def test_repository_markdown_links_whitespace_and_fences():
    paths=[ROOT/'README.md',*ROOT.glob('connectors/**/*.md')]
    for path in paths:
        raw=path.read_bytes()
        assert raw.endswith(b'\n') and not raw.endswith(b'\n\n'),path
        assert all(not line.endswith((b' ',b'\t')) for line in raw.splitlines()),path
        text=raw.decode()
        assert sum(bool(re.match(r'^\s*```',line)) for line in text.splitlines())%2==0,path
        for target in re.findall(r'\[[^\]\n]*\]\(([^\s)]+)\)',text):
            target=unquote(target.split('#',1)[0])
            if target and ':' not in target and not target.startswith('/'):
                assert (path.parent/target).exists(),(path,target)
