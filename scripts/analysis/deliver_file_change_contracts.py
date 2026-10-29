"""Deliver a fixed metadata allowlist; original source/AST is never read.

Delivery has two phases so completed delivery receipts can be archived without
claiming a still-running receipt already exists. Every phase preflights its full
output plan before writing; existing differing bytes are rejected.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

WORKSPACE = Path('/Users/nallylin/Documents/code/ccodex')
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = WORKSPACE / 'analysis' / BASELINE
WORK = WORKSPACE / '.analysis-local/file-change-view-delivery-work'
SCRIPT = WORKSPACE / 'scripts/analysis/deliver_file_change_contracts.py'
RAW = Path('raw/file-change-view-contracts')
ORIGINAL = WORKSPACE / '.analysis-local/file-change-view-contracts-work'
OLD_PEER = WORKSPACE / '.analysis-local/file-change-view-contracts-peer-work'
ERRATA = WORKSPACE / '.analysis-local/file-change-view-errata-work'
EXPECTED = {
    'original/file-change-view-contracts.json': (ORIGINAL, 'file-change-view-contracts.json', 178936, '49ddb254d3341ff1064fb3bb15a49642de4d838417328ffb3a2ff1808a56112a'),
    'original/evidence.jsonl': (ORIGINAL, 'evidence.jsonl', 112044, '3d9d7bfbf7488f4a6af014e8fb1ae602d9168a534f7f7f5987e7d703738e310b'),
    'original/summary.md': (ORIGINAL, 'summary.md', 3039, '3cc0ad6b06a621595abe701640808f1e74e1b92662d59f6a13f59a50dfa45a6f'),
    'original/validation.json': (ORIGINAL, 'validation.json', 7793, '60a9406ba78ade5c80a59ad728a573735fccfd1c084bf6befad19e9824ca26fb'),
    'original/freeze-manifest.json': (ORIGINAL, 'freeze-manifest.json', 58721, 'b3f1534f9fea6f467bc0d77825548b9c38b2d6175433cf315f2856187cab0d84'),
    'original/freeze-confirmation.json': (ORIGINAL, 'freeze-confirmation.json', 1430, 'cbc165f595e547c6768a0457e21cebe18283e340be8730420c6a6ebf8083e0ad'),
    'original/peer-review.json': (OLD_PEER, 'peer-review.json', 44140, '008b8445fed00d1748314382a29823a73621449950631793019920f4701b17f9'),
    'original/peer-review.md': (OLD_PEER, 'peer-review.md', 1158, '76c3187f0e64c6564f8f7922ffdb07e9f5f53880490d778f710a417a50a2d9a0'),
    'errata/file-change-view-contracts-v2.json': (ERRATA, 'file-change-view-contracts-v2.json', 181686, '459e1ab894c85074a7d324780b620d0346aefbd281f4bbf9a441aaf55def5cbc'),
    'errata/evidence.jsonl': (ERRATA, 'evidence.jsonl', 9303, '41a05edd915c4fea5c27caa43eb9d6a6fb50bc512dca071838f0126dc072b9cf'),
    'errata/errata.json': (ERRATA, 'errata.json', 7733, '95d1a2d3ca5cd035254ec62204b9cdf6a58e29a22aa9045500cd3304a6b42d2b'),
    'errata/summary.md': (ERRATA, 'summary.md', 1680, '99b7ba696cabf7bf5da1ee7b813fae92a46bb13993ea0a95d3f98f9734cee7bf'),
    'errata/provenance.json': (ERRATA, 'provenance.json', 5451, '29a63116bc7210d8d2e5ef7435ed14f880d4b3cea3c98b41d475f12681421863'),
    'errata/validation.json': (ERRATA, 'validation.json', 28765, '1ad60fe6400050615d21d9d08c947e9bf104c0dd6e8e284cc0be7d0c5ffa55f4'),
    'errata/independent-review.json': (ERRATA, 'independent-review.json', 27654, '7301931a465ac01980588facd028b520fcf3028233d8335caad0d2b57a014580'),
    'errata/independent-review.md': (ERRATA, 'independent-review.md', 669, 'f26849384e7cc5ef8b00b99d737c1b3070d919eb2b310f2f752b9e032c19340b'),
    'errata/freeze-manifest.json': (ERRATA, 'freeze-manifest.json', 34768, '0818244a3d97a6dc25d59e1b8fb8db934b7dbfe116205f66f67c53fb00749dd0'),
    'errata/freeze-confirmation.json': (ERRATA, 'freeze-confirmation.json', 3796, '8bd3fcd1e6e77cd8f9bb8be6b385da125393614505a4bb1f3463413ca4aa1729'),
}
ALIASES = {
    'file-change-view-contracts-v2.json': 'errata/file-change-view-contracts-v2.json',
    'file-change-view-errata-evidence.jsonl': 'errata/evidence.jsonl',
    'file-change-view-errata.json': 'errata/errata.json',
    'file-change-view-errata-peer-review.json': 'errata/independent-review.json',
}
SUMMARY = 'file-change-view-contracts-summary.md'
PROVENANCE = 'file-change-view-contracts-delivery-provenance.json'
CAPTURES = ['run.py', 'preflight-plan.json', 'delivery-validation.json',
            'diagnostic-observed-source.py', 'diagnostic-observed-output.txt', 'author-diagnostic-disclosure.json'] + [
    f'attempts/{attempt}/{name}' for attempt in ('preflight-01', 'preflight-02', 'deliver-01')
    for name in ('exact-source.py', 'stdout.txt', 'stderr.txt', 'receipt.json')]
checks = 0

def require(condition, message):
    global checks
    checks += 1
    if not condition:
        raise ValueError(message)

def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def file_pin(path):
    return {'path': str(path), **pin(path.read_bytes())}

def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()

def safe(path):
    require(not path.is_symlink() and all(not p.is_symlink() for p in path.parents), 'symlink: ' + str(path))

def preflight(path, raw):
    safe(path)
    require(path.is_relative_to(OUT) or path.is_relative_to(WORK), 'output outside delivery roots')
    require(all(not p.exists() or p.is_dir() for p in path.parents), 'non-directory output parent')
    parent = next(p for p in path.parents if p.exists())
    require(parent.is_dir() and os.access(parent, os.W_OK), 'parent not writable: ' + str(parent))
    require(not path.with_name(path.name + '.file-change-delivery-tmp').exists(), 'stale delivery temporary')
    require(not path.exists() or (path.is_file() and path.read_bytes() == raw), 'existing differing output: ' + str(path))

def write_exact(path, raw):
    if path.exists():
        return 'same-bytes-retained'
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.file-change-delivery-tmp')
    temporary.write_bytes(raw)
    temporary.chmod(0o444)
    temporary.replace(path)
    return 'created'

def pointer(doc, path):
    for segment in path.lstrip('/').split('/'):
        doc = doc[int(segment)] if isinstance(doc, list) else doc[segment]
    return doc

def load_inputs():
    require(OUT.is_dir(), 'fixed formal baseline missing')
    inputs, receipts = {}, []
    for relative, (directory, name, size, digest) in EXPECTED.items():
        p = directory / name
        safe(p)
        require(p.is_file() and p.stat().st_mode & 0o777 == 0o444, 'input not readonly metadata: ' + str(p))
        require(p.suffix in ('.json', '.jsonl', '.md'), 'not allowed metadata')
        raw = p.read_bytes()
        require((len(raw), pin(raw)['sha256']) == (size, digest), 'frozen pin changed: ' + relative)
        inputs[relative] = raw
        receipts.append({'archivePath': (RAW / relative).as_posix(), 'original': {'path': str(p), **pin(raw)}, 'mode': '0o444'})
    return inputs, receipts

def verify_metadata(inputs):
    docs = {name: json.loads(raw) for name, raw in inputs.items() if name.endswith('.json')}
    old = docs['original/file-change-view-contracts.json']
    new = docs['errata/file-change-view-contracts-v2.json']
    delta = docs['errata/errata.json']
    old_peer = docs['original/peer-review.json']
    peer = docs['errata/independent-review.json']
    validation = docs['errata/validation.json']
    manifest = docs['errata/freeze-manifest.json']
    confirm = docs['errata/freeze-confirmation.json']
    require(old['baselineId'] == new['baselineId'] == delta['baselineId'] == peer['baselineId'] == manifest['baselineId'] == BASELINE, 'baseline mismatch')
    require(len(old['contracts']) == len(new['contracts']) == 30, '30-contract denominator changed')
    old_rows = [json.loads(line) for line in inputs['original/evidence.jsonl'].splitlines() if line]
    rows = [json.loads(line) for line in inputs['errata/evidence.jsonl'].splitlines() if line]
    require(len(old_rows) == 30 and len(rows) == 2, 'historical30/fresh2 journal changed')
    required = {'id','baselineId','claim','sourcePath','sourceHash','locator','method','confidence','verificationStatus'}
    for row in rows:
        require(required <= row.keys() and row['confidence'] in ('confirmed','inferred','unresolved'), 'fresh journal schema/confidence')
        require(row['baselineId'] == BASELINE and row['id'] not in row['erratumOf']['evidenceIds'], 'fresh row identity/self-reference')
    require([r['id'] for r in rows] == ['FILE-CHANGE-ERRATA-0001','FILE-CHANGE-ERRATA-0002'], 'fresh2 IDs changed')
    expected = copy.deepcopy(old)
    require(len(delta['changes']) == 3, 'three semantic fields changed')
    require([c['pointer'] for c in delta['changes']] == ['/contracts/11/errorContract','/contracts/17/claim','/contracts/17/errorContract'], 'semantic change scope')
    for change in delta['changes']:
        require(pointer(old, change['pointer']) == change['oldValue'] and pointer(new, change['pointer']) == change['newValue'], 'errata value provenance')
        owner, key = change['pointer'].rsplit('/', 1)
        pointer(expected, owner)[key] = change['newValue']
    for index, row in zip((11,17), rows):
        expected['contracts'][index]['evidenceIds'].append(row['id'])
        require(row['erratumOf']['contractId'] == old['contracts'][index]['contractId'], 'erratum contract identity')
        require(row['erratumOf']['evidenceIds'] == old['contracts'][index]['evidenceIds'], 'old evidence reference changed')
    expected['errataDerivation'] = new['errataDerivation']
    require(expected == new, 'unapproved derivative field changed')
    require(new['originalSourcePins'] == old['originalSourcePins'] and new['denominators'] == old['denominators'], 'inherited original pins/denominators changed')
    d = validation['denominators']
    require(d['originalCatalogContracts'] == d['historicalSourceJournalRecords'] == 30 and d['errataRecords'] == d['changedContracts'] == 2 and d['changedSemanticFields'] == 3, 'errata denominator changed')
    require(d['newSourceRecords'] == d['newGlobalRecords'] == d['runtimeObservations'] == 0, 'errata source/global/runtime boundary changed')
    require(old_peer['status'] == 'completed-with-two-static-wording-findings' and old_peer['metadataChecks'] == {'status':'passed','checks':1486,'errors':[]}, 'original peer status/count changed')
    require(len(old_peer['semanticFindings']) == 2, 'original semantic findings changed')
    old_reviewed = {Path(p['path']).name:p for p in old_peer['reviewedProducts']}
    for name in ('file-change-view-contracts.json','evidence.jsonl','summary.md','validation.json','freeze-manifest.json','freeze-confirmation.json'):
        require({k:old_reviewed[name][k] for k in ('bytes','sha256')} == pin(inputs['original/'+name]), 'original peer metadata pin')
    require(peer['status'] == 'passed-with-static-scope-limits' and peer['checks'] == 130 and peer['errors'] == [], 'limited delta peer changed')
    require(validation['status'] == 'passed' and validation['checks'] == 609 and validation['errors'] == [], 'author delta validation changed')
    require(confirm['status'] == 'passed' and confirm['checks'] == 162 and confirm['errors'] == [], 'errata postfreeze changed')
    require({k:confirm['manifest'][k] for k in ('bytes','sha256')} == pin(inputs['errata/freeze-manifest.json']), 'confirmation manifest identity')
    require([r['name'] for r in docs['original/freeze-manifest.json']['formalCopyAllowlist']] == [name.split('/',1)[1] for name in EXPECTED if name.startswith('original/') and 'peer-review' not in name], 'original minimum allowlist changed')
    require(manifest['formalCopyAllowlist'] == [name.split('/',1)[1] for name in EXPECTED if name.startswith('errata/')], 'errata10 allowlist changed')
    for product in manifest['finalProducts']:
        name = 'errata/' + Path(product['path']).name
        require({k:product[k] for k in ('bytes','sha256')} == pin(inputs[name]), 'errata finalProduct pin')
    for product in peer['reviewedProducts']:
        name = 'errata/' + Path(product['path']).name
        require({k:product[k] for k in ('bytes','sha256')} == pin(inputs[name]), 'delta reviewedProduct pin')
    return old, new, d

def build_plan(inputs):
    outputs = {RAW / name: raw for name, raw in inputs.items()}
    outputs.update({Path(name): inputs[source] for name, source in ALIASES.items()})
    outputs[Path(SUMMARY)] = (
        '固定基线的文件与变更查看静态合同当前为版本2：原30条合同保留，仅C012缓存预热与C018 worker请求的异常边界由两条元数据errata限定。旧36功能组、原30条journal与51个选定单位的分母不变；新增source/global/功能/运行观察均为0。\n\n'
        '[当前合同](file-change-view-contracts-v2.json) · [两条errata记录](file-change-view-errata-evidence.jsonl) · [修订清单](file-change-view-errata.json) · [限定delta审查](file-change-view-errata-peer-review.json) · [交付来源](file-change-view-contracts-delivery-provenance.json)。\n\n'
        'Wt仅吞掉callback返回值经local .catch处理的Promise rejection；同步调用或.catch异常进入outer catch并受token/generation条件约束。IWn.request先插入pending；返回Promise rejection可清理，同步sender/.catch异常逃出非async请求，所选路径没有该清理。已保存async preload声明不证明实际bridge receiver。\n\n'
        '[原冻结核心](raw/file-change-view-contracts/original/file-change-view-contracts.json)及[原30行journal](raw/file-change-view-contracts/original/evidence.jsonl)保存历史原字节；[原peer](raw/file-change-view-contracts/original/peer-review.json)仍为completed-with-two-static-wording-findings，1486项metadata检查不等于全语义通过。[原摘要](raw/file-change-view-contracts/original/summary.md)、[errata原摘要](raw/file-change-view-contracts/errata/summary.md)也原字节保留。原摘要相对链接按原本地上下文理解，本阅读页仅提供正式位置导航。\n\n'
        '作者609、限定peer130、errata封存后162为不同范围，分别保存、不相加、未在交付时重跑。实际UI、transport/main/app-server/Git receiver、持久化、运行时序与模式仍待证实；Git写操作没有由名称得到确认。交付脚本只读显式元数据，不读取原JS/AST/完整单位或执行目标。一次作者目录诊断误对旧保存AST做字节哈希读取，未解析/复制/引入新事实，详见交付provenance披露。\n'
    ).encode()
    require(len(outputs) == 23, 'metadata23 output count changed')
    return outputs

def output_pins(outputs):
    return [{'path':str(OUT / name),'relativePath':name.as_posix(),**pin(raw)} for name, raw in outputs.items()]

def main():
    phase = argparse.ArgumentParser()
    phase.add_argument('--phase', choices=('preflight','deliver','finalize','verify'), required=True)
    args = phase.parse_args()
    require(pin(Path(__file__).read_bytes()) == pin(SCRIPT.read_bytes()), 'executed capture differs from owned formal script')
    inputs, input_receipts = load_inputs()
    old, catalog, denominator = verify_metadata(inputs)
    outputs = build_plan(inputs)
    capture_receipts = []
    if args.phase in ('finalize','verify'):
        for name in CAPTURES:
            p = WORK / name
            safe(p)
            require(p.is_file(), 'completed own delivery capture missing: ' + name)
            raw = p.read_bytes()
            target = RAW / 'delivery' / name
            outputs[target] = raw
            capture_receipts.append({'original':file_pin(p),'published':target.as_posix(),'role':'own new delivery code/metadata/capture only'})
        for attempt in ('preflight-02','deliver-01'):
            receipt = json.loads((WORK / 'attempts' / attempt / 'receipt.json').read_bytes())
            require(receipt['exitCode'] == 0, 'captured delivery phase failed')
            for kind in ('source','stdout','stderr','runner'):
                require(file_pin(Path(receipt[kind]['path'])) == receipt[kind], 'actual capture pin mismatch: ' + kind)
            require(receipt['source']['sha256'] == file_pin(SCRIPT)['sha256'], 'captured source not owned delivery script')
        provenance = {
            'schemaVersion':'file-change-metadata-delivery/1','baselineId':BASELINE,'status':'fixed-metadata-delivered-with-two-static-errata',
            'inputMetadata':input_receipts,'outputs':output_pins(build_plan(inputs)),
            'ownCompletedDeliveryCaptures':capture_receipts,'deliverySource':file_pin(SCRIPT),
            'denominators':denominator,'originalCatalogDenominators':old['denominators'],
            'savedChecksNotRerun':{'originalCorePeerMetadata':1486,'originalCoreSemanticFindings':2,'authorErrata':609,'independentErrataDelta':130,'errataPostfreeze':162,'interpretation':'Different scopes, not summed; no producer/verifier rerun.'},
            'originalPeerStatus':'completed-with-two-static-wording-findings','limitedDeltaPeerStatus':'passed-with-static-scope-limits',
            'originalJournal':'30 historical rows copied exactly; prior claim wording preserved. Fresh2 errata do not enter global evidence or feature counts.',
            'scope':'Original6 metadata plus original peer2; errata10 metadata. Four exact current aliases and one reader summary. Only new delivery-owned code/captures are archived.',
            'inheritedOriginalSourcePins':catalog['originalSourcePins'],'originalSourcePinsReadOrRehashed':False,
            'formalMetadataOutputCount':24,'ownCompletedCaptureOutputCount':len(CAPTURES),
            'actualFinalizeReceipt':str(WORK / 'attempts/finalize-01/receipt.json'),
            'receiptTiming':'Preflight/delivery source/stdout/stderr/exit receipts completed before this provenance. Finalize receipt is written by parent runner after this phase and handed off separately; no self-pinning or presumed completion.',
            'retainedFailedAttempt':{'path':str(WORK/'attempts/preflight-01/receipt.json'),'exitCode':1,'reason':'Wrong original peer Markdown filename review.md; actual name peer-review.md. No formal output writes.'},
            'operatorDiagnosticDisclosure':json.loads((WORK/'author-diagnostic-disclosure.json').read_bytes()),
            'protectedFiles':'README/report/state/global evidence/future publisher are not output paths.',
            'targetExecuted':False,'deliveryProgramOriginalJsOrAstOrUnitsReadOrCopied':False,'originalJsReadOrParsedInThisTask':False,'thirdPartyImplementationCopied':False,'uiNetworkModelProfileAuthUsed':False,
        }
        outputs[Path(PROVENANCE)] = encode(provenance)
    planned = {OUT / name: raw for name, raw in outputs.items()}
    local = WORK/('delivery-validation.json' if args.phase == 'deliver' else args.phase+'-validation.json')
    # This receipt is new per phase. Its final check count is known after copies;
    # require absence and writable parents before any planned output is written.
    require(not local.exists(), 'phase validation already exists: ' + str(local))
    preflight(local, b'')
    if args.phase == 'preflight':
        raw = encode({'schemaVersion':1,'baselineId':BASELINE,'status':'preflight-passed','inputs':input_receipts,'plannedMetadataOutputs':output_pins(outputs),'deferredProvenance':{'path':str(OUT/PROVENANCE),'reason':'Final provenance pins completed own delivery receipt; generated in finalize phase.'},'futureOwnCaptures':CAPTURES,'scope':'Metadata-only preflight; no formal output writes.'})
        planned[WORK/'preflight-plan.json'] = raw
        # Deferred output has no available bytes yet; require absence now.
        require(not (OUT/PROVENANCE).exists(), 'new deferred provenance already exists')
        preflight(OUT/PROVENANCE, b'')
    for path, raw in planned.items():
        preflight(path, raw)
    if args.phase == 'verify':
        for path, raw in planned.items():
            require(path.is_file() and path.read_bytes() == raw and path.stat().st_mode & 0o777 == 0o444, 'formal output verification failed: ' + str(path))
    else:
        for path, raw in planned.items():
            if args.phase == 'preflight' and path.is_relative_to(OUT):
                continue
            write_exact(path, raw)
            require(path.read_bytes() == raw, 'exact copied bytes mismatch')
    for record in input_receipts:
        require(file_pin(Path(record['original']['path'])) == record['original'], 'frozen input changed during delivery')
    result = {'schemaVersion':1,'baselineId':BASELINE,'phase':args.phase,'status':'passed','checks':checks,'errors':[],
              'inputMetadata':input_receipts,'outputs':output_pins(outputs),'ownCaptureCount':len(capture_receipts),'historicalJournalRecords':30,'freshErrataRecords':2,
              'newGlobalSourceRecords':0,'newUserFeatures':0,'runtimeObservations':0,'executedSource':file_pin(Path(__file__).resolve())}
    write_exact(local, encode(result))
    print(json.dumps({'phase':args.phase,'status':'passed','checks':checks,'errors':[],
                      'formalMetadataOutputs':23 if args.phase in ('preflight','deliver') else 24,
                      'ownedCaptureOutputs':len(capture_receipts),'validation':file_pin(local)},ensure_ascii=False))

if __name__ == '__main__':
    main()
