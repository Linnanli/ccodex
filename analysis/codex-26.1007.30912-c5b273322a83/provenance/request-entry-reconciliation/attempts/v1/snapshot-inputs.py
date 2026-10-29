"""Snapshot already saved JSON/JSONL facts only. No original target source access."""
from pathlib import Path
import hashlib, json

ROOT=Path('/Users/nallylin/Documents/code/ccodex')
OUT=ROOT/'.analysis-local/request-entry-reconciliation-work'
BASE='analysis/codex-26.1007.30912-c5b273322a83'
receipts=[]
def snapshot(relative, expected=None, expected_bytes=None, role='existing-analysis-artifact'):
    origin=ROOT/relative
    assert origin.suffix in ['.json','.jsonl','.md'], str(origin)
    raw=origin.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
    if expected is not None: assert digest==expected, 'Hash mismatch: '+relative
    if expected_bytes is not None: assert len(raw)==expected_bytes, 'Bytes mismatch: '+relative
    existing=next((x for x in receipts if x['originPath']==str(origin)),None)
    if existing: return existing,raw
    target=OUT/'inputs'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    receipt={'originPath':str(origin),'originRelativePath':relative,'snapshotPath':str(target),'bytes':len(raw),'sha256':digest,
             'expectedSha256':expected,'expectedBytes':expected_bytes,'pinStatus':'matched' if expected else 'new-exact-input-receipt',
             'kind':role,'originalTargetSourceRead':False}
    receipts.append(receipt);return receipt,raw

manifest,raw=snapshot('.analysis-local/entry-ledger-work/frozen-manifest.json','8893c6fe30d23e2261511b51e11544efd82b841d09f7a31090fb8bd4d0eb2e39',1615)
frozen=json.loads(raw);pin={x['path']:x for x in frozen['files']}
for path in ['.analysis-local/entry-ledger-work/functional-entry-ledger.json','.analysis-local/entry-ledger-work/validation.json',
             '.analysis-local/entry-ledger-work/summary.json','.analysis-local/entry-ledger-work/summary.md','.analysis-local/entry-ledger-work/reviewed-links.json']:
    x=pin[path];snapshot(path,x['sha256'],x['bytes'])
_,raw=snapshot(BASE+'/functional-entry-ledger.json',pin['.analysis-local/entry-ledger-work/functional-entry-ledger.json']['sha256'],22973530)
ledger=json.loads(raw)
snapshot(BASE+'/functional-entry-reviewed-links.json',pin['.analysis-local/entry-ledger-work/reviewed-links.json']['sha256'],25848)
_,raw=snapshot(BASE+'/request-wrapper-contracts.json','8b787ffcec396a73bb2d540d644a7aa6b2c03840d90be45c91c0a3053c5fdad9',585390)
wrapper=json.loads(raw)
snapshot('.analysis-local/review-work/request-wrapper-contracts.json','8b787ffcec396a73bb2d540d644a7aa6b2c03840d90be45c91c0a3053c5fdad9',585390)
snapshot(BASE+'/request-wrapper-evidence.jsonl',wrapper['evidence']['sha256'],1411812)
snapshot('.analysis-local/review-work/request-wrapper-evidence.jsonl',wrapper['evidence']['sha256'],1411812)
snapshot(BASE+'/request-wrapper-summary.md')
history=ROOT/'.analysis-local/completion-audit-work/inputs/request-wrapper-contracts.json'
if history.exists(): snapshot(str(history.relative_to(ROOT)),role='historical-completion-audit-input')
for x in ledger['sourceArtifacts']:
    snapshot(x['path'],x['sha256'],x['bytes'],role='ledger-source-artifact')
status={'schemaVersion':1,'baselineId':ledger['baselineId'],'status':'saved-artifact-inputs-snapshotted-and-pinned',
        'inputs':receipts,'ledgerSourceArtifactsVerified':len(ledger['sourceArtifacts']),
        'wrapperStandaloneValidation':'not-located; no claim inferred from filename or current publication run',
        'wrapperStandaloneManifest':'not-located; embedded evidence pin and scan counts retained separately',
        'publicationScope':'No claim that any current publication-run artifact set includes request-wrapper-contracts.',
        'targetSourceRead':False,'targetExecuted':False,'cliExecuted':False,'uiUsed':False,'modelInvoked':False,'networkUsed':False}
(OUT/'input-receipts.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':status['status'],'inputCount':len(receipts),'ledgerSourceArtifactsVerified':14,'targetSourceRead':False},ensure_ascii=False))
