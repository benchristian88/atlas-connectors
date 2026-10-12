# SPDX-License-Identifier: Apache-2.0
"""Provision reviewed collection bytes for tests; never part of a Connector."""
import argparse
import hashlib
import io
from pathlib import Path
import tarfile

DIGEST = '77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6'


def install(archive, output):
    raw=archive.read_bytes()
    if len(raw)>16*1024*1024 or hashlib.sha256(raw).hexdigest()!=DIGEST:
        raise ValueError('unreviewed_test_collection')
    destination=output/'ansible_collections/community/proxmox'
    destination.mkdir(parents=True,exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as contents:
        for member in contents:
            if member.isdir(): continue
            name=Path(member.name)
            if name.is_absolute() or '..' in name.parts: raise ValueError('unsafe_test_collection')
            source=contents.extractfile(member)
            if source is None: raise ValueError('invalid_test_collection')
            path=destination/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(source.read())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    install(args.archive,args.output)
