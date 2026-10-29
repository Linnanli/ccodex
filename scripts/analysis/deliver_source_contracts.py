"""Publish explicitly pinned metadata from completed bounded source reviews.

The owned publication plan supplies the finite allowlist and reader qualifications.
Target source, ASTs, and native binaries never enter this delivery.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE
LOCAL = ROOT / '.analysis-local'
FORBIDDEN_KEYS = {'sourceTextLocalOnly', 'sourceText', 'sourceCode', 'codeText',
                  'fullAst', 'fullAST', 'ast', 'rawAst'}


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def metadata_only(value):
    if isinstance(value, dict):
        assert not FORBIDDEN_KEYS.intersection(value), 'Implementation/AST field in allowlist'
        for item in value.values():
            metadata_only(item)
    elif isinstance(value, list):
        for item in value:
            metadata_only(item)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('plan', type=Path)
    args = parser.parse_args()
    plan_path = args.plan.resolve()
    assert plan_path.is_relative_to(LOCAL) and not args.plan.is_symlink()
    plan_bytes = plan_path.read_bytes()
    plan = json.loads(plan_bytes)
    assert plan['baselineId'] == BASELINE
    payloads, indices = {}, []
    for group in plan['groups']:
        slug = group['slug']
        assert slug and all(c.islower() or c.isdigit() or c == '-' for c in slug)
        prefix = 'raw/' + slug + '/'
        copies = []
        for item in group['copies']:
            source = (ROOT / item['source']).resolve()
            assert source.is_relative_to(LOCAL) and source.is_file()
            assert not (ROOT / item['source']).is_symlink()
            assert source.stat().st_mode & 0o222 == 0
            raw = source.read_bytes()
            assert pin(raw) == {key: item[key] for key in ['bytes', 'sha256']}
            assert source.suffix in {'.json', '.jsonl', '.md', '.txt', '.py', '.mjs'}
            assert item['kind'] in {'metadata', 'owned-tool', 'actual-stdio'}
            if item['kind'] == 'metadata' and source.suffix in {'.json', '.jsonl'}:
                values = [json.loads(raw)] if source.suffix == '.json' else [
                    json.loads(line) for line in raw.splitlines() if line.strip()]
                for value in values:
                    metadata_only(value)
            elif item['kind'] == 'owned-tool':
                assert 'local-source' not in source.parts
                assert source.suffix in {'.py', '.mjs'}
            elif item['kind'] == 'actual-stdio':
                assert source.suffix == '.txt'
            relative = prefix + item['destination']
            assert relative not in payloads
            payloads[relative] = raw
            copies.append({'original': str(source), 'outputPath': relative,
                           'kind': item['kind'], **pin(raw)})
        by_destination = {item['outputPath']: item for item in copies}
        core_path = prefix + group['core']
        assert core_path in by_destination
        core = json.loads(payloads[core_path])
        assert core['baselineId'] == BASELINE
        journal_path = prefix + group['journal']
        assert journal_path in by_destination
        journal = [json.loads(line) for line in payloads[journal_path].splitlines() if line.strip()]
        assert len(journal) == group['recordCount']
        assert len({row['id'] for row in journal}) == len(journal)
        review_paths = [prefix + name for name in group['reviews']]
        assert review_paths and all(name in by_destination for name in review_paths)
        supplement_paths = [prefix + name for name in group.get('supplements', [])]
        assert all(name in by_destination for name in supplement_paths)
        reader = {
            'schemaVersion': 'reviewed-source-contract-reader/1', 'baselineId': BASELINE,
            'scope': group['scope'],
            'authorSnapshot': {'path': core_path, **pin(payloads[core_path]),
                               'statusPreserved': core.get('status')},
            'evidenceJournal': {'path': journal_path, **pin(payloads[journal_path]),
                                'recordCount': len(journal)},
            'independentReviews': [{'path': name, **pin(payloads[name])} for name in review_paths],
            'readerQualifications': group['readerQualifications'],
            'counts': group['counts'], 'globalRecordsAdded': 0,
            'runtimeRunsAdded': 0, 'additionalModelTasks': 0,
            'confirmedChatGptExclusionsAdded': 0, 'fullAnalysisCompleted': False,
            'thirdPartyImplementationsPublished': False,
        }
        if supplement_paths:
            reader['authorQualifications'] = [
                {'path': name, **pin(payloads[name]), 'addsEvidenceRecords': False}
                for name in supplement_paths]
        metadata_only(reader)
        reader_name = slug + '.json'
        summary_name = slug + '-summary.md'
        payloads[reader_name] = encode(reader)
        payloads[summary_name] = group['summary'].encode()
        index = {'schemaVersion': 1, 'baselineId': BASELINE,
                 'kind': 'bounded-source-contract-metadata-delivery',
                 'scope': group['scope'], 'exactCopies': copies,
                 'derived': [{'path': name, **pin(payloads[name])}
                             for name in [reader_name, summary_name]],
                 'publicationPlan': {'localPath': str(plan_path), **pin(plan_bytes)},
                 'globalRecordsAdded': 0, 'runtimeRunsAdded': 0,
                 'additionalModelTasks': 0, 'confirmedChatGptExclusionsAdded': 0,
                 'originalSourceReadOrExecuted': False, 'fullAnalysisCompleted': False,
                 'thirdPartyImplementationsPublished': False}
        index_name = slug + '-provenance.json'
        payloads[index_name] = encode(index)
        indices.append({'path': index_name, **pin(payloads[index_name])})

    # Check input pins, containment, existing bytes and current parent permissions.
    for relative, raw in payloads.items():
        target = OUT / relative
        assert target.resolve().is_relative_to(OUT.resolve()) and not target.is_symlink()
        assert not target.exists() or (target.is_file() and target.read_bytes() == raw)
        existing_parent = target.parent
        while not existing_parent.exists():
            existing_parent = existing_parent.parent
        assert existing_parent.is_dir() and os.access(existing_parent, os.W_OK | os.X_OK)
    for relative, raw in payloads.items():
        target = OUT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(raw)
        target.chmod(0o444)
        assert target.read_bytes() == raw
    print(json.dumps({'status': 'delivered', 'groups': len(indices), 'outputs': len(payloads),
                      'indices': indices, 'globalRecordsAdded': 0, 'runtimeRunsAdded': 0,
                      'thirdPartyImplementationsPublished': False,
                      'reportOrStateModified': False, 'fullAnalysisCompleted': False}))


if __name__ == '__main__':
    main()
