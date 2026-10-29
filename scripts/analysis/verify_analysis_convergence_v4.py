"""Independent readback of the existing-artifact convergence publication."""
import copy
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/codex-26.1007.30912-c5b273322a83'
WORK = ROOT / '.analysis-local/analysis-convergence-v4-work'
RAW = OUT / 'raw/analysis-convergence-v4'


def read(p):
    return json.loads(p.read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    audit = read(OUT / 'analysis-stage-decisions-v4.json')
    before = read(WORK / 'state-before.json')
    after = read(OUT / 'analysis-state.json')
    plan = (ROOT / 'docs/reverse-engineering/analysis-plan.md').read_bytes()
    assert digest(plan) == '48dd8b65348efd4a8b5634aac5341c4507c262e7b5c88e8ed9368c88eeb96db4'
    pins = {}

    def check_pins(obj):
        if isinstance(obj, dict):
            if {'path', 'bytes', 'sha256'} <= obj.keys():
                p = OUT / obj['path']
                if not p.is_file():
                    p = ROOT / obj['path']
                data = p.read_bytes()
                assert len(data) == obj['bytes'] and digest(data) == obj['sha256'], p
                pins[str(p)] = obj['sha256']
            for value in obj.values():
                check_pins(value)
        elif isinstance(obj, list):
            for value in obj:
                check_pins(value)

    check_pins(audit)
    criteria = audit['criteria']
    requirements = [r for s in audit['stages'] for r in s['requirements']]
    assert len(criteria) == 9 and len(requirements) == 39
    prior = read(OUT / 'analysis-stage-decisions-v3.json')
    old = read(OUT / 'analysis-stage-decisions-v2.json')
    assert [r['requirement'] for r in criteria] == [r['requirement'] for r in prior['criteria']]
    assert [r['requirement'] for r in requirements] == [r['requirement'] for s in old['stages'] for r in s['requirements']]
    for row in criteria + requirements:
        loc = row['planLocator']; span = loc['byteRange']
        quote = plan[span['start']:span['endExclusive']]
        assert quote.decode() == row['requirement'] and digest(quote) == loc['spanHash']
        assert loc['sourceHash'] == digest(plan)
    assert sum(r['status'].startswith('record') for r in criteria) == 4
    assert Counter(r['status'] for r in requirements) == audit['counts']['requirementStatusCounts']

    dependencies = list(csv.DictReader((OUT / 'dependencies.csv').open()))
    actions = read(OUT / 'dependency-investigation-actions-v1.json')
    check_pins(actions)
    assert len(dependencies) == len(actions['rows']) == 202
    inherited_count = 0
    for source, row in zip(dependencies, actions['rows']):
        assert row['dependencyId'] == source['id'] and row['name'] == source['name']
        for field in ['sourcePath', 'sourceHash', 'version', 'versionBasis', 'recommendedIntegration']:
            assert row[field] == source[field]
        for field in ['locator', 'unresolved', 'evidenceIds']:
            assert row[field] == json.loads(source[field])
        assert row['actions'] and row['investigationExecuted'] is False
        inherited = json.loads(source['investigationActions']) if source['investigationActions'] else []
        if inherited:
            inherited_count += 1
            assert len(inherited) == len(row['actions'])
            for original, current in zip(inherited, row['actions']):
                assert all(current[k] == v for k, v in original.items())
                assert set(current) - set(original) <= {'status'}
        else:
            assert all(a['action'] and a['status'] == 'pending; not executed by consolidation' for a in row['actions'])
    assert inherited_count == 17 and actions['counts']['rowsWithNewExplicitActions'] == 185

    ordering = read(OUT / 'restoration-current-ordering-v1.json')
    check_pins(ordering)
    coverage = read(OUT / 'restoration-coverage-v16.json')
    milestones = read(OUT / 'implementation-milestones-v9.json')
    ledger = read(OUT / 'feature-scope-v25.json')
    scenarios = read(OUT / 'feature-scope-v24-scenarios.json')
    features = {f['featureId'] for f in ledger['features']}
    owners = [f for t in coverage['taskGroups'] for f in t['featureIds']]
    assert len(features) == len(owners) == 373 and set(owners) == features
    assert len(coverage['taskGroups']) == 48
    assert len(scenarios['scenarios']) == 1216 and scenarios['executed'] == 0
    assert all(s.get('executionStatus', s.get('status')) == 'not-executed' for s in scenarios['scenarios'])
    tasks = {t['taskId']: t for t in coverage['taskGroups']}
    old_preparation = {r['id']: r for r in milestones['sourcePreparationGraph']}
    for kind in ['sourcePreparation', 'integration']:
        graph = ordering[kind + 'Graph']; index = {r['id']: r for r in graph}
        assert len(graph) == len(index) == 57
        assert all(set(r['dependsOn']) <= index.keys() for r in graph)
        done = set()
        for level in ordering[kind + 'Levels']:
            assert all(set(index[k]['dependsOn']) <= done for k in level)
            assert not done.intersection(level)
            done.update(level)
        assert done == index.keys()
        assert set(index['W09']['dependsOn']) == set(tasks) | {'W08'}
        for task_id, task in tasks.items():
            expected = task['dependsOn'] if kind == 'integration' else old_preparation[task_id]['dependsOn'] if task_id in old_preparation else ['W01', 'W05', 'W06', 'W07']
            assert index[task_id]['dependsOn'] == expected
        for foundation in milestones[kind + 'Graph']:
            if foundation['id'].startswith('W') and foundation['id'] != 'W09':
                assert index[foundation['id']] == foundation
    assert Counter(f['mode'] for f in ledger['features']) == {'unknown': 372, 'shared': 1}

    required = ['id', 'baselineId', 'claim', 'sourcePath', 'sourceHash', 'locator', 'method', 'confidence', 'verificationStatus']
    for check in audit['selectedJournalSchemaAudit']:
        records = [json.loads(line) for line in (OUT / check['path']).read_text().splitlines() if line.strip()]
        assert len(records) == check['records']
        assert check['missingFields'] == {k: sum(k not in r for r in records) for k in required}
        assert check['nonPlanConfidenceValues'] == Counter(str(r.get('confidence')) for r in records if r.get('confidence') not in ['confirmed', 'inferred', 'unresolved'])
    records = [json.loads(line) for line in (OUT / 'analysis-stage-decisions-v4-evidence.jsonl').read_text().splitlines()]
    assert len(records) == 9 and all(set(required) <= r.keys() and r['confidence'] == 'inferred' for r in records)
    modules = read(OUT / 'modules.json')
    assert len(modules) == 438
    assert audit['moduleInventoryAudit']['missingExplicitFields'] == {k: sum(k not in r for r in modules) for k in ['responsibility', 'exports', 'thirdPartyDependencies']}

    allowed = {'updatedAtUtc', 'stageDecisions', 'analysisRequirementsCurrentAudit', 'dependencyInvestigationActions', 'currentRestorationOrdering', 'pending'}
    assert {k: v for k, v in before.items() if k not in allowed} == {k: v for k, v in after.items() if k not in allowed}
    stage_allowed = {'decisions', 'summary', 'provenance', 'counts', 'nextAction', 'latestConvergence'}
    assert {k: v for k, v in before['stageDecisions'].items() if k not in stage_allowed} == {k: v for k, v in after['stageDecisions'].items() if k not in stage_allowed}
    assert after['fullAnalysisCompleted'] is False and after['status'] == 'in-progress'
    assert audit['fullAnalysisCompleted'] is False and audit['clientImplementationStarted'] is False
    for k, v in audit['counts'].items():
        if k.startswith('new'):
            assert v == 0
    check_pins(after['stageDecisions'])
    for name in ['report.md', 'gaps.md']:
        current = (OUT / name).read_bytes(); original = (RAW / (name + '.before')).read_bytes()
        assert current.endswith(original) and b'analysis-stage-decisions-v4.md' in current[:-len(original)]
    immutable = [OUT / n for n in ['analysis-stage-decisions-v4.json', 'analysis-stage-decisions-v4.md', 'analysis-stage-decisions-v4-evidence.jsonl', 'dependency-investigation-actions-v1.json', 'restoration-current-ordering-v1.json']]
    immutable += [p for p in RAW.rglob('*') if p.is_file()]
    assert all(p.stat().st_mode & 0o222 == 0 for p in immutable)
    receipt = {'result': 'passed', 'distinctPinnedArtifacts': len(pins), 'exactPlanQuotes': 48, 'dependencyRows': 202, 'inheritedActionRows': 17, 'newActionRows': 185, 'currentFeatures': 373, 'taskGroups': 48, 'nodesPerGraph': 57, 'unexecutedSpecifications': 1216, 'unrelatedStatePreserved': True, 'newModelSubmissions': 0, 'fullAnalysisCompleted': False}
    with (WORK / 'independent-readback.json').open('x') as stream:
        stream.write(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
