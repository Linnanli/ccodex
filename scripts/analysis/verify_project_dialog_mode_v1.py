import hashlib
import json
import re
from pathlib import Path

ROOT = Path('/Users/nallylin/Documents/code/ccodex')
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/project-dialog-mode-work'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def check_pin(pin):
    data = (ROOT / pin['path']).read_bytes()
    assert len(data) == pin['bytes'] and sha(data) == pin['sha256'], pin['path']

doc = json.loads((OUT / 'project-dialog-mode-v1.json').read_text())
receipt = json.loads((WORK / 'publication.json').read_text())
for pin in receipt['artifacts'] + doc['inputPins'] + doc['rawArtifacts']:
    check_pin(pin)
assert doc['baselineId'] == BASE and not doc['fullAnalysisCompleted'] and not doc['implementationReady']
source_cache = {}
def check_span(row):
    key = row['sourcePath']
    if key not in source_cache:
        source_cache[key] = (FROZEN / key.removeprefix('app.asar/')).read_bytes()
    data = source_cache[key]
    assert sha(data) == row['sourceHash']
    span = row['byteRange']
    selected = data[span['start']:span['endExclusive']]
    assert sha(selected) == row['spanHash']
    return selected.decode()

units = {u['id']: u for u in doc['sourceUnits']}
assert len(units) == 39
for unit in units.values():
    text = check_span(unit)
    check_pin(unit['sourceArtifact'])
    assert text.encode() == (ROOT / unit['sourceArtifact']['path']).read_bytes()
for alias, canonical in doc['sourceAliases'].items():
    assert canonical in units and alias not in units

for join in doc['namedImportExportJoins']:
    consumer = join['consumer']
    text = check_span(consumer)
    assert re.search(r'(?<![\w$])' + re.escape(consumer['imported']) + r'\s+as\s+' + re.escape(consumer['local']) + r'(?![\w$])', text)
    if 'producer' in join:
        producer = join['producer']
        assert check_span(producer) == producer['local'] + ' as ' + producer['exported']
        assert consumer['imported'] == producer['exported']
        assert consumer['from'].removeprefix('./') == producer['sourcePath'].split('/')[-1]
    else:
        assert 'L as i' in check_span(units[join['producerUnitId']])
        assert consumer['from'] == './local-folders-section-6f4091076c76.js'

evidence = [json.loads(line) for line in (OUT / 'project-dialog-mode-v1-evidence.jsonl').read_text().splitlines()]
assert evidence == doc['facts'] + doc['restorationDecisions'] and len(evidence) == 11
required = {'id','baselineId','claim','sourcePath','sourceHash','locator','method','confidence','verificationStatus'}
for row in evidence:
    assert required <= row.keys() and row['confidence'] in ('confirmed','inferred','unresolved')
    ids = row['locator']['sourceUnitIds']
    refs = [units[doc['sourceAliases'].get(identifier, identifier)] for identifier in ids]
    assert row['sourceHash'] == refs[0]['sourceHash'] and row['sourcePath'] == refs[0]['sourcePath']
    assert row['locator']['byteRange'] == refs[0]['byteRange']
    assert row['locator']['spanHash'] == refs[0]['spanHash']
assert sum(row['confidence'] == 'confirmed' for row in evidence) == 8
assert sum(row['confidence'] == 'inferred' for row in evidence) == 3

check_pin(doc['replay'])
replay = json.loads((ROOT / doc['replay']['path']).read_text())
assert replay['status'] == 'passed' and replay['caseCount'] == len(replay['cases']) == 54
raw_ids = {u['id'] for letter in 'abcdef' for u in json.loads((WORK / f'query-{letter}.json').read_text())['units']}
raw_ids |= {u['id'] for u in json.loads((WORK / 'expressions.json').read_text())['units']}
for case in replay['cases']:
    assert case['status'] == 'passed' and set(case['sourceUnitIds']) <= raw_ids
assert doc['counts']['newModelSubmissions'] == doc['counts']['newClientLaunches'] == doc['counts']['newProductScenarioPasses'] == 0
assert doc['associationDisposition']['consumerBoundarySourceClosed']
assert doc['associationDisposition']['retainedCodexSupportSourceProven']
assert not doc['associationDisposition']['actualUiChainObserved']

result = {'status':'passed','artifactPinsChecked':len(receipt['artifacts'] + doc['inputPins'] + doc['rawArtifacts']),
          'frozenSourceFiles':len(source_cache),'selectedSourceUnits':len(units),'namedImportExportJoins':len(doc['namedImportExportJoins']),
          'nineFieldEvidenceRecords':len(evidence),'isolatedCasesReadBack':54,
          'qualification':'Saved evidence/source identity, selected import/export endpoints and synthetic source receipts only; not product, service, native or build acceptance.'}
(WORK / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
