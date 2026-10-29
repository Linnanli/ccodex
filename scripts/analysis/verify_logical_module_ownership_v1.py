#!/usr/bin/env python3
"""Check saved overlap decisions, task references and unchanged analysis scope."""
import collections
import hashlib
import json
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/logical-module-ownership-v1-work'
sha = lambda b: hashlib.sha256(b).hexdigest()
cache = {}
pins = set()
pointers = set()


def read(path):
    path = Path(path)
    if path not in cache:
        cache[path] = json.loads(path.read_text())
    return cache[path]


def locate(v, ptr):
    if ptr:
        assert ptr.startswith('/')
        for t in ptr[1:].split('/'):
            k = t.replace('~1', '/').replace('~0', '~')
            v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def check_ref(r):
    p = ROOT / r['path']
    b = p.read_bytes()
    assert len(b) == r['bytes'] and sha(b) == r['sha256'], p
    pins.add((r['path'], r['sha256']))
    if 'jsonPointer' in r:
        locate(read(p), r['jsonPointer'])
        pointers.add((r['path'], r['jsonPointer']))


def visit(v):
    if isinstance(v, dict):
        if {'path', 'bytes', 'sha256'} <= v.keys():
            check_ref(v)
        for x in v.values():
            visit(x)
    elif isinstance(v, list):
        for x in v:
            visit(x)


publication = read(WORK / 'publication.json')
visit(publication)
doc = read(ROOT / publication['decisions']['path'])
visit(doc)
catalog = read(OUT / 'logical-module-inventory-v1.json')
assert doc['baselineId'] == BASE
assert doc['fullAnalysisCompleted'] is False and doc['implementationReady'] is False
assign = doc['proposalAssignments']
owners = {o['ownerId']: o for o in doc['responsibilityOwners']}
proposals = {r['id']: r for r in catalog['records']}
assert len(assign) == len(proposals) == 38 and len(owners) == 37
assert {a['proposalId'] for a in assign} == proposals.keys()
assert {a['ownerId'] for a in assign} == owners.keys()
for a in assign:
    assert a['proposalId'] in owners[a['ownerId']]['memberProposalIds']
    assert a['fullOriginalModuleRecovered'] is False and a['confidence'] == 'inferred'
nontrivial = [a for a in assign if a['proposalId'] != a['ownerId']]
assert len(nontrivial) == 1
alias = nontrivial[0]
assert alias['proposalId'] == 'LM-BOUNDARY-STRUCT-RWC-SELECTOR'
assert alias['ownerId'] == 'LM-PROVIDER-host-rpc-selector'
left = proposals[alias['proposalId']]['sourceRanges']
right = proposals[alias['ownerId']]['sourceRanges']
assert any(a['sourcePath'] == b['sourcePath'] and a['sourceHash'] == b['sourceHash'] and
           a['byteRange'] == b['byteRange'] == {'start': 2181016, 'endExclusive': 2181910}
           for a in left for b in right), 'KI unification lacks exact source unit identity'

original_overlaps = catalog['sourceOverlapReviews']
decisions = doc['overlapDecisions']
assert len(decisions) == 19
for n, d in enumerate(decisions):
    o = original_overlaps[n]
    assert (d['left'], d['right'], d['sharedRanges']) == (o['left'], o['right'], o['sharedRanges'])
    assert d['overlap']['jsonPointer'] == f'/sourceOverlapReviews/{n}'
    assert d['confidence'] == 'inferred'
    assert d['completeSourcePartitionProven'] is False and d['runtimeEquivalenceClaimed'] is False
    owner_ids = ([d['implementationOwner']] if 'implementationOwner' in d else
                 list(d['implementationOwnersByResponsibility'].values()))
    assert all(id in owners for id in owner_ids)
kind_counts = collections.Counter(d['kind'] for d in decisions)
assert dict(kind_counts) == {'delegate-shared-helper': 3, 'unify-same-contract-proposals': 1,
                             'adapter-uses-resolver': 1, 'composition-or-import-witness': 11,
                             'separate-policy-provider-and-renderer': 3}
assert doc['counts']['overlapDecisionKinds'] == kind_counts
registry_owner = 'LM-PROVIDER-domain-host-registry'
assert all(d['implementationOwner'] == registry_owner for d in decisions if d['kind'] == 'delegate-shared-helper')

coverage = read(OUT / 'restoration-coverage-v17.json')
feature_ledger = read(OUT / 'feature-scope-v26.json')
feature_to_task = {f['featureId']: f['taskId'] for f in coverage['features']}
task_ids = {t['taskId'] for t in coverage['taskGroups']}
graph = read(OUT / 'restoration-current-ordering-v1.json')
foundation_ids = {n['id'] for n in graph['sourcePreparationGraph'] if n['id'].startswith('W')}
assert len(task_ids) == 48 and len(coverage['features']) == len(feature_ledger['features']) == 373
assert len(graph['sourcePreparationGraph']) == len(graph['integrationGraph']) == 57
joined_owners = 0
for id, o in owners.items():
    assert o['primaryFoundationTask']['taskId'] in foundation_ids
    assert o['consumerJoinGap'] and o['allConsumersAssigned'] is False
    assert o['runtimeValidated'] is False and o['clientImplementationGenerated'] is False
    assert o['sourceMode'] == 'unknown' and o['disposition'] == 'retain'
    assert o['proposedPaths'] and all(not p.startswith('src/') for p in o['proposedPaths'])
    if o['consumerTaskJoins']:
        joined_owners += 1
    for j in o['consumerTaskJoins']:
        assert j['taskId'] in task_ids
        assert j['actualUiReceiverIdentityProven'] is False and j['completeChainProven'] is False
        assert j['modeAssignmentChanged'] is False and j['runtimeAcceptanceChanged'] is False
        for f in j['featureIds']:
            assert feature_to_task[f] == j['taskId']
fetch = owners['LM-BOUNDARY-STRUCT-RWC-FETCH']
assert fetch['proposedPaths'] == ['packages/desktop-http-client/src/desktop-fetch.ts']
assert owners['LM-APPHOST-AH-M06']['proposedPaths'] == ['apps/desktop/src/main/http/desktop-fetch.ts']
project = owners['LM-BOUNDARY-STRUCT-RWC-PROJECTS']
assert len(project['proposedPaths']) == 3
candidate = project['candidateConsumerJoin']
assert candidate['status'] == 'pending-source-qualified-delegation-identity'
assert candidate['featureId'] == 'FSC-0105' and feature_to_task['FSC-0105'] == candidate['taskId'] == 'T14'
assert candidate['notAddedAsNewFeature'] is True
assert candidate['relatedRemoteGoal']['featureId'] == 'FSC-0045'
assert feature_to_task['FSC-0045'] == 'T05'

# Check the limited positive import/call evidence for the pending local-project join.
saved = read(OUT / 'raw/restoration-plan-v7/local-content-01/source-contracts.json')
im = saved['imports'][2]
assert im['module'] == './app-initial-6350d04672d0.js'
assert {'local': 'Ke', 'imported': 'j$t'} in im['specifiers']
assert {'local': 'qe', 'imported': 'k$t'} in im['specifiers']
call = saved['calls'][27]
assert call['callee'] == 'Ke' and call['arguments'] == ['r']
assert call['sourcePath'] == im['sourcePath'] and call['sourceHash'] == im['sourceHash']
assert call['binding']['scopeKind'] == 'Program'
assert saved['targetCodeExecuted'] is False
assert 'Ke(scope)' in read(OUT / 'settings-operation-batch-04.json')['operationContracts'][1]['effect']

counts = doc['counts']
assert counts['ownersWithConditionalFeatureTaskJoins'] == joined_owners == 7
for k, v in counts.items():
    if k.startswith('new'):
        assert v == 0
ev = [json.loads(l) for l in (ROOT / publication['evidence']['path']).read_text().splitlines()]
assert len(ev) == 57 and len({e['id'] for e in ev}) == 57
for e in ev:
    assert {'id', 'baselineId', 'claim', 'sourcePath', 'sourceHash', 'locator', 'method', 'confidence', 'verificationStatus'} <= e.keys()
    assert e['baselineId'] == BASE and e['confidence'] == 'inferred'
    assert sha((ROOT / e['sourcePath']).read_bytes()) == e['sourceHash']
    locate(read(ROOT / e['sourcePath']), e['locator']['jsonPointer'])
for k in ['decisions', 'summary', 'evidence']:
    assert stat.S_IMODE((ROOT / publication[k]['path']).stat().st_mode) == 0o444

before = read(WORK / 'state-before.json')
after = read(OUT / 'analysis-state.json')
assert after['logicalModuleInventory']['ownershipReview']['decisions'] == publication['decisions']
assert after['stageDecisions']['nextAction'] == doc['nextAction']
comparison = json.loads(json.dumps(after))
del comparison['logicalModuleInventory']['ownershipReview']
comparison['stageDecisions']['nextAction'] = before['stageDecisions']['nextAction']
comparison['updatedAtUtc'] = before['updatedAtUtc']
assert comparison == before
assert after['fullAnalysisCompleted'] is False and after['status'] == 'in-progress'
assert after['latestBehaviorAuthorizationState']['groupRemaining'] == 0
for name in ['report.md', 'gaps.md']:
    previous = (WORK / ('before-' + name)).read_bytes()
    current = (OUT / name).read_bytes()
    assert current.endswith(previous) and len(current) > len(previous)
receipt = {'status': 'passed', 'baselineId': BASE, 'distinctPinnedFiles': len(pins),
           'distinctJsonPointers': len(pointers), 'proposalAssignments': 38,
           'responsibilityOwners': 37, 'sameSourceKIUnificationChecked': True,
           'overlapDecisionsChecked': 19, 'sourceLevelConditionalFeatureOwnerJoins': joined_owners,
           'localProjectImportCallIdentityChecked': True, 'localProjectFullDelegateJoinStillPending': True,
           'currentFeaturesUnchanged': 373, 'currentFeatureTasksUnchanged': 48,
           'unrelatedStateAndAuthorizationPreserved': True, 'historicalReportsPreserved': True,
           'fullAnalysisCompleted': False,
           'scope': 'Saved-artifact identity, decision coverage, source-qualified metadata links and accounting; no source execution/runtime or product acceptance.'}
(WORK / 'independent-readback.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(receipt, ensure_ascii=False))
