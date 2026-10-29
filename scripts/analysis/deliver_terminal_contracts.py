"""Deliver only the frozen terminal catalog's explicit metadata allowlist.

This script never reads source/AST/implementation files and does not run any
producer, target, CLI, UI, network, or model. Existing differing outputs fail
preflight before any delivery writes.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
SOURCE = WORKSPACE / '.analysis-local/terminal-feature-contracts-work'
OUT = WORKSPACE / 'analysis' / BASELINE
WORK = WORKSPACE / '.analysis-local/terminal-contracts-delivery-work'
ALLOWLIST = [
    'terminal-feature-contracts.json', 'interfaces.json', 'evidence.jsonl',
    'summary.md', 'validation.json', 'inherited-evidence.json',
    'peer-review/independent-review.json', 'peer-review/independent-review.md',
]
EXTRAS = ['frozen-manifest.json', 'freeze-confirmation.json', 'post-freeze-validation.json']
EXPECTED = {
    'terminal-feature-contracts.json': (151763, '1b636bc2f5bae3ff138481372488eb44c619cf45e1f526189b23ae26c04aa3c6'),
    'interfaces.json': (4913, 'dfd920c849909e76558a04bf82d7086bd94fddef0d4373ad0284c07f5e541db8'),
    'evidence.jsonl': (54535, '8feaa8619ccead8d6d1e0f57eed5b2e3c347f28ebe457b8575b91d88d6ff028b'),
    'summary.md': (2900, '002d75c7fa8dda8df0a1b2943df28be886758ed631826c8f2c8056e939be0f41'),
    'validation.json': (3169, '5f210632c74e69f27b0e7b345be15b52e1f70f1bf276a627f186c0bc95b64ba7'),
    'inherited-evidence.json': (10642, 'c70263d308e37e516224c8b6d83ac5491a948fb157acdda1c860a4b981134027'),
    'peer-review/independent-review.json': (30003, '482741db73c602fe2f5ecaf7021a61feace3e0e2a7130bece47bad8541d575f6'),
    'peer-review/independent-review.md': (1966, 'aff3db2b129e588a3bb759be855ae7333a3ef1cb23659f6f938d07d73d8e9c47'),
    'frozen-manifest.json': (72369, '83afca929f20f49a37702e0933eda09ab9778fc8746045a3ff7691f2c9c2cad0'),
    'freeze-confirmation.json': (913, '6f76a99a5acad659c78181973d55a84ff01b539b7f44215d041c6d6b7801286e'),
    'post-freeze-validation.json': (2887, 'd75a1c446e35833c27f0394f2bd4d2960b810bfc82b8288b353e7c9886d14dd5'),
}
ALIASES = {
    'terminal-feature-contracts.json': 'terminal-feature-contracts.json',
    'terminal-feature-contracts-evidence.jsonl': 'evidence.jsonl',
    'terminal-feature-contracts-interfaces.json': 'interfaces.json',
    'terminal-feature-contracts-validation.json': 'validation.json',
    'terminal-feature-contracts-peer-review.json': 'peer-review/independent-review.json',
    'terminal-feature-contracts-peer-review.md': 'peer-review/independent-review.md',
}
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

def safe_path(path):
    require(not path.is_symlink(), 'symlink: ' + str(path))
    require(all(not p.is_symlink() for p in path.parents), 'symlink parent: ' + str(path))

def preflight_output(path, raw):
    safe_path(path)
    require(path.is_relative_to(OUT), 'output outside fixed baseline')
    require(all(not p.exists() or p.is_dir() for p in path.parents),
            'existing output parent is not a directory: ' + str(path))
    require(not path.with_name(path.name + '.terminal-delivery-tmp').exists(), 'stale delivery temporary')
    if path.exists():
        require(path.is_file() and path.read_bytes() == raw, 'existing differing output: ' + str(path))

def write_exact(path, raw):
    if path.exists():
        return 'same-bytes-retained'
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.terminal-delivery-tmp')
    temporary.write_bytes(raw)
    temporary.chmod(0o444)
    temporary.replace(path)
    return 'created'

def main():
    require(OUT.is_dir(), 'fixed formal baseline absent')
    safe_path(SOURCE)
    require(set(EXPECTED) == set(ALLOWLIST + EXTRAS), 'fixed input closure mismatch')
    inputs = {}
    input_receipts = []
    for name in ALLOWLIST + EXTRAS:
        p = SOURCE / name
        safe_path(p)
        require(p.is_file() and p.stat().st_mode & 0o777 == 0o444, 'input not readonly metadata: ' + name)
        require(p.suffix in ('.json', '.jsonl', '.md') and not any(v in Path(name).parts for v in ('sources', 'inputs', 'attempts')), 'input is not metadata allowlist')
        raw = p.read_bytes()
        require((len(raw), pin(raw)['sha256']) == EXPECTED[name], 'frozen input changed: ' + name)
        inputs[name] = raw
        input_receipts.append({'relativePath': name, 'original': {'path': str(p), **pin(raw)}, 'mode': '0o444', 'closureRole': 'manifest-listed-allowed-metadata' if name in ALLOWLIST else 'explicit-metadata-extra-not-claimed-in-closed-file-count'})
    catalog = json.loads(inputs['terminal-feature-contracts.json'])
    manifest = json.loads(inputs['frozen-manifest.json'])
    confirmation = json.loads(inputs['freeze-confirmation.json'])
    postfreeze = json.loads(inputs['post-freeze-validation.json'])
    validation = json.loads(inputs['validation.json'])
    peer = json.loads(inputs['peer-review/independent-review.json'])
    require(catalog['baselineId'] == manifest['baselineId'] == confirmation['baselineId'] == postfreeze['baselineId'] == validation['baselineId'] == peer['baselineId'] == BASELINE, 'baseline mismatch')
    require(catalog['archivePolicy']['formalProductAllowlist'] == manifest['formalProductAllowlist'] == ALLOWLIST, 'allowlist mismatch')
    require(manifest['formalMetadataExtras'] == EXTRAS, 'metadata extras mismatch')
    require(catalog['archivePolicy']['originalCompleteLargeAssetsArchived'] is False and catalog['archivePolicy']['thirdPartyImplementationForRecovery'] is False, 'original or third-party source archival policy changed')
    require(manifest['sourcePolicy']['implementationTextInFormalProducts'] is False and manifest['sourcePolicy']['toolImplementationsCopied'] is False, 'implementation text allowed')
    closed = {r['relativePath']: r for r in manifest['files']}
    for name in ALLOWLIST:
        require(name in closed and closed[name]['formalMetadataAllowed'] is True, 'not manifest-allowed metadata: ' + name)
        require(pin(inputs[name]) == {k: closed[name][k] for k in ('bytes', 'sha256')}, 'manifest pin mismatch: ' + name)
    for document, key in [(confirmation, 'manifest'), (postfreeze, 'manifest')]:
        require({k: document[key][k] for k in ('bytes', 'sha256')} == pin(inputs['frozen-manifest.json']), 'freeze manifest receipt mismatch')
        require(document['status'] == 'passed' and document['errors'] == [], 'freeze receipt did not pass')
    require({k: postfreeze['confirmation'][k] for k in ('bytes', 'sha256')} == pin(inputs['freeze-confirmation.json']), 'postfreeze confirmation receipt mismatch')
    require(manifest['status'] == 'frozen-with-scope-limits', 'catalog not frozen')
    require(peer['findingsRemaining'] == [] and peer['status'] == 'passed-with-static-scope-limits', 'peer has remaining findings')
    pv = peer['independentVerification']
    require(pv['finalSelectedUnitAndSemanticChecks'] == 815 and pv['metadataDeltaBoundaryChecks'] == 601 and pv['errors'] == [], 'peer saved separate counts changed')
    require(validation['status'] == 'passed' and validation['checks'] == 672 and validation['errors'] == [], 'author delta validation changed')
    require(validation['sourceCoordinateValidationReused']['checks'] == 52859 and validation['sourceCoordinateValidationReused']['errors'] == [], 'author reused source validation changed')
    rows = [json.loads(line) for line in inputs['evidence.jsonl'].splitlines() if line]
    require(len(catalog['contracts']) == len(rows) == len({r['id'] for r in rows}) == 35, '35 catalog record identity changed')
    required = {'id','baselineId','claim','sourcePath','sourceHash','locator','method','confidence','verificationStatus'}
    for contract, row in zip(catalog['contracts'], rows):
        require(required <= row.keys() and all(contract[k] == row[k] for k in required), 'journal core schema/value changed')
        require(row['baselineId'] == BASELINE and row['confidence'] in ('confirmed','inferred','unresolved'), 'journal static identity/confidence changed')
    d = catalog['denominators']
    require(d == manifest['denominators'], 'manifest denominator mismatch')
    require(d['savedFeatureGroupsUnchanged'] == 36 and d['selectedCompleteFunctionsForContracts'] == 43 and d['authoredCatalogRecords'] == 35 and d['globalSourceRecordsAdded'] == 0, '35/43/36/global0 denominator changed')
    require(d['newOriginalSourceContractRecords'] == 31 and d['artifactDiscoveryOrUnknownProposalRecords'] == 4 and d['inheritedEvidenceRecords'] == 6, '31/4/6 scope changed')
    require(d['runtimeObservations'] == d['modeExclusions'] == 0 and d['wholeUserFeatureDenominator'] == 'unknown', 'unknown runtime/mode/feature boundary changed')
    require(len(json.loads(inputs['inherited-evidence.json'])['records']) == 6, 'six inherited records changed')
    outputs = {}
    copies = []
    for name, raw in inputs.items():
        relative = Path('raw/terminal-feature-contracts') / name
        outputs[relative] = raw
        copies.append({'original': str(SOURCE / name), 'published': relative.as_posix(), **pin(raw), 'role': 'exact-metadata-copy'})
    for name, source in ALIASES.items():
        outputs[Path(name)] = inputs[source]
        copies.append({'original': str(SOURCE / source), 'published': name, **pin(inputs[source]), 'role': 'exact-metadata-alias'})
    summary = (
        '已交付固定基线的终端静态合同：35 条记录（31 条原源码合同、4 条 discovery/未知/恢复建议），另有 6 条继承证据。43 个完整函数/成员是作者选定范围；旧 36 个功能组不变，全局 source records 新增 0。\n\n'
        '来源包括 7 个小 renderer/helper 模块、1 个 manager initializer 和 4 个 service-boundary 函数。宿主 terminal 注入、会话/输出/输入/尺寸及清理职责见保存合同；实际 UI、模式、PTY/native receiver、端口送达、跨进程时序、恢复持久化和完整功能分母仍 unknown。\n\n'
        '[合同](terminal-feature-contracts.json) · [记录](terminal-feature-contracts-evidence.jsonl) · [接口](terminal-feature-contracts-interfaces.json) · [作者验证](terminal-feature-contracts-validation.json) · [独立审查](terminal-feature-contracts-peer-review.json) · [原作者摘要](raw/terminal-feature-contracts/summary.md)。\n\n'
        '独立 source/semantic checks 815 与 metadata delta checks 601 分别保留；作者旧 source checks 52859 为复用，最终 delta checks 672 为另一范围，均不相加。本次只校验并复制允许的 metadata，不重跑任何分析或目标。\n'
    ).encode()
    outputs[Path('terminal-feature-contracts-summary.md')] = summary
    provenance = {
        'schemaVersion':'terminal-contracts-metadata-delivery/1', 'baselineId':BASELINE,
        'status':'scoped-frozen-metadata-delivery', 'sourceDirectory':str(SOURCE),
        'scope':'Eight exact metadata allowlist entries plus three explicit freeze metadata extras only; no original source, saved complete units, AST, target/tool implementation or analysis stdout copied.',
        'archivePolicyPreserved':catalog['archivePolicy'], 'denominators':d,
        'journalSchemaPreserved':True, 'journalConfidences':dict(Counter(r['confidence'] for r in rows)),
        'savedReviewCounts':{'independentSourceSemantic':815,'independentMetadataDelta':601,'authorReusedSource':52859,'authorFinalMetadataDelta':672,'interpretation':'Distinct overlapping scopes; not summed; none rerun by this delivery.'},
        'inputs':input_receipts, 'copies':copies,
        'derivedSummary':{'path':'terminal-feature-contracts-summary.md',**pin(summary),'basis':'Reader links and saved scope/count/unknown metadata; original summary stays exact in raw archive.'},
        'deliverySource':file_pin(Path(__file__).resolve()),
        'actualAttemptReceipt':str(WORK / 'attempts/deliver-01/receipt.json'),
        'receiptTiming':'Parent runner writes actual stdout/stderr/exit receipt after delivery ends; delivery does not claim that receipt was available before completion.',
        'outputClosure':{'rawExact':11,'topLevelExactAliases':6,'derivedSummary':1,'provenance':1,'total':19},
        'excludedFreezeMetadata':'Three named extras are allowed observations; copying them does not add them to the 230-file frozen manifest closure.',
        'globalSourceRecordsAdded':0, 'targetExecuted':False,'originalProgramsReadOrParsed':False,'authorProducerOrVerifierExecuted':False,'uiNetworkModelAuthUsed':False,
        'protectedFilesPolicy':'No existing README/report/state/global journal/IPC or unrelated formal output is a write target. Only terminal paths shown in copies/derivedSummary plus this provenance are written.',
    }
    outputs[Path('terminal-feature-contracts-delivery-provenance.json')] = encode(provenance)
    require(len(outputs) == 19, 'delivery output count changed')
    # Validate the complete plan, including existing-output equality, before writes.
    for relative, raw in outputs.items():
        preflight_output(OUT / relative, raw)
    output_receipts = []
    for relative, raw in outputs.items():
        path = OUT / relative
        action = write_exact(path, raw)
        require(path.read_bytes() == raw, 'delivered bytes mismatch')
        output_receipts.append({'path':str(path),'relativePath':relative.as_posix(),**pin(raw),'action':action,'mode':oct(path.stat().st_mode & 0o777)})
    result = {'schemaVersion':'terminal-delivery-checks/1','baselineId':BASELINE,'status':'delivered','checks':checks,'errors':[],'records':35,'selectedCompleteUnits':43,'savedFeatureGroups':36,'globalSourceRecordsAdded':0,'runtimeObserved':False,'inputs':input_receipts,'outputs':output_receipts,'executedSource':file_pin(Path(__file__).resolve()),'savedReviewsNotRerun':provenance['savedReviewCounts']}
    WORK.mkdir(parents=True,exist_ok=True)
    (WORK/'delivery-validation.json').write_bytes(encode(result))
    print(json.dumps({'status':'delivered','checks':checks,'errors':[],'records':35,'outputs':len(outputs),'validation':file_pin(WORK/'delivery-validation.json'),'provenance':file_pin(OUT/'terminal-feature-contracts-delivery-provenance.json')},ensure_ascii=False))

if __name__ == '__main__':
    main()
