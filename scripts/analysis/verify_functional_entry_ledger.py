#!/usr/bin/env python3
"""Independently verify a ledger against its frozen JSON/JSONL inputs only."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def resolve(doc, pointer):
    for segment in pointer.split('/')[1:]:
        key = segment.replace('~1', '/').replace('~0', '~')
        doc = doc[int(key)] if isinstance(doc, list) else doc[key]
    return doc


def nodes(value):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from nodes(child)


def verify(root, ledger_path):
    ledger_bytes = ledger_path.read_bytes()
    doc = json.loads(ledger_bytes)
    artifacts, inputs = {}, {}
    for artifact in doc['sourceArtifacts']:
        raw = (root / artifact['path']).read_bytes()
        assert sha(raw) == artifact['sha256'], artifact['path']
        assert len(raw) == artifact['bytes']
        if artifact['format'] == 'jsonl':
            assert all(line.strip() for line in raw.splitlines())
            value = [json.loads(line) for line in raw.splitlines()]
        else:
            value = json.loads(raw)
        artifacts[artifact['artifactId']] = artifact
        inputs[artifact['artifactId']] = value
    baseline = inputs['baseline']['baselineId']
    assert baseline == doc['baselineId'] == inputs['manifest']['baselineId']
    source_files = {f['sourcePath']: f for f in inputs['manifest']['archiveFiles']}
    evidence = {}
    for artifact in doc['sourceArtifacts']:
        if artifact['format'] != 'jsonl':
            continue
        for index, record in enumerate(inputs[artifact['artifactId']]):
            assert record['id'] not in evidence
            evidence[record['id']] = (artifact['artifactId'], index, record)
    entry_ids = [e['entryId'] for e in doc['entries']]
    support_ids = [n['nodeId'] for n in doc['supportNodes']]
    deferred_ids = [e['candidateId'] for e in doc['deferredCandidates']]
    assert len(set(entry_ids)) == len(entry_ids)
    assert len(set(support_ids)) == len(support_ids)
    assert len(set(deferred_ids)) == len(deferred_ids)
    assert not set(entry_ids).intersection(support_ids)
    all_ids = set(entry_ids + support_ids)
    pointer_occurrences = reference_occurrences = coordinates = 0
    referenced_ids = set()
    for value in nodes(doc):
        if not isinstance(value, dict):
            continue
        if 'artifactId' in value and 'jsonPointer' in value:
            artifact = artifacts[value['artifactId']]
            resolve(inputs[value['artifactId']], value['jsonPointer'])
            if 'sha256' in value:
                assert value['sha256'] == artifact['sha256']
                assert value['path'] == artifact['path']
            pointer_occurrences += 1
        for key in ['evidenceId', 'primaryEvidenceId']:
            if key in value:
                assert value[key] in evidence
                referenced_ids.add(value[key])
                reference_occurrences += 1
        if 'evidenceIds' in value or 'conditionEvidenceIds' in value:
            for key in ['evidenceIds', 'conditionEvidenceIds']:
                for evidence_id in value.get(key, []):
                    assert evidence_id in evidence
                    referenced_ids.add(evidence_id)
                    reference_occurrences += 1
        if 'sourcePath' in value and 'sourceHash' in value and 'byteRange' in value:
            source = source_files[value['sourcePath']]
            assert value['sourceHash'] == source['sha256']
            span = value['byteRange']
            assert span['kind'] == 'byte-range'
            assert 0 <= span['start'] <= span['endExclusive'] <= source['bytes']
            if 'evidenceId' in value:
                original = evidence[value['evidenceId']][2]
                assert original['sourcePath'] == value['sourcePath']
                assert original['sourceHash'] == value['sourceHash']
                assert original['locator'] == span
                assert original.get('spanHash') == value.get('spanHash')
            coordinates += 1
    catalog_ids = [e['evidenceId'] for e in doc['evidenceReferences']]
    assert len(catalog_ids) == len(set(catalog_ids))
    assert referenced_ids == set(catalog_ids)
    for e in doc['evidenceReferences']:
        artifact, index, original = evidence[e['evidenceId']]
        journal = e['evidenceJournal']
        assert artifact == journal['artifactId']
        assert index + 1 == journal['line']
        assert journal['sha256'] == artifacts[artifact]['sha256']
        assert journal['path'] == artifacts[artifact]['path']
        assert original['baselineId'] == baseline
        assert original['method'] == e['method']
        assert original['confidence'] == e['confidence']
        assert original['verificationStatus'] == e['verificationStatus']
    links = doc['reviewedContractLinks']
    assert len({l['linkId'] for l in links}) == len(links)
    incident, handler_incident = defaultdict(set), defaultdict(set)
    for link in links:
        assert link['from'] in all_ids and link['to'] in all_ids
        assert link['operationEquivalence'] is False
        assert link['featureMergeAuthorized'] is False
        assert link['runtimeReachability'] == 'unknown'
        for endpoint in [link['from'], link['to']]:
            incident[endpoint].add(link['linkId'])
            if link['handlerIdentity']:
                handler_incident[endpoint].add(link['linkId'])
    for entry in doc['entries']:
        assert set(entry['reviewedContractLinkIds']) == incident[entry['entryId']]
        assert set(entry['reviewedHandlerIdentityLinkIds']) == handler_incident[entry['entryId']]
        assert entry['featureId'] is None and entry['mode'] == 'unknown'
        source = entry['sourceArtifact']
        original = resolve(inputs[source['artifactId']], source['jsonPointer'])
        if source['artifactId'] == 'menu':
            assert original['contractId'] == entry['entryId']
    counts = Counter(e['denominatorGroup'] for e in doc['entries'])
    primary_groups = {d['groupId'] for d in doc['denominators'] if d['role'] == 'primary-entry'}
    primary = [e for e in doc['entries'] if e['denominatorGroup'] in primary_groups]
    for denominator in doc['denominators']:
        if denominator['role'] in ['primary-entry', 'auxiliary-entry']:
            assert counts[denominator['groupId']] == denominator['recordCount']
    s = doc['summary']
    assert s['entryRecords'] == len(entry_ids) == 968
    assert s['primaryEntryRecords'] == len(primary) == 868
    assert s['auxiliaryEntryRecords'] == len(entry_ids) - len(primary) == 100
    assert s['supportNodes'] == len(support_ids) == 176
    assert s['deferredCandidateRecords'] == len(deferred_ids) == 337
    assert s['byDenominator'] == dict(counts)
    for group, count in counts.items():
        coverage = s['associationByDenominator'][group]
        group_entries = [e for e in doc['entries'] if e['denominatorGroup'] == group]
        assert coverage['recordCount'] == count
        assert coverage['withReviewedContractLinks'] == sum(bool(incident[e['entryId']]) for e in group_entries)
        assert coverage['withoutReviewedContractLinks'] == sum(not incident[e['entryId']] for e in group_entries)
        assert coverage['withReviewedHandlerIdentityLinks'] == sum(bool(handler_incident[e['entryId']]) for e in group_entries)
        assert coverage['withReviewedOperationEquivalenceLinks'] == coverage['mappedToConfirmedFeature'] == 0
    assert s['reviewedLinks'] == len(links) == 1088
    assert s['linksByRelation'] == dict(Counter(l['relation'] for l in links))
    assert s['entriesWithReviewedContractLinks'] == sum(bool(incident[e]) for e in entry_ids)
    assert s['entriesWithoutReviewedContractLinks'] == sum(not incident[e] for e in entry_ids)
    assert s['primaryEntriesWithReviewedContractLinks'] == sum(bool(incident[e['entryId']]) for e in primary)
    assert s['primaryEntriesWithoutReviewedContractLinks'] == sum(not incident[e['entryId']] for e in primary)
    assert s['entriesWithReviewedHandlerIdentityLinks'] == sum(bool(handler_incident[e]) for e in entry_ids)
    assert s['entriesWithReviewedOperationEquivalenceLinks'] == s['entriesMappedToConfirmedFeature'] == 0
    assert s['featureCensusDenominator'] == 'unknown'
    assert s['ledgerEvidenceReferences'] == len(catalog_ids)
    assert s['sourceArtifactCount'] == len(artifacts)
    return {'status': 'passed', 'baselineId': baseline,
        'ledgerSha256': sha(ledger_bytes), 'ledgerBytes': len(ledger_bytes),
        'inputArtifactsHashVerified': len(artifacts), 'jsonPointerOccurrencesVerified': pointer_occurrences,
        'evidenceReferenceOccurrencesVerified': reference_occurrences,
        'uniqueExistingEvidenceReferences': len(catalog_ids),
        'sourceCoordinateOccurrencesVerifiedAgainstFrozenJournalsAndManifest': coordinates,
        'entryRecords': len(entry_ids), 'reviewedContractLinks': len(links),
        'modeAndFeatureAssignmentsRemainUnknown': True,
        'targetCodeReadParsedExecuted': False,
        'spanBytesRehashed': False,
        'scope': 'Artifact hashes, JSON pointers, original evidence references/coordinates, link endpoints, denominator/association counts; original target-code/runtime scope is unchanged.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--ledger', type=Path, default=Path('.analysis-local/entry-ledger-work/functional-entry-ledger.json'))
    parser.add_argument('--output', type=Path, default=Path('.analysis-local/entry-ledger-work/validation.json'))
    args = parser.parse_args()
    root = args.root.resolve()
    result = verify(root, args.ledger if args.ledger.is_absolute() else root / args.ledger)
    output = args.output if args.output.is_absolute() else root / args.output
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
