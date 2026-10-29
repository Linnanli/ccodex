#!/usr/bin/env python3
"""Embed unchanged complete REA Evidence in a trace request without JSON materialization."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--seed-kind', default='channel',
                        choices=['node-id', 'route', 'string', 'api', 'channel', 'module', 'native-export'])
    parser.add_argument('--seed-value', required=True)
    parser.add_argument('--direction', default='both', choices=['outgoing', 'incoming', 'both'])
    args = parser.parse_args()
    if len(args.expected_sha256) != 64 or any(c not in '0123456789abcdef' for c in args.expected_sha256):
        parser.error('expected-sha256 must contain 64 lowercase hexadecimal characters')
    source = args.evidence.resolve(strict=True)
    output = args.output.absolute()
    if output.exists():
        parser.error('output already exists; complete Evidence is never overwritten')
    if not output.parent.is_dir():
        parser.error('output parent directory must exist')
    tail = b',"native_observations":[],"seed":' + json.dumps({
        'kind': args.seed_kind, 'value': args.seed_value,
        'match': 'exact', 'case_sensitive': True,
    }, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    tail += b',"direction":' + json.dumps(args.direction).encode('ascii') + b'}\n'
    source_digest = hashlib.sha256()
    output_digest = hashlib.sha256()
    temporary = None
    byte_count = 0
    try:
        with source.open('rb') as evidence, tempfile.NamedTemporaryFile(
                prefix='.' + output.name + '.', suffix='.tmp', dir=output.parent, delete=False) as request:
            temporary = Path(request.name)
            before = os.fstat(evidence.fileno())
            if not stat.S_ISREG(before.st_mode):
                parser.error('Evidence must be a regular file')
            def write(part):
                request.write(part)
                output_digest.update(part)
            write(b'{"application":')
            for block in iter(lambda: evidence.read(1024 * 1024), b''):
                byte_count += len(block)
                source_digest.update(block)
                write(block)
            after = os.fstat(evidence.fileno())
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
                    after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
                raise RuntimeError('Evidence file changed while reading')
            if byte_count != before.st_size or source_digest.hexdigest() != args.expected_sha256:
                raise RuntimeError('Evidence does not match its recorded complete-output hash')
            write(tail)
            request.flush()
            os.fsync(request.fileno())
        # Hard-link creation fails if a concurrent writer created the output.
        os.link(temporary, output)
        print(json.dumps({'evidence': str(source), 'evidenceSha256': source_digest.hexdigest(),
                          'evidenceBytes': byte_count, 'output': str(output),
                          'outputSha256': output_digest.hexdigest(),
                          'outputBytes': output.stat().st_size,
                          'method': 'Raw complete Evidence bytes embedded unchanged; REA validates JSON and Evidence identity.'}))
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
