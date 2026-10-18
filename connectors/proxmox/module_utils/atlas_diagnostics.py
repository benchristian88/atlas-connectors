# SPDX-License-Identifier: Apache-2.0
"""Discovery diagnostics v1. No source values, messages, URLs or config blobs.

The fixed playbook receives a runtime-owned, precreated sidecar alongside its
private input. This module never creates a destination or accepts one in config.
"""
import json
import os
from pathlib import Path
import re
import stat

MAX_EVENTS = 8192
MAX_EVENT_BYTES = 768
NORMAL = {'stage', 'result', 'reason_code', 'object_class', 'external_id', 'parent_external_id', 'source_category', 'record_count'}
DEBUG = {'field', 'encountered_type', 'validation_rule', 'expected', 'action'}
TOKEN = re.compile(r'[a-z][a-z0-9_.-]{0,63}')
IDENTITY = re.compile(r'[A-Za-z0-9][A-Za-z0-9_./:-]{0,191}')


def value_type(value):
    return {type(None): 'null', bool: 'boolean', int: 'integer', float: 'number',
            str: 'string', list: 'array', dict: 'object'}.get(type(value), 'unknown')


class Diagnostics:
    def __init__(self, *, debug=False, sensitive=(), descriptor=None):
        self.debug, self.descriptor = debug is True, descriptor
        self.sensitive = tuple(value for value in sensitive if isinstance(value, str) and value)
        self.events = []
        self.context = {'stage': 'discovery'}
        self.detail = {}

    @classmethod
    def open(cls, path, input_file, *, debug=False, sensitive=()):
        if not path:
            return cls(debug=debug, sensitive=sensitive)  # Older runtimes/unit fixtures.
        destination, source = Path(path), Path(input_file)
        parent = destination.parent
        if (destination.name != 'diagnostics.ndjson' or not destination.is_absolute()
                or parent != source.parent or parent.is_symlink()
                or parent.stat().st_uid != os.getuid() or parent.stat().st_mode & 0o077):
            raise ValueError('diagnostic_destination_invalid')
        descriptor = os.open(destination, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK)
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid()
                or info.st_mode & 0o077 or info.st_size):
            os.close(descriptor)
            raise ValueError('diagnostic_destination_invalid')
        return cls(debug=debug, sensitive=sensitive, descriptor=descriptor)

    def at(self, stage, **context):
        self.context, self.detail = {'stage': stage, **context}, {}

    def rule(self, field, value, rule, expected):
        # Type only: never retain the offending value, even transiently in detail.
        self.detail = {'field': field, 'encountered_type': value_type(value),
                       'validation_rule': rule, 'expected': expected}

    def emit(self, result, reason, *, record_count=0, **context):
        if len(self.events) >= MAX_EVENTS:
            return
        row = {'sequence': len(self.events) + 1, **self.context, 'result': result,
               'reason_code': reason, 'record_count': record_count, **context}
        row.update(self.detail)
        # All metadata is from explicit call sites. Drop unsafe optional identity;
        # never substitute source error text or serialize an arbitrary value.
        safe = {}
        for key, value in row.items():
            if key in {'sequence', 'record_count'}:
                safe[key] = value
            elif key in NORMAL | DEBUG:
                pattern = IDENTITY if key in {'external_id', 'parent_external_id'} else TOKEN
                if (isinstance(value, str) and pattern.fullmatch(value)
                        and not any(secret in value for secret in self.sensitive)
                        and 'Authorization' not in value and not re.search(r'password|bearer|private.key|api.token|token.secret|eyJ', value, re.I)):
                    safe[key] = value
        if len(self.events) == MAX_EVENTS - 1:
            safe = {'sequence': MAX_EVENTS, 'stage': 'diagnostics', 'result': 'error', 'reason_code': 'diagnostic_limit'}
        raw = json.dumps(safe, separators=(',', ':'), sort_keys=True, allow_nan=False).encode() + b'\n'
        if len(raw) > MAX_EVENT_BYTES:
            safe = {'sequence': row['sequence'], 'stage': 'diagnostics', 'result': 'error', 'reason_code': 'diagnostic_limit'}
            raw = json.dumps(safe, separators=(',', ':')).encode() + b'\n'
        if not self.debug:
            safe = {key: value for key, value in safe.items() if key not in DEBUG}
            raw = json.dumps(safe, separators=(',', ':'), sort_keys=True, allow_nan=False).encode() + b'\n'
        self.events.append(safe)
        if self.descriptor is not None:
            # Unbuffered append: evidence exists before a later exception/kill.
            view = memoryview(raw)
            while view:
                written = os.write(self.descriptor, view)
                if written <= 0:
                    raise OSError('diagnostic_write_failed')
                view = view[written:]

    def close(self):
        if self.descriptor is not None:
            os.close(self.descriptor)
            self.descriptor = None
