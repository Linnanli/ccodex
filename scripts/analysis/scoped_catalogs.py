"""Publish immutable, scoped static-analysis archives; never evaluate archived code.

The fixed profiles identify frozen analysis inventories. Complete target source
and tool implementations are provenance-only inputs and cannot be published.
Unknown file origins stop preflight. No global evidence journal is read or edited.
"""
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from collections import Counter
from typing import Mapping, Tuple
import hashlib
import json
import os
import tempfile

BASELINE_ID = 'codex-26.1007.30912-c5b273322a83'
INDEX_NAME = 'scoped-catalogs-provenance.json'
EVIDENCE_INDEX_NAME = 'scoped-catalogs-evidence-index.jsonl'
FROZEN_ORIGIN_WORKSPACE = Path('/Users/nallylin/Documents/code/ccodex')

class PublicationError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise PublicationError(message)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def byte_pin(raw):
    return {'bytes': len(raw), 'sha256': digest(raw)}

def pin(path):
    return {'path': str(path), **byte_pin(path.read_bytes())}

@dataclass(frozen=True)
class CatalogSpec:
    catalog_id: str
    directory: str
    manifest: str
    manifest_bytes: int
    manifest_sha256: str
    main: str
    journal: str
    peer: str
    source_field: str
    source_profile: str
    evidence_prefix: str
    expected_records: int
    # Exact authored-code paths from the root-authorized frozen analysis inventory.
    # This is an origin allowlist, not an assertion that every script was executed.
    authored_code_paths: Tuple[str, ...]
    record_profile: str = 'direct-new-source'
    validation_profile: str = 'final-products'
    closure_profile: str = 'exact'

# BEGIN FIXED CATALOG CONFIGURATION
CATALOGS = (
    CatalogSpec('request-entry-unmatched-review', 'request-entry-unmatched-review-work', 'manifest.json', 39346, 'd01806f412b432827fefc362b102e15691c8ec7eba193d49d7431a004071a413', 'review.json', 'journal.jsonl', 'peer/peer-review.json', 'sourceInputs', 'unmatched-original', 'REQUEST-ENTRY-UNMATCHED-', 38, ('attempts/v1/scope_review.cjs', 'attempts/v1/snapshot_inputs.py', 'attempts/v2/discovery_inputs.py', 'attempts/v2/review.py', 'attempts/v2/scope_review.cjs', 'attempts/v3/review.py', 'attempts/v3/scope_review.cjs', 'attempts/v3/verify.py', 'discovery_inputs.py', 'inputs/scripts/analysis/features.py', 'peer/attempt-01/source.py', 'peer/attempt-02/source.py', 'peer/attempt-03/source.py', 'peer/independent-check.py', 'peer/inspect-receipt-chain.py', 'peer/inspect-saved-scope.py', 'peer/run-owned-inspection.py', 'review.py', 'scope_review.cjs', 'snapshot_inputs.py', 'verify.py'), 'revalidated-locators', 'final-products', 'exact'),
    CatalogSpec('turn-notification-state', 'turn-notification-state-work', 'frozen-manifest.json', 40319, '22bd4e5f55e7360cc119aa3054cc801cb39db2f493024ba143d01ef51b2e1308', 'turn-notification-state.json', 'evidence.jsonl', 'peer-review/peer-review.json', 'sourceInputs', 'notification-original', 'TURN-NOTIFICATION-STATE-', 221, ('attempts/freeze-v1/freeze.py', 'attempts/inspect-v1/inspect.mjs', 'attempts/inspect-v1/run-attempt.py', 'attempts/inspect-v2/inspect.mjs', 'attempts/inspect-v2/run-attempt.py', 'attempts/inspect-v3/inspect.mjs', 'attempts/inspect-v3/run-attempt.py', 'attempts/inspect-v4/inspect.mjs', 'attempts/inspect-v4/run-attempt.py', 'attempts/inspect-v5/inspect.mjs', 'attempts/inspect-v5/run-attempt.py', 'attempts/inspect-v6/inspect.mjs', 'attempts/inspect-v6/run-attempt.py', 'attempts/produce-v1/produce.mjs', 'attempts/produce-v1/run-attempt.py', 'attempts/produce-v2/produce.mjs', 'attempts/produce-v2/run-attempt.py', 'attempts/produce-v3/produce.mjs', 'attempts/produce-v3/run-attempt.py', 'attempts/verify-v1/run-attempt.py', 'attempts/verify-v1/verify.py', 'freeze.py', 'inspect.mjs', 'peer-review/attempt-01/run-check.py', 'peer-review/attempt-01/source.py', 'peer-review/check.py', 'peer-review/run-check.py', 'produce.mjs', 'run-attempt.py', 'verify.py'), 'direct-new-source', 'final-products', 'exact'),
    CatalogSpec('approval-entry-contracts', 'approval-entry-contracts-work', 'freeze-manifest.json', 23294, '564471546ad068bf254ec20e879829a508b4279cc95d6f4b7cf6aa28db9eaeea', 'approval-entry-contracts.json', 'evidence.jsonl', 'peer-review/independent-review-final.json', 'sourcePins', 'approval-original', 'APPROVAL-ENTRY-AST-', 30, ('attempt-01-source.cjs', 'attempt-02-source.cjs', 'attempt-03-source.cjs', 'attempt-04-source.py', 'attempt-05-source.py', 'attempt-06-source.py', 'build_contracts.py', 'extract-fast.cjs', 'extract-response-context.cjs', 'extract.cjs', 'freeze-attempt-01-source.py', 'freeze.py', 'peer-review/attempt-01-source.cjs', 'peer-review/attempt-02-source.cjs', 'peer-review/attempt-03-source.py', 'peer-review/attempt-04-source.py', 'peer-review/capture-decisions.py', 'peer-review/inspection-01-source.py', 'peer-review/inspection-02-source.py', 'peer-review/inspection-03-source.py', 'peer-review/pin-final-source.py', 'peer-review/pin-final.py', 'peer-review/read-claims.py', 'peer-review/read-selected.py', 'peer-review/verify-claims.py', 'peer-review/verify-static.cjs'), 'direct-new-source', 'approval-peer-reviewed-products', 'exact'),
    CatalogSpec('computer-use-settings-boundary', 'computer-use-settings-boundary-work', 'freeze-manifest.json', 61762, 'abe311a6398525979a44228a640ccda285fa251af5673e39937a8f988f833f00', 'computer-use-settings-boundary.json', 'computer-use-settings-boundary-evidence.jsonl', 'peer-review/peer-review.json', 'sourcePins', 'computer-settings-original', 'CUSET-EVIDENCE-', 28, ('attempts/01/inspect_bindings.mjs', 'attempts/02/inspect_services.mjs', 'attempts/03/inspect_rpc.mjs', 'attempts/04/inspect_host.mjs', 'attempts/05/inspect_definitions.mjs', 'attempts/06/inspect_handlers.mjs', 'attempts/07/inspect_storage_channel.mjs', 'attempts/08/inspect_host_receiver.mjs', 'attempts/09/build_catalog.mjs', 'attempts/10/verify_catalog.mjs', 'attempts/11/inspect_path_origins.mjs', 'attempts/12/inspect_path_origins.mjs', 'attempts/13/capture_revision.mjs', 'attempts/14/build_catalog.mjs', 'attempts/15/verify_catalog.mjs', 'attempts/interactive-metadata-read-failure/source.py', 'build_catalog.mjs', 'capture_revision.mjs', 'freeze_catalog.mjs', 'inspect_bindings.mjs', 'inspect_definitions.mjs', 'inspect_handlers.mjs', 'inspect_host.mjs', 'inspect_host_receiver.mjs', 'inspect_path_origins.mjs', 'inspect_rpc.mjs', 'inspect_services.mjs', 'inspect_storage_channel.mjs', 'peer-review/attempts/01/snapshot-metadata.py', 'peer-review/attempts/02/inspect-catalog.py', 'peer-review/attempts/03/inspect-focus.py', 'peer-review/attempts/04/bounded-check.mjs', 'peer-review/attempts/05/bounded-check.mjs', 'peer-review/attempts/06/inspect-structure.py', 'peer-review/attempts/07/bounded-check.mjs', 'peer-review/attempts/08/snapshot-revision.py', 'peer-review/attempts/09/inspect-context.py', 'peer-review/attempts/10/bounded-check.mjs', 'peer-review/attempts/11/inspect-assertion-inputs.py', 'peer-review/attempts/12/bounded-check.mjs', 'peer-review/attempts/13/peer-check.py', 'peer-review/attempts/14/peer-check.py', 'peer-review/attempts/15/peer-check.py', 'peer-review/bounded-check.mjs', 'peer-review/inputs-final/attempts/13/capture_revision.mjs', 'peer-review/inputs-final/attempts/14/build_catalog.mjs', 'peer-review/inputs-final/attempts/15/verify_catalog.mjs', 'peer-review/inputs-final/build_catalog.mjs', 'peer-review/inputs-final/verify_catalog.mjs', 'peer-review/inputs/attempts/01/inspect_bindings.mjs', 'peer-review/inputs/attempts/02/inspect_services.mjs', 'peer-review/inputs/attempts/03/inspect_rpc.mjs', 'peer-review/inputs/attempts/04/inspect_host.mjs', 'peer-review/inputs/attempts/05/inspect_definitions.mjs', 'peer-review/inputs/attempts/06/inspect_handlers.mjs', 'peer-review/inputs/attempts/07/inspect_storage_channel.mjs', 'peer-review/inputs/attempts/08/inspect_host_receiver.mjs', 'peer-review/inputs/attempts/09/build_catalog.mjs', 'peer-review/inputs/attempts/10/verify_catalog.mjs', 'peer-review/inputs/attempts/11/inspect_path_origins.mjs', 'peer-review/inputs/attempts/12/inspect_path_origins.mjs', 'peer-review/inputs/attempts/interactive-metadata-read-failure/source.py', 'peer-review/inputs/build_catalog.mjs', 'peer-review/inputs/inspect_bindings.mjs', 'peer-review/inputs/inspect_definitions.mjs', 'peer-review/inputs/inspect_handlers.mjs', 'peer-review/inputs/inspect_host.mjs', 'peer-review/inputs/inspect_host_receiver.mjs', 'peer-review/inputs/inspect_path_origins.mjs', 'peer-review/inputs/inspect_rpc.mjs', 'peer-review/inputs/inspect_services.mjs', 'peer-review/inputs/inspect_storage_channel.mjs', 'peer-review/inputs/run.py', 'peer-review/inputs/verify_catalog.mjs', 'peer-review/inspect-assertion-inputs.py', 'peer-review/inspect-catalog.py', 'peer-review/inspect-context.py', 'peer-review/inspect-focus.py', 'peer-review/inspect-structure.py', 'peer-review/peer-check.py', 'peer-review/run-owned.py', 'peer-review/snapshot-metadata.py', 'peer-review/snapshot-revision.py', 'run.py', 'verify_catalog.mjs'), 'unit-linked-new-source', 'peer-reviewed-products', 'explicit-post-freeze-exclusions'),
)
# END FIXED CATALOG CONFIGURATION

def _relative(value):
    require(isinstance(value, str) and bool(value), 'missing relative path')
    p = PurePosixPath(value)
    require(not p.is_absolute() and '..' not in p.parts and '.' not in p.parts,
            'unsafe relative path: '+value)
    require(p.as_posix() == value and '\\' not in value, 'noncanonical relative path: '+value)
    return p

def _no_symlink(path):
    for p in (path, *path.parents):
        require(not p.is_symlink(), 'symlink not permitted: '+str(p))

def _json(raw, label):
    try:
        return json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise PublicationError('invalid JSON: '+label) from exc

def _rows(raw, label):
    try:
        return [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]
    except (ValueError, UnicodeDecodeError) as exc:
        raise PublicationError('invalid JSONL: '+label) from exc

def _record_pin(record):
    require(isinstance(record.get('bytes',record.get('size')), int) and record.get('bytes',record.get('size')) >= 0, 'missing byte pin')
    sha = record.get('sha256', record.get('sourceHash'))
    require(isinstance(sha, str) and len(sha) == 64 and all(c in '0123456789abcdef' for c in sha),
            'missing SHA256 pin')
    return {'bytes': record.get('bytes',record.get('size')), 'sha256': sha}

def _fixed_sources(spec, manifest, main):
    inputs = (main if spec.source_profile == 'computer-settings-original' else manifest).get(spec.source_field)
    require(isinstance(inputs, list) and bool(inputs), 'missing source identity list: '+spec.catalog_id)
    forbidden = {}
    for item in inputs:
        if spec.source_profile == 'unmatched-original':
            require(item.get('kind') == 'fixed-baseline-target-source' and item.get('originalBytesCopied') is False,
                    'unmatched original-source marker changed')
            source_path = item.get('path')
        elif spec.source_profile == 'notification-original':
            require(item.get('kind') == 'original-target-implementation-source', 'notification source marker changed')
            source_path = item.get('localPath')
        elif spec.source_profile == 'approval-original':
            require(item.get('originalCompleteAssetArchived') is False, 'approval complete-asset origin changed')
            source_path = item.get('sourcePath')
        elif spec.source_profile == 'computer-settings-original':
            require(manifest.get('sourceCopies') is False, 'settings sourceCopies marker changed')
            source_path = 'app.asar/'+_relative(item.get('relativePath')).as_posix()
        else:
            raise PublicationError('source-profile adapter is not configured: '+spec.source_profile)
        require(isinstance(source_path, str) and (Path(source_path).is_absolute() or (spec.source_profile == 'computer-settings-original' and source_path.startswith('app.asar/'))), 'original source identity unknown')
        rec = _record_pin(item)
        forbidden[(rec['bytes'], rec['sha256'])] = {'kind':'original-target-complete-source', 'path':source_path}
    # These identities are metadata only. The implementation files are never read.
    tool = manifest.get('toolRuntime')
    if isinstance(tool, dict):
        require(tool.get('kind') == 'tool-runtime-implementation', 'toolRuntime origin unknown')
        rec = _record_pin(tool)
        forbidden[(rec['bytes'], rec['sha256'])] = {'kind':'tool-runtime-implementation', 'path':tool.get('path')}
    tools = manifest.get('tools', {})
    for name in ('parser', 'node'):
        if isinstance(tools.get(name), dict):
            rec = _record_pin(tools[name])
            forbidden[(rec['bytes'], rec['sha256'])] = {'kind':'tool-runtime-implementation', 'path':tools[name].get('path')}
    if spec.source_profile == 'computer-settings-original':
        parser_inputs=[i for i in main.get('inputPins',[]) if i.get('path') == '../../../../../private/tmp/ccodex-rea-tooling/install/node_modules/@babel/parser/lib/index.js']
        require(len(parser_inputs)==1, 'settings parser metadata identity unknown')
        rec=_record_pin(parser_inputs[0]);forbidden[(rec['bytes'],rec['sha256'])]={'kind':'tool-runtime-implementation','path':parser_inputs[0]['path']}
    return inputs, forbidden

def _origin(spec, relative, raw, forbidden):
    key = (len(raw), digest(raw))
    if key in forbidden:
        return {'kind':'excluded-'+forbidden[key]['kind'], 'basis':'explicit frozen source/tool identity',
                'originPath':forbidden[key]['path'], 'allowed':False}
    suffix = PurePosixPath(relative).suffix
    if suffix in ('.js', '.cjs', '.mjs', '.py'):
        require(relative in spec.authored_code_paths, 'unknown code origin: '+spec.catalog_id+'/'+relative)
        require(suffix != '.js', 'complete or unclassified JavaScript asset is not allowed')
        return {'kind':'authored-analysis-helper', 'basis':'fixed root-authorized code path + frozen manifest pin; execution not implied', 'allowed':True}
    if suffix == '.json':
        _json(raw, relative)
        return {'kind':'saved-analysis-json', 'basis':'fixed frozen-owned analysis inventory', 'allowed':True}
    if suffix == '.jsonl':
        _rows(raw, relative)
        return {'kind':'saved-analysis-jsonl', 'basis':'fixed frozen-owned analysis inventory', 'allowed':True}
    if suffix in ('.md', '.txt', '.stdout', '.stderr') or PurePosixPath(relative).name in ('stdout', 'stderr'):
        try:
            raw.decode('utf-8')
        except UnicodeDecodeError as exc:
            raise PublicationError('nontext analysis log: '+relative) from exc
        return {'kind':'analysis-prose-or-execution-log', 'basis':'fixed frozen-owned analysis inventory; bounded excerpts allowed', 'allowed':True}
    raise PublicationError('unknown file origin: '+spec.catalog_id+'/'+relative)

def _mode(value):
    require(value in ('0444', '0o444', 0o444), 'unsupported frozen mode marker')

def _file_set(directory):
    found = set()
    for current, dirs, files in os.walk(directory, followlinks=False):
        for name in dirs:
            require(not (Path(current)/name).is_symlink(), 'symlink directory in frozen closure')
        for name in files:
            p = Path(current)/name
            require(p.is_file() and not p.is_symlink(), 'nonregular file in frozen closure')
            found.add(p.relative_to(directory).as_posix())
    return found

def _product_relative(record, directory):
    if 'relativePath' in record:
        return _relative(record['relativePath']).as_posix()
    require('path' in record, 'final product has no path')
    path = Path(record['path'])
    if not path.is_absolute():
        rel=_relative(record['path']).as_posix()
        prefix='.analysis-local/'+directory.name+'/'
        return _relative(rel[len(prefix):] if rel.startswith(prefix) else rel).as_posix()
    try:
        rel = path.relative_to(FROZEN_ORIGIN_WORKSPACE/'.analysis-local'/directory.name).as_posix()
    except ValueError as exc:
        raise PublicationError('final product escapes owned directory') from exc
    return _relative(rel).as_posix()

def _journal_counts(spec, rows, unit_ids):
    ids=[r.get('id') for r in rows]
    require(len(set(ids))==len(ids) and all(isinstance(i,str) for i in ids), 'duplicate/missing primary ID')
    require(len(rows)==spec.expected_records, 'fixed journal denominator changed')
    require(all(i.startswith(spec.evidence_prefix) for i in ids), 'primary record prefix changed')
    for row in rows:
        require(isinstance(row.get('claim'),str) and 'confidence' in row, 'producer claim/confidence missing')
        if spec.record_profile=='unit-linked-new-source':
            require(isinstance(row.get('units'),list) and bool(row['units']) and set(row['units'])<=unit_ids,
                    'settings source claim units missing/unknown')
            require(row.get('baselineId',BASELINE_ID)==BASELINE_ID, 'optional producer baseline differs')
        else:
            require(row.get('baselineId')==BASELINE_ID and 'method' in row, 'direct producer schema changed')
            loc=row.get('locator',{})
            require(isinstance(row.get('sourcePath'),str) and row['sourcePath'].startswith('app.asar/'), 'qualified original source missing')
            require(isinstance(row.get('sourceHash'),str) and len(row['sourceHash'])==64, 'source hash missing')
            require(loc.get('kind')=='byte-range' and isinstance(loc.get('start'),int) and isinstance(loc.get('endExclusive'),int)
                    and 0<=loc['start']<loc['endExclusive'], 'source locator missing')
    new_source=0 if spec.record_profile=='revalidated-locators' else len(rows)
    return {'records':len(rows),'newlyAuthoredOriginalSourceRecords':new_source,
            'revalidatedLocatorRecords':len(rows) if spec.record_profile=='revalidated-locators' else 0,
            'unitLinkedSourceClaimRecords':len(rows) if spec.record_profile=='unit-linked-new-source' else 0,
            'inheritedPrimaryRecords':0,'methods':dict(sorted(Counter(json.dumps(r.get('method'),ensure_ascii=False) for r in rows).items())),
            'confidences':dict(sorted(Counter(str(r['confidence']) for r in rows).items())), 'globalRecordsAdded':0,
            'definition':'Producer source claims in their fixed selected scope; settings unit-linked claims lack direct journal source fields. Revalidated old call locators are separate. Artifact-record views are not new source facts or features.'}


def _preflight_catalog(workspace, spec):
    directory = workspace/'.analysis-local'/spec.directory
    _no_symlink(directory)
    require(directory.is_dir(), 'missing frozen directory: '+str(directory))
    mp = directory/spec.manifest
    _no_symlink(mp)
    raw_manifest = mp.read_bytes()
    require(byte_pin(raw_manifest) == {'bytes':spec.manifest_bytes,'sha256':spec.manifest_sha256}, 'frozen manifest pin changed: '+spec.catalog_id)
    require(mp.stat().st_mode & 0o777 == 0o444, 'manifest is not readonly0444')
    manifest = _json(raw_manifest, str(mp))
    require(manifest.get('baselineId') == BASELINE_ID, 'manifest baseline mismatch')
    main_pre=_json((directory/spec.main).read_bytes(),spec.main)
    source_inputs, forbidden = _fixed_sources(spec, manifest, main_pre)
    inventory = manifest.get('files')
    require(isinstance(inventory, list), 'manifest files not a list')
    materials = {}
    file_records = []
    excluded = []
    for record in inventory:
        relative = _relative(record.get('relativePath',record.get('path'))).as_posix()
        require(relative not in materials and relative != spec.manifest, 'duplicate/self frozen inventory entry')
        path = directory/relative
        _no_symlink(path)
        require(path.is_file(), 'missing frozen file: '+relative)
        if 'path' in record and Path(record['path']).is_absolute():
            require(record['path'] == str(FROZEN_ORIGIN_WORKSPACE/'.analysis-local'/spec.directory/relative), 'frozen recorded local path mismatch: '+relative)
        _mode(record.get('mode',record.get('modeAfterFreeze')))
        require(path.stat().st_mode & 0o777 == 0o444, 'file is not readonly0444: '+relative)
        raw = path.read_bytes()
        require(byte_pin(raw) == _record_pin(record), 'frozen file pin changed: '+relative)
        origin = _origin(spec, relative, raw, forbidden)
        materials[relative] = raw
        file_records.append({'relativePath':relative,**byte_pin(raw),'mode':'0444','origin':origin})
        if not origin['allowed']:
            excluded.append({'relativePath':relative,**byte_pin(raw),'origin':origin})
    current_files=_file_set(directory)
    extras=current_files-(set(materials)|{spec.manifest})
    post_freeze=[]
    if spec.closure_profile=='exact':
        require(not extras and current_files==set(materials)|{spec.manifest}, 'frozen file closure changed: '+spec.catalog_id)
    else:
        require(manifest.get('exclusions')==['freeze-manifest.json self','freeze-confirmation.json post-freeze observation','attempts/16/ this freeze run logs/receipt created after snapshot'], 'settings exclusion declaration changed')
        require(not ((set(materials)|{spec.manifest})-current_files), 'listed settings file missing')
        for rel in sorted(extras):
            require(rel=='freeze-confirmation.json' or rel.startswith('attempts/16/'), 'undeclared post-freeze extra file')
            p=directory/rel;post_freeze.append({'relativePath':rel,**pin(p),'observedMode':oct(p.stat().st_mode&0o777),'status':'present post-freeze observation; not pinned by frozen manifest, not archived'})
    materials[spec.manifest] = raw_manifest
    file_records.append({'relativePath':spec.manifest,**byte_pin(raw_manifest),'mode':'0444',
                         'origin':{'kind':'frozen-analysis-manifest','basis':'fixed manifest hash/bytes','allowed':True}})
    allowed = {f['relativePath'] for f in file_records if f['origin']['allowed']}
    required = (spec.main,spec.journal,'summary.md','validation.json',spec.peer,spec.manifest)
    require(set(required) <= allowed, 'required publication artifact is excluded/missing')
    products = manifest.get('finalProducts')
    require(isinstance(products, list) and bool(products), 'manifest final products missing')
    for product in products:
        relative = _product_relative(product, directory)
        require(relative in materials and byte_pin(materials[relative]) == _record_pin(product), 'manifest final product mismatch')
    main = _json(materials[spec.main], spec.main)
    require(main.get('baselineId') == BASELINE_ID, 'main baseline mismatch')
    validation = _json(materials['validation.json'], 'validation.json')
    peer = _json(materials[spec.peer], spec.peer)
    require(str(peer.get('status')).startswith('passed') and peer.get('errors')==[], 'peer not passed')
    if spec.validation_profile=='final-products':
        require(validation.get('status')=='passed' and validation.get('errors')==[], 'validation not passed')
        final_products=validation.get('finalProducts')
        require(isinstance(final_products,list) and bool(final_products), 'independent validation finalProducts missing')
    elif spec.validation_profile=='approval-peer-reviewed-products':
        require(validation.get('status')=='passed-with-scope-limits' and validation.get('errors')==[], 'approval validation not passed-with-scope-limits')
        final_products=peer.get('reviewedProducts')
        require(isinstance(final_products,list) and bool(final_products), 'approval final peer product pins missing')
    else:
        require(validation.get('acceptedForIndependentPeer') is True and validation.get('errors')==[], 'settings author validation not accepted')
        require(validation.get('checksRun')==634 and peer.get('checksRun')==1252, 'settings validation/peer denominator changed')
        final_products=peer.get('reviewedProducts')
        require(isinstance(final_products,list) and bool(final_products), 'settings final peer product pins missing')
    validated=set()
    for product in final_products:
        relative=_product_relative(product,directory)
        require(relative in materials and byte_pin(materials[relative])==_record_pin(product), 'final reviewed product mismatch')
        validated.add(relative)
    require({spec.main,spec.journal,'summary.md'}<=validated, 'final pins do not cover main/journal/summary')
    units={}
    if spec.record_profile=='unit-linked-new-source':
        unit_doc=_json(materials['computer-use-settings-boundary-units.json'],'settings units')
        units={u['id']:u for u in unit_doc['units']}
        require(len(units)==144, 'settings original 144-unit denominator changed')
    rows=_rows(materials[spec.journal],spec.journal)
    counts=_journal_counts(spec,rows,set(units))
    deviations=[]
    for field in ('baselineId','method','sourcePath','sourceHash','locator','verificationStatus'):
        missing=sum(field not in r for r in rows)
        if missing:deviations.append({'field':field,'recordsMissing':missing,'adaptation':'Original rows unchanged; artifact view has publication-journal identity only. Original missing values preserved as null.'})
    noncanonical=sorted({r['confidence'] for r in rows if r.get('confidence')!='confirmed'})
    if noncanonical:deviations.append({'field':'confidence','producerValues':noncanonical,'adaptation':'Retained unchanged as producerConfidence; view confidence confirms saved-record identity only.'})
    if 'status' not in main:deviations.append({'field':'main.status','adaptation':'Missing original status retained as null.'})
    if spec.validation_profile=='approval-peer-reviewed-products':deviations.append({'field':'validation.finalProducts','adaptation':'Not present. Original passed-with-scope-limits status retained; exact final peer.reviewedProducts and freeze finalProducts used.'})
    if spec.validation_profile=='peer-reviewed-products':deviations.append({'field':'validation.status/finalProducts','adaptation':'Not present. Author acceptedForIndependentPeer/errors/checksRun plus exact final peer.reviewedProducts and freeze finalProducts used; no invented validation schema/status.'})
    inherited_files=[]
    for relative in sorted(allowed):
        if relative.startswith('inputs/') and relative.endswith('.jsonl'):
            old_rows = _rows(materials[relative],relative)
            old_ids = [r.get('id') for r in old_rows]
            inherited_files.append({'relativePath':relative,'records':len(old_rows),
                                    'uniqueIds':len(set(i for i in old_ids if isinstance(i,str))),
                                    'scope':'Archived saved input occurrences only; not primary rows or global additions.'})
    return {'spec':spec,'directory':directory,'manifest':manifest,'materials':materials,'fileRecords':file_records,
            'allowed':allowed,'excluded':excluded,'main':main,'peer':peer,'counts':counts,
            'archivedInheritedJournals':inherited_files,'sourceInputCount':len(source_inputs),
            'manifestPin':{'path':str(mp),**byte_pin(raw_manifest)},'rows':rows,'units':units,'producerSchemaDeviations':deviations,'postFreezeObservedExcluded':post_freeze}

def _arguments(out,workspace,baseline,catalog_ids):
    require(isinstance(out,Path) and isinstance(workspace,Path), 'out/workspace must be Path arguments')
    _no_symlink(out); _no_symlink(workspace)
    require(workspace.is_dir(), 'workspace does not exist')
    out=out.resolve();workspace=workspace.resolve()
    require(out.is_relative_to(workspace), 'output must be inside supplied workspace for published artifact coordinates')
    require(out != workspace and not out.is_relative_to(workspace/'.analysis-local')
            or out.is_relative_to(workspace/'.analysis-local'/'scoped-catalog-publication-work'), 'output must not overwrite source-owned workdirs')
    require(isinstance(baseline,Mapping) and baseline.get('baselineId') == BASELINE_ID, 'baseline[baselineId] must match fixed baseline')
    baseline_raw=json.dumps(dict(baseline),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    specs={s.catalog_id:s for s in CATALOGS}
    ids=tuple(specs) if catalog_ids is None else tuple(catalog_ids)
    require(len(set(ids))==len(ids) and bool(ids) and all(i in specs for i in ids), 'unknown/duplicate/not-yet-configured catalog ID')
    bindings={'out':str(out),'workspace':str(workspace),'baselineId':BASELINE_ID,
              'baselineArgumentEncoding':'canonical JSON UTF8 sorted keys compact separators',
              'baselineArgumentPin':byte_pin(baseline_raw),'catalogIds':list(ids)}
    return out,workspace,bindings,[specs[i] for i in ids]

def _aliases(spec):
    cid=spec.catalog_id
    return {'main':cid+'.json','summary':cid+'-summary.md','rawSummary':cid+'-raw-summary.md',
            'journal':cid+'-evidence.jsonl','validation':cid+'-validation.json',
            'peer':cid+'-peer-review.json','manifest':cid+'-manifest.json','provenance':cid+'-provenance.json'}

def describe_artifacts(*,out,workspace,baseline,catalog_ids=None):
    """Return the complete fixed output path plan after validating all source inputs."""
    out,workspace,bindings,specs=_arguments(out,workspace,baseline,catalog_ids)
    catalogs=[_preflight_catalog(workspace,s) for s in specs]
    paths=[INDEX_NAME,EVIDENCE_INDEX_NAME]
    for c in catalogs:
        paths.extend(_aliases(c['spec']).values())
        paths.extend('raw/scoped-catalogs/'+c['spec'].catalog_id+'/'+p for p in sorted(c['allowed']))
    return {'schemaVersion':'scoped-static-catalog-artifact-plan/1','callBindings':bindings,
            'relativePaths':paths,'absolutePaths':[str(out/p) for p in paths],
            'globalRecordsAdded':0,'originalGenericFeatureGroups':36,'functionalFeatureCensusDenominator':'unknown'}

def publish_scoped_catalogs(*,out,workspace,baseline,catalog_ids=None):
    """Preflight all frozen inputs, then publish archives/aliases and return compact state."""
    out,workspace,bindings,specs=_arguments(out,workspace,baseline,catalog_ids)
    catalogs=[_preflight_catalog(workspace,s) for s in specs]
    outputs={}
    derived_paths={INDEX_NAME,EVIDENCE_INDEX_NAME}
    state={}
    helper_source=pin(Path(__file__))
    artifact_views=[]
    for c in catalogs:
        s=c['spec'];cid=s.catalog_id;aliases=_aliases(s)
        rawdir='raw/scoped-catalogs/'+cid+'/'
        copied=[]
        for relative in sorted(c['allowed']):
            dest=rawdir+relative;raw=c['materials'][relative];outputs[dest]=raw
            copied.append({'originRelativePath':relative,'destinationRelativePath':dest,**byte_pin(raw)})
        originals={'main':s.main,'journal':s.journal,'validation':'validation.json','peer':s.peer,'manifest':s.manifest,'rawSummary':'summary.md'}
        aliases_records=[]
        for role,original in originals.items():
            raw=c['materials'][original];outputs[aliases[role]]=raw
            aliases_records.append({'role':role,'sourceRelativePath':original,'destinationRelativePath':aliases[role],**byte_pin(raw),'method':'byte-identical alias'})
        links=[{'role':r,'label':r,'relativePath':aliases[r]} for r in ('main','journal','validation','peer','manifest','provenance')]
        footer='\n\nPublication artifact links (derived from the fixed publication map):\n\n'+'\n'.join('- ['+l['label']+']('+l['relativePath']+')' for l in links)+'\n'
        raw_summary=c['materials']['summary.md'];mapped_summary=raw_summary
        replacements=[]
        link_map={}
        if cid=='approval-entry-contracts':
            link_map={'evidence.jsonl':aliases['journal'],'validation.json':aliases['validation']}
        elif cid=='computer-use-settings-boundary':
            link_map={'computer-use-settings-boundary-units.json':rawdir+'computer-use-settings-boundary-units.json'}
        for before,after in link_map.items():
            original_token=(']('+before+')').encode();replacement_token=(']('+after+')').encode()
            count=mapped_summary.count(original_token)
            require(count>0,'fixed summary link missing: '+cid+'/'+before)
            mapped_summary=mapped_summary.replace(original_token,replacement_token)
            replacements.append({'originalTarget':before,'publishedTarget':after,'exactOriginalToken':original_token.decode(),'exactReplacementToken':replacement_token.decode(),'occurrences':count,'method':'exact Markdown target token replacement in derived summary only'})
        derived=mapped_summary+footer.encode()
        derived_paths.update({aliases['summary'],aliases['provenance']})
        outputs[aliases['summary']]=derived
        derivation={'method':'Replace listed exact Markdown link targets, then append fixed artifact link footer; raw summary remains byte-identical',
                    'replacements':replacements,'mappedSummaryPin':byte_pin(mapped_summary),
                    'rawSourceRelativePath':'summary.md','rawPublishedRelativePath':aliases['rawSummary'],
                    'rawPin':byte_pin(raw_summary),'derivedRelativePath':aliases['summary'],'derivedPin':byte_pin(derived),
                    'appendedFooterUtf8':footer,'appendedFooterPin':byte_pin(footer.encode()),'links':links}
        main=c['main'];peer=c['peer']
        compact={'main':aliases['main'],'summary':aliases['summary'],'rawSummary':aliases['rawSummary'],
                 'journal':aliases['journal'],'validation':aliases['validation'],'peer':aliases['peer'],
                 'manifest':aliases['manifest'],'provenance':aliases['provenance'],'rawDirectory':rawdir,
                 'originalSchema':main.get('schemaVersion',main.get('schema')),'originalStatus':main.get('status'),
                 'originalDenominators':main.get('denominators'), 'originalScopeSummary':main.get('summary',main.get('scope')),
                 'manifestPin':c['manifestPin'],'peerStatus':peer.get('status'),'primaryJournal':c['counts'],
                 'archivedInheritedJournalOccurrences':sum(x['records'] for x in c['archivedInheritedJournals']),
                 'producerSchemaDeviations':c['producerSchemaDeviations'],'sourceInputCount':c['sourceInputCount'],'frozenInputFileCount':len(c['fileRecords']),
                 'publishedArchiveFileCount':len(c['allowed']),'excludedImplementationFiles':c['excluded'],'postFreezeObservedExcluded':c['postFreezeObservedExcluded'],
                 'globalRecordsAdded':0,'functionalFeatureCensusDenominator':'unknown','runtimeObserved':0,
                 'modeExclusionsClaimed':0,'originalGenericFeatureGroups':36}
        state[cid]=compact
        provenance={'schemaVersion':'scoped-static-catalog-provenance/1','baselineId':BASELINE_ID,'catalogId':cid,
                    'callBindings':bindings,'helperSource':helper_source,'frozenManifest':c['manifestPin'],'recordedFrozenOriginWorkspace':str(FROZEN_ORIGIN_WORKSPACE),
                    'inputCoordinatePolicy':'Manifest saved absolute coordinates remain fixed. Actual owned-file reads use supplied workspace and the same verified relative inventory; fixture relocation does not alter original pins.',
                    'originalSchema':compact['originalSchema'],'originalStatus':compact['originalStatus'],
                    'scope':'Publication validates frozen archive integrity/origin only; does not rerun analysis or promote static findings to runtime/mode/whole-feature results.',
                    'producerSchemaDeviations':c['producerSchemaDeviations'],'postFreezeObservedExcluded':c['postFreezeObservedExcluded'],'fileOriginInventory':c['fileRecords'],'excludedFiles':c['excluded'],'rawCopies':copied,'byteIdenticalAliases':aliases_records,
                    'summaryDerivation':derivation,'primaryJournal':c['counts'],'archivedInheritedJournals':c['archivedInheritedJournals'],
                    'globalJournalRead':False,'globalRecordsAdded':0,'legacyGlobalJournalRecordsUnchanged':65571,
                    'originalGenericFeatureGroupsUnchanged':36,'functionalFeatureCensusDenominator':'unknown','runtimeObserved':0,
                    'targetCodeExecuted':False,'producerRerun':False,'uiNetworkModelUsed':False,
                    'artifactPolicy':'Root-authorized fixed frozen analysis inventories only. Explicit original/tool implementations excluded by source identity. Unknown file/code origins stop preflight.'}
        journal_sha=digest(c['materials'][s.journal])
        journal_coordinate=(out/aliases['journal']).relative_to(workspace).as_posix()
        for line,row in enumerate(c['rows'],1):
            unit_refs=row.get('units')
            linked_units=[{'id':uid,'locator':c['units'][uid].get('locator'),'scope':c['units'][uid].get('scope')} for uid in (unit_refs or [])]
            artifact_views.append({'id':'SCOPED-CATALOG-'+str(len(artifact_views)+1).zfill(6),'baselineId':BASELINE_ID,
                'claim':'保存 catalog '+cid+' journal 的 '+row['id']+' 记录包含：'+row['claim']+'。静态结论适用原 scope；此视图仅核验已保存记录身份。',
                'sourcePath':journal_coordinate,'sourceHash':journal_sha,'locator':{'kind':'jsonl-record','line':line,'lineBase':1,'recordId':row['id']},
                'method':'saved-scoped-static-analysis-record-publication','confidence':'confirmed',
                'verificationStatus':'artifact-record verified;static-selected-scope-only;runtime/mode/persistence unknown',
                'catalogId':cid,'originalId':row['id'],'producerConfidence':row.get('confidence'),'producerMethod':row.get('method'),
                'originalUnits':unit_refs,'linkedProducerUnitMetadata':linked_units,
                'mainRelativePath':aliases['main'],'rawJournalRelativePath':rawdir+s.journal,
                'originalScope':main.get('scope'),'originalSourceLocator':{'sourcePath':row.get('sourcePath'),'sourceHash':row.get('sourceHash'),'locator':row.get('locator')},
                'claimScope':'Saved artifact identity only; no additional original-source/runtime/feature claim and no global integration.'})
        outputs[aliases['provenance']]=(json.dumps(provenance,indent=2,ensure_ascii=False)+'\n').encode()
    state={'schemaVersion':'scoped-static-catalog-state/1','baselineId':BASELINE_ID,'provenanceIndex':INDEX_NAME,
           'catalogs':state,'catalogCount':len(state),'primaryJournalRecords':sum(c['counts']['records'] for c in catalogs),
           'newlyAuthoredOriginalSourceRecords':sum(c['counts']['newlyAuthoredOriginalSourceRecords'] for c in catalogs),
           'revalidatedLocatorRecords':sum(c['counts']['revalidatedLocatorRecords'] for c in catalogs),
           'artifactRecordViews':len(artifact_views),'evidenceIndex':EVIDENCE_INDEX_NAME,
           'inheritedPrimaryRecords':sum(c['counts']['inheritedPrimaryRecords'] for c in catalogs),
           'globalRecordsAdded':0,'legacyGlobalJournalRecordsUnchanged':65571,'originalGenericFeatureGroupsUnchanged':36,
           'functionalFeatureCensusDenominator':'unknown','runtimeObserved':0}
    outputs[EVIDENCE_INDEX_NAME]=('\n'.join(json.dumps(v,ensure_ascii=False,separators=(',',':')) for v in artifact_views)+'\n').encode()
    index={'schemaVersion':'scoped-static-catalog-publication-index/1','baselineId':BASELINE_ID,
           'callBindings':bindings,'helperSource':helper_source,'state':state,'evidenceIndex':{'relativePath':EVIDENCE_INDEX_NAME,**byte_pin(outputs[EVIDENCE_INDEX_NAME]),'records':len(artifact_views),'recordScope':'Artifact-level standard view only; globalRecordsAdded=0'},'producerSchemaDeviations':{c['spec'].catalog_id:c['producerSchemaDeviations'] for c in catalogs},
           'artifactRelativePaths':sorted([*outputs,INDEX_NAME]),'replaceableDerivedArtifacts':sorted(derived_paths),
           'existingOutputPolicy':'Immutable archives and byte-identical aliases must match. Listed derived metadata, evidence view and summaries may be atomically replaced after all input/destination preflight succeeds.',
           'publicationPolicy':'All raw and primary aliases are byte-identical; derived summary footer and links are recorded in each catalog provenance. No old global journal or feature denominator changes.'}
    outputs[INDEX_NAME]=(json.dumps(index,indent=2,ensure_ascii=False)+'\n').encode()
    # Validate every destination before the first write. Source directories are never modified.
    for relative,raw in outputs.items():
        _relative(relative);dest=out/relative;_no_symlink(dest)
        for parent in dest.parents:
            require(not parent.exists() or parent.is_dir(),'publication parent is not a directory: '+str(parent))
        if dest.exists():
            require(dest.is_file(),'publication destination is not a file: '+str(dest))
            require(relative in derived_paths or dest.read_bytes()==raw,'immutable publication destination differs: '+str(dest))
    for relative,raw in outputs.items():
        dest=out/relative
        if not dest.exists() or (relative in derived_paths and dest.read_bytes()!=raw):
            dest.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='wb',dir=dest.parent,prefix='.scoped-catalog-',delete=False) as staged:
                staged.write(raw);temporary=Path(staged.name)
            try:
                os.replace(temporary,dest)
            finally:
                if temporary.exists():temporary.unlink()
        require(byte_pin(dest.read_bytes())==byte_pin(raw),'publication output verification failed')
    return state
