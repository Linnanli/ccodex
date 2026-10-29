#!/usr/bin/env python3
"""Join a fixed set of saved proposals; never parse or execute target code."""
import copy
import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/logical-module-inventory-v1-work'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
WORK.mkdir(parents=True, exist_ok=True)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pin(path):
    path = Path(path)
    b = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(b), 'sha256': sha(b)}


inputs = {}


def read(name):
    p = Path(name)
    if not p.is_absolute():
        p = OUT / p
    inputs[str(p)] = pin(p)
    return json.loads(p.read_text())


def pointer(value, ptr):
    for token in ptr.lstrip('/').split('/') if ptr else []:
        token = token.replace('~1', '/').replace('~0', '~')
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def ref(name, ptr):
    p = Path(name)
    if not p.is_absolute():
        p = OUT / p
    d = read(p)
    pointer(d, ptr)
    return {**inputs[str(p)], 'jsonPointer': ptr}


def norm_range(raw, origin):
    r = raw.get('originalLocator', raw)
    source = r.get('source', {})
    path = r.get('sourcePath') or source.get('path')
    if path and path.startswith(str(FROZEN) + '/'):
        path = 'app.asar/' + str(Path(path).relative_to(FROZEN))
    source_hash = r.get('sourceHash') or source.get('sha256')
    loc = r.get('byteRange') or r.get('sourceLocator') or r.get('locator')
    if not loc and 'byteStart' in r:
        loc = {'start': r['byteStart'], 'endExclusive': r['byteEnd']}
    if loc and 'byteRange' in loc:
        loc = loc['byteRange']
    assert path and path.startswith('app.asar/') and source_hash and loc, r
    if loc.get('kind') == 'json-pointers':
        return {'sourcePath': path, 'sourceHash': source_hash,
                'metadataLocator': loc, 'origin': origin}
    span = r.get('spanHash') or r.get('spanSha256') or r.get('sourceSpanSha256')
    if not span and 'byteStart' in r:
        span = r.get('sha256')
    return {'sourcePath': path, 'sourceHash': source_hash,
            'byteRange': {'start': loc['start'], 'endExclusive': loc['endExclusive']},
            'inheritedSpanHash': span,
            'nodeType': r.get('nodeType') or r.get('parse', {}).get('completeNodeType'),
            'origin': origin}


def strings(v):
    if not v:
        return []
    return v if isinstance(v, list) else [v]


modules = read('modules.json')
published_index = {m['sourcePath']: i for i, m in enumerate(modules)}
records = []


def add(family, name, idx, m, ranges, role, imports, surface, state, effects,
        dependencies, intended, extra_refs=(), proposed_path=None):
    ptr = idx
    origin = ref(name, ptr)
    source_views = []
    for source in sorted({r['sourcePath'] for r in ranges}):
        n = published_index.get(source)
        source_views.append({'sourcePath': source,
                             'publishedFileEnvironment': modules[n]['environment'] if n is not None else 'unknown',
                             'source': ref('modules.json', '/' + str(n)) if n is not None else None,
                             'qualification': 'Published-file classification only; actual selected runtime instance is unobserved.'})
    unknown = strings(m.get('unresolved') or m.get('limitations') or m.get('limits') or m.get('missingEvidence'))
    row = {
        'id': 'LM-' + family + '-' + str(m.get('id', idx.rsplit('/', 1)[-1])),
        'originFamily': family, 'originId': m.get('id'), 'origin': origin,
        'status': 'inferred-maintenance-proposal; not implemented',
        'responsibility': {'value': role, 'status': 'inferred-proposal', 'basis': [origin, *extra_refs]},
        'environment': {'sourceFiles': source_views, 'intendedRuntime': intended,
                        'intendedRuntimeStatus': 'design-proposal; placement requires review',
                        'actualInstance': 'unknown'},
        'mode': {'value': 'unknown', 'disposition': 'retain',
                 'reason': 'No whole-module ChatGPT-only consumer closure is established by these proposal inputs.'},
        'sourceRanges': [r for r in ranges if 'byteRange' in r],
        'sourceMetadataRefs': [r for r in ranges if 'metadataLocator' in r],
        'imports': {'contractDependencies': imports, 'basis': [origin, *extra_refs],
                    'publishedFileDependencyRefs': [v['source'] for v in source_views if v['source']],
                    'completeLogicalImportClosure': False,
                    'qualification': 'Contract inputs and containing-file dependency references; not an exact ESM import list for the proposed split.'},
        'exports': {'observedContractSurface': surface, 'basis': [origin, *extra_refs],
                    'proposedEsmExports': None, 'completeConsumerClosure': False,
                    'qualification': 'Observed/candidate contract surface does not establish new module exports, all callers or wire equivalence.'},
        'sharedState': {'boundedContract': state, 'basis': [origin, *extra_refs],
                        'completeOwnershipClosure': False, 'runtimeValues': 'unknown'},
        'sideEffects': {'boundedContract': effects, 'basis': [origin, *extra_refs],
                        'completeEffectClosure': False, 'actualExecution': 'unobserved'},
        'thirdPartyDependencies': {'boundaries': dependencies,
                                   'implementationRecovery': False,
                                   'exactModuleDependencyClosure': False,
                                   'qualification': 'Named package/runtime boundaries or unresolved helpers; no automatic third-party ownership assignment and no generated vendor implementation.'},
        'proposedPath': {'value': proposed_path or m.get('proposedPath'),
                         'status': 'new-maintenance-design; not original directory recovery', 'basis': [origin]},
        'preservationRule': m.get('maintenanceRule') or m.get('preserve') or m.get('safeRestorationBoundary'),
        'unknowns': unknown + ['Complete imports/exports, consumer/state/effect ownership and runtime equivalence remain unverified.'],
        'featureTaskOwnership': {'featureIds': None, 'taskIds': None,
                                 'status': 'not yet joined to the current 373-feature / 48-task ownership ledger'},
        'runtimeValidated': False, 'clientImplementationGenerated': False,
    }
    assert row['proposedPath']['value'] and row['sourceRanges']
    records.append(row)


# Fixed proposal families, not a search for new modules or feature candidates.
boundary = read('module-boundary-proposals.json')
rwc = read('request-wrapper-contracts.json')
rwc_index = {x['id']: i for i, x in enumerate(rwc['contracts'])}
boundary_details = {
    'RWC-MANAGER': ('Injected requestClient and configured/local-fallback transports', 'Dfn.sendRequest; plugin invalidation', 'Transport reference and plugin caches; local fallback depends on appServices', 'Enqueue/dispatch requests and invalidate plugin caches after completion', 'Transport/RPC implementation ownership unresolved', 'renderer-side client facade candidate'),
    'RWC-SELECTOR': ('HI/qI host state, configured forHost, connected or deferred client.rpc', 'KI host-specific facade selection', 'Per-host cached/deferred proxies and connection state', 'Resolve/duplicate RPC capabilities; fallback after a failed primary branch', 'RPC transport implementation remains external/unresolved', 'renderer host selector candidate'),
    'RWC-FETCH': ('HTTP method/URL, fetchJson and desktop fetch/cancel message adapter', 'AW.sendRequest HTTP facade', 'Per-request desktop cancellation context; full ownership unknown', 'Ordinary HTTP or special vscode://codex dictation desktop message dispatch', 'Fetch/runtime and opaque HTTP helpers; ownership unresolved', 'renderer adapter candidate; existing proposed main path conflicts with containing-file placement and requires review'),
    'RWC-RESOLVER': ('Injected resolver #e', 'X2t.sendRequest getter forwards arguments to resolver result', 'Stored resolver callback; actual receiver is runtime dependent', 'Invocation of resolved sendRequest; downstream effects unresolved', 'No third-party ownership follows from injection alone', 'renderer facade candidate'),
    'RWC-HOSTED-FILES': ('Injected sendAppServerExtensionRequest callback', 'Five reviewed hosted-file member calls', 'Injected callback/connection reference; lifetime closure unknown', 'App-server extension requests; implementation/results unobserved', 'Extension/provider implementation remains unresolved', 'main service adapter candidate'),
    'RWC-HOST-TRANSPORT': ('Injected connection.handleHostRequest and prewarm handler', '_fe.sendRequest / send request-envelope adapter', 'Connection identity and request/trace context', 'Forward id/method/params/trace requests to connection/prewarm path', 'Concrete transport/provider and final wire remain unresolved', 'main host transport candidate'),
    'RWC-COORDINATION': ('Injected ipcClient or socket and source/target client/host IDs', 'c1 request/response; p1 injected-client facade', 'Request IDs, timeout and socket response coordination', 'Socket writes and response waiting; live execution unobserved', 'Socket/runtime dependency; injected-client ownership unresolved', 'main-or-shared coordination candidate; not a proved single-process split'),
    'RWC-PROJECTS': ('Renderer project service facade, main qHe and workspace/confirmation/persistence adapters', 'projects.createLocal and reviewed dialog/service entry chain', 'Project state, workspace roots and assignments across process boundaries', 'Source/default-root selection, confirmation, assignment and project/state mutation', 'MessagePort/RPC implementation external; helper ownership unresolved', 'cross-process domain boundary; renderer client and main persistence require separate files'),
}
for i, m in enumerate(boundary['proposals']):
    origin = ref('module-boundary-proposals.json', f'/proposals/{i}')
    ranges = [norm_range(x, {**origin, 'jsonPointer': f'/proposals/{i}/sourceMappings/{j}'}) for j, x in enumerate(m['sourceMappings'])]
    c = m['sourceContract']
    extra = []
    if c in boundary_details:
        imp, surf, state, effects, dep, env = boundary_details[c]
        extra = [ref('request-wrapper-contracts.json', f'/contracts/{rwc_index[c]}')]
    elif c == 'chunk-transport.json':
        imp, surf = 'Size-cache/special-array helpers and injected IPC/window adapters', 'Queued sender/receiver and start/chunk/end framing with current acknowledgement'
        state, effects = 'One active transfer per target; assembly and size/shared-object caches', 'Frame delivery, acknowledgement, retry and dispatch; missing-ACK deadline remains unknown'
        dep, env = 'Electron/preload IPC and structured-clone runtime; helper provenance incomplete', 'pure shared codec plus separately owned main/preload/renderer adapters'
        extra = [ref('chunk-transport.json', '/staticContractSummary'), ref('chunk-transport.json', '/suggestedImplementationBoundary')]
    else:
        imp, surf = 'Imported React/DOM runtime and annotation application callbacks', 'Annotation lifecycle/root adapter; preserve reviewed render/unmount boundaries'
        state, effects = 'Annotation/root lifecycle state; complete ownership unknown', 'Application mounting/rendering/disposal contract; live reachability unobserved'
        dep, env = 'React and React DOM package entrypoint candidates; exact lock/modification/behavior parity unverified', 'browser-page preload application adapter candidate'
        extra = [ref('dependency-import-decisions.json', '/applicationWrapperResponsibilities/0')]
    add('BOUNDARY', 'module-boundary-proposals.json', f'/proposals/{i}', m, ranges, m['responsibility'], imp, surf, state, effects, dep, env, extra)

ah = read('app-host-maintenance.json')
ah_refs = {r['id']: (i, r) for i, r in enumerate(ah['evidenceReferences'])}
ah_state = [
    ('Selected window message/port and injected IPC adapter', 'Window message forwarding bridge', 'Listener/window envelope lifecycle; sender and port identity unresolved', 'postMessage with selected transfer list'),
    ('Event predicate, context resolver, connection/RPC and remote-view adapters', 'QXe connection entry / registerAppView', 'Per-connection context/remote-view lifecycle', 'Optional createAppHost, port connection and remote view registration'),
    ('WindowServices, membership registry and sender/frame predicate', 'Context getter/setter and registration predicate', 'M1e context slot and registered-window membership', 'Setter registers existing non-destroyed windows; populate/unregister closure unresolved'),
    ('Injected provider constructors, state/principal and disposal callbacks', 'hXe.createAppHost service composition', 'Service/provider instances and origin-destruction lifecycle', 'Construct/publish services and attach disposal hooks'),
    ('Fetch callback, AbortController, response/stream bridge', 'Fetch/cancel/dispose provider operations', 'Request-ID to AbortController map', 'Abort mapped request and clear response/stream resources'),
    ('Identity/header/error helpers and network adapter', 'Ude.fetchHttp / performDesktopFetch / progress request', 'Auth/workspace/retry and response observation context', 'Destination guards, fetch/progress, response/error normalization'),
    ('Policy/config/session and native fetch/request adapters', 'Application network policy and transport facade', 'Loading/ready/failed, generation, restrictions and allowlist', 'Refresh policy, enforce destination rules and delegate fetch/request'),
    ('Requirements/config parser, temporary transport and permission/relaunch adapter', 'Requirements read and startup lifecycle', 'Startup requirements and temporary transport state', 'Initialize/read/finally-close; permission/relaunch candidate effects'),
]
for i, m in enumerate(ah['modules']):
    ranges = []
    for eid in m['evidenceIds']:
        n, value = ah_refs[eid]
        ranges.append(norm_range(value, ref('app-host-maintenance.json', f'/evidenceReferences/{n}')))
    imp, surf, state, effects = ah_state[i]
    dep_refs = [ref('app-host-maintenance.json', f'/dependencyBoundaries/{n}') for n, x in enumerate(ah['dependencyBoundaries']) if x['id'] in m['dependsOn']]
    interface_refs = [ref('app-host-maintenance.json', f'/interfaces/{n}') for n, x in enumerate(ah['interfaces']) if x['id'] in m['dependsOn']]
    add('APPHOST', 'app-host-maintenance.json', f'/modules/{i}', m, ranges, m['responsibility'], imp, surf, state, effects,
        {'dependencyBoundaryRefs': dep_refs, 'interfaceRefs': interface_refs,
         'qualification': 'AH-B03/B04/B05 include opaque helpers of unresolved ownership; do not automatically externalize all helpers.'},
        'preload bridge candidate' if i == 0 else 'main composition/adapter candidate', interface_refs + dep_refs)

sc = read('source-contract-module-proposals.json')
sc_details = [
    ('Store get/set and Qoe/dPt/pPt state bindings', 'gS mode transition; existing gS-as-jqn export is a separate source fact', 'Supplied store and requested-mode atoms', 'Conditional dPt write followed by pPt; errors propagate without local rollback', 'Store/factory/helper implementation ownership unresolved', 'renderer transition adapter candidate'),
    ('Access flags and persistedMode input', 'lPt conditional mode resolver', 'Input values only in the selected resolver; global state ownership unknown', 'Returns work/chat/undefined or unvalidated persisted value; runtime input unobserved', 'Access/provider helpers unresolved', 'renderer resolver candidate'),
    ('Fu/fd/Ch factories and injected store/atom consumers', 'Selected vS/state declarations and derived state graph', 'home-composer-mode-v1 and related atom graph; persistence not proven', 'Initialization/derived reads; execution, storage and notification behavior unknown', 'Factory/provider ownership and storage implementation unresolved', 'renderer state-definition candidate'),
    ('objc-js NobjcLibrary/fromPointer/typedBlock and native window handle', 'Window event monitor factory returning cleanup', 'Monitor handle and window callback lifecycle', 'Install local event monitor, invoke matching callback and remove monitor', 'objc-js package import; native ABI/build provenance and behavior unverified', 'main macOS window adapter candidate'),
    ('objc-js RunLoop/typedBlock and notification center', 'Notification permission Promise and RunLoop/center helpers', 'RunLoop reference count/cleanup and cached notification center', 'Request authorization; callback or synchronous-error cleanup; reject/resolve', 'objc-js package import; native callback/RunLoop and ABI parity unverified', 'main macOS notifications adapter candidate'),
    ('objc-js callFunction/fromPointer/NobjcLibrary plus J5/Y5 helpers', 'pFe Apple Event wrapper factory', 'Returned library/class/function references; full lifetime unknown', 'Construct typed wrappers; actual Apple Event dispatch not established', 'objc-js package import; J5/Y5 ownership and native permissions unresolved', 'worker macOS Apple Event adapter candidate'),
]
for i, m in enumerate(sc['proposals']):
    ranges, refs = [], []
    for s in m['sourceRefs']:
        d = read(s['artifact'])
        assert inputs[str(OUT / s['artifact'])]['sha256'] == s['artifactPin']['sha256']
        r = ref(s['artifact'], s['pointer'])
        refs.append(r)
        ranges.append(norm_range(pointer(d, s['pointer']), r))
    imp, surf, state, effects, dep, env = sc_details[i]
    contract_file = m['sourceRefs'][0]['artifact']
    if i < 3:
        refs.append(ref(contract_file, '/' + ['transition', 'resolver', 'stateInitialization'][i]))
    else:
        refs.append(ref(contract_file, '/contracts/' + str([16, 17, 18][i - 3])))
    add('SOURCE', 'source-contract-module-proposals.json', f'/proposals/{i}', m, ranges, m['responsibility'], imp, surf, state, effects, dep, env, refs)

provider = read('submission-recovery-guidance.json')
provider_details = [
    ('Scope/effect hooks and appServices registry presence', 'OMc installs Bfn/Vfn provider lifecycle', 'Scope and provider installation/cleanup', 'Effect installs and retires selected provider branch', 'apps/desktop/src/renderer/app-host/provider-lifecycle.ts'),
    ('HI/qI, forHost and connected/deferred client.rpc', 'KI host RPC selection', 'Per-host proxy cache/deferred capability', 'Resolve/duplicate/retire capabilities; primary error fallback', 'packages/app-host-client/src/host-rpc-selector.ts'),
    ('X3 registry, Sii/loi and N3 fallback condition', 'Domain-manager registration/lookup/disposal', 'Per-scope host-manager registry and subscribers', 'Register/replace/delete/dispose managers and publish state', 'packages/app-server-client/src/domain-host-registry.ts'),
    ('Captured N3 manager, MessageChannel and nIt/eIt RPC connector', 'yMc/vMc internal manager/coordinator facade', 'Per-host manager/client/server records', 'Create/connect ports; replace changed manager and clean resources', 'apps/desktop/src/renderer/app-host/internal-manager-rpc.ts'),
    ('Provided appServerManagers registry and entry.manager RPC capability', 'SMc ready-entry host facade and forHost', 'Per-host watches, leases, registry/client duplicates and connection state', 'Accept ready entry, publish HI; retire stale/replaced/disconnected resources', 'apps/desktop/src/renderer/app-host/host-provided-rpc.ts'),
]
for i, m in enumerate(provider['modules']):
    ranges, refs = [], []
    for j, u in enumerate(m['sourceUnits']):
        r = ref('submission-recovery-guidance.json', f'/modules/{i}/sourceUnits/{j}')
        ranges.extend(norm_range(x, r) for x in u['sourceRanges'])
    for c in m['sourceContracts']:
        refs.append(ref('submission-host-instance.json', c['jsonPointer']))
    if i == 4:
        refs.append(ref('resume-provider-resolution.json', '/providerBranches'))
    imp, surf, state, effects, path = provider_details[i]
    add('PROVIDER', 'submission-recovery-guidance.json', f'/modules/{i}', m, ranges, m['responsibility'], imp, surf, state, effects,
        'RPC framework/transport implementation external; exact dependency/ABI/entrypoint closure incomplete',
        'renderer host-provider candidate', refs, path)
    if i == 4:
        records[-1]['refinement'] = {'source': ref('resume-provider-resolution.json', '/providerBranches'),
                                    'qualification': 'Later source review conditionally joins provided endpoint to main jfe/vp/kM; actual selected branch/instance and service result remain unobserved. Earlier proposal unknown is retained as historical wording.'}

ctx = read('source-context-module-proposal.json')
ctx_ranges = [norm_range(x, ref('source-context-module-proposal.json', f'/sourceMappings/{i}')) for i, x in enumerate(ctx['sourceMappings'])]
add('CONTEXT', 'source-context-module-proposal.json', '', ctx, ctx_ranges, ctx['responsibility'], 'node:async_hooks and supplied source-context value/callback',
    ctx['candidateInterface'], 'Async-local namespace/instance lifecycle and values remain unobserved',
    'Forward callback through context runner; preserve return/Promise identity and throw behavior', ctx['dependency'],
    ctx['environment'], [ref('source-context-module-proposal.json', '/candidateInterface')])

runtime = read('runtime-feature-policy-contracts.json')
runtime_details = [
    ([0, 1, 2, 3, 4], 'Allowlisted boolean merge/cache, auth owner and generation invalidation', 'Native feature methods and auth/principal callbacks', 'Allowlist setter/reset and legacy enable/disable policy', 'e$ shared cache, owner identity and generation', 'Ordered native calls/cache updates and owner reset', 'main policy candidate'),
    ([4, 6, 8], 'Expose runtime feature capabilities through the app-host service boundary', 'RPC base, app state, principal getter and native feature API', 'uze get/set/is-enabled service operations', 'Provider/app-state references and service lifecycle', 'Publish owlFeatures service; map only the specified unsupported error', 'main service provider candidate'),
    ([5, 6, 7, 8], 'Ready/evaluation context checks and runtime-feature gate dispatch', 'Gate SDK/data/hash/equality helpers and owlFeatures service facade', 'bZs/xZs evaluation/dispatch with two mapped runtime feature keys', 'WeakMap identity continuity and gate evaluation context', 'Parallel legacy/runtime dispatch under recorded guards', 'renderer gate adapter candidate'),
]
for i, (facts, role, imp, surf, state, effects, env) in enumerate(runtime_details):
    ranges, refs = [], []
    for n in facts:
        fact = runtime['facts'][n]
        r = ref('runtime-feature-policy-contracts.json', f'/facts/{n}')
        refs.append(r)
        ranges.extend(norm_range(x, r) for x in fact['supportingSourceSpans'])
    path = runtime['maintenanceDecision']['proposedSourceUnits'][i]
    add('RUNTIME', 'runtime-feature-policy-contracts.json', f'/maintenanceDecision/proposedSourceUnits/{i}',
        {'id': f'RF-{i+1}', 'limits': runtime['remainingLimits']}, ranges, role, imp, surf, state, effects,
        runtime['maintenanceDecision']['externalDependencies'], env, refs, path)

settings = read('settings-module-synthesis.json')
settings_details = [
    ('Asset components/providers and platform-sensitive selection', 'ua descriptor registry, da initializer and la accessor', 'Descriptor table and accessor/initializer wiring', 'Asset selection only; 53 descriptors are not 53 settings workflows', 'settings/asset-registry.ts'),
    ('Page loader/constructor adapters and imported page targets', 'lQa page-factory lookup table', 'Factory table and loader references; delivery unknown', 'Conditional construction/dynamic loading; page behavior not covered', 'settings/page-factory-registry.ts'),
    ('gWa/wnt-to-Rr data link and injected visibility/auth/host/capability context', 'Section data, _a dispatcher and Ea visibility factory', 'Section registry and parameter-dependent predicates', 'Visibility processing; route mounting is not established', 'settings/sections-and-visibility.ts'),
    ('Router/navigation and MNs/PNs helpers plus page factory table', 'M6 settings redirect/lookup/render contract', 'Selected section and search/hash/state/mode query context', 'Ordered redirects preserving search/hash/state, then conditional lQa lookup', 'settings/route-policy-and-renderer.tsx'),
]
for i, m in enumerate(settings['fourLayerBoundaryRecommendations']):
    ranges = [norm_range(x, ref('settings-module-synthesis.json', f'/fourLayerBoundaryRecommendations/{i}/sourceAnchors/{j}')) for j, x in enumerate(m['sourceAnchors'])]
    imp, surf, state, effects, path = settings_details[i]
    add('SETTINGS', 'settings-module-synthesis.json', f'/fourLayerBoundaryRecommendations/{i}', m, ranges, m['safeRestorationBoundary'], imp, surf, state, effects,
        'Router/React/loader/hooks remain dependency interfaces; exact provenance, full imports and library modification not established by this synthesis',
        'renderer settings support layer candidate', (), path)
    records[-1]['historicalQualification'] = 'Source synthesis predates later settings workflow batches. Its saved missing-evidence wording applies to these selected registration/route contracts, not a new claim that all current workflow analysis is missing.'

assert len(records) == 38
assert len({r['id'] for r in records}) == 38

# Only byte/hash identity verification of already recorded spans. No AST or target execution.
source_bytes = {}
span_count = 0
for row in records:
    seen = set()
    unique_ranges = []
    for r in row['sourceRanges']:
        key = (r['sourcePath'], r['sourceHash'], r['byteRange']['start'], r['byteRange']['endExclusive'])
        if key in seen:
            continue
        seen.add(key)
        if r['sourcePath'] not in source_bytes:
            source_bytes[r['sourcePath']] = (FROZEN / r['sourcePath'].removeprefix('app.asar/')).read_bytes()
        b = source_bytes[r['sourcePath']]
        assert sha(b) == r['sourceHash'], r['sourcePath']
        start, end = r['byteRange']['start'], r['byteRange']['endExclusive']
        assert 0 <= start < end <= len(b), r
        digest = sha(b[start:end])
        if r['inheritedSpanHash']:
            assert digest == r['inheritedSpanHash'], r
        r['verifiedSpanHash'] = digest
        r['hashVerificationScope'] = 'identity-only; inherited source claim not independently reanalysed'
        unique_ranges.append(r)
        span_count += 1
    row['sourceRanges'] = unique_ranges
    for r in row['sourceMetadataRefs']:
        if r['sourcePath'] not in source_bytes:
            source_bytes[r['sourcePath']] = (FROZEN / r['sourcePath'].removeprefix('app.asar/')).read_bytes()
        assert sha(source_bytes[r['sourcePath']]) == r['sourceHash']
        r['hashVerificationScope'] = 'whole-file identity only; inherited JSON-pointer claim not reanalysed'

overlaps = []
for i, left in enumerate(records):
    for right in records[i + 1:]:
        hits = []
        for a in left['sourceRanges']:
            for b in right['sourceRanges']:
                if (a['sourcePath'], a['sourceHash']) != (b['sourcePath'], b['sourceHash']):
                    continue
                start = max(a['byteRange']['start'], b['byteRange']['start'])
                end = min(a['byteRange']['endExclusive'], b['byteRange']['endExclusive'])
                if start < end:
                    hits.append((a['sourcePath'], start, end))
        if hits:
            overlaps.append({'left': left['id'], 'right': right['id'],
                             'sharedRanges': [{'sourcePath': p, 'byteRange': {'start': s, 'endExclusive': e}} for p, s, e in sorted(set(hits))],
                             'disposition': 'requires ownership review; shared source coordinates do not prove equivalent or distinct complete modules'})

state_path = OUT / 'analysis-state.json'
before = state_path.read_bytes()
assert not (WORK / 'state-before.json').exists(), 'Do not replace an earlier publication attempt.'
(WORK / 'state-before.json').write_bytes(before)
state = json.loads(before)
for name in ['feature-scope-v26.json', 'feature-scope-v24-scenarios.json', 'restoration-coverage-v17.json',
             'restoration-current-ordering-v1.json', 'analysis-stage-decisions-v4.json',
             'dependency-investigation-actions-v1.json']:
    read(name)
plan_pin = pin(ROOT / 'docs/reverse-engineering/analysis-plan.md')

catalog = {
    'schemaVersion': 1, 'baselineId': BASE, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
    'status': 'bounded-existing-proposal-inventory; full module analysis incomplete',
    'scope': 'Fixed seven saved proposal families. Does not discover all proposals, recover original modules or establish the whole-client module denominator.',
    'plan': plan_pin,
    'requiredFields': ['responsibility', 'environment', 'mode', 'sourceRanges', 'imports', 'exports', 'sharedState', 'sideEffects', 'thirdPartyDependencies', 'proposedPath'],
    'records': records,
    'sourceOverlapReviews': overlaps,
    'publishedFileInventory': {'source': inputs[str(OUT / 'modules.json')], 'records': len(modules),
                               'disposition': 'Unchanged published-file inventory; these 438 records are not recovered logical modules.'},
    'currentFeatureTaskOwnership': {'featureLedger': inputs[str(OUT / 'feature-scope-v26.json')],
                                    'coverage': inputs[str(OUT / 'restoration-coverage-v17.json')],
                                    'status': '373 features / 48 tasks unchanged; module-to-task ownership join remains pending'},
    'dependencyInvestigation': inputs[str(OUT / 'dependency-investigation-actions-v1.json')],
    'counts': {'proposalRecords': 38, 'proposalFamilies': 7, 'sourceFilesIdentityChecked': len(source_bytes),
               'recordSourceRangesIdentityChecked': span_count, 'sourceOverlapPairs': len(overlaps),
               'newOriginalProgramParses': 0, 'newReaRuns': 0, 'newModelSubmissions': 0,
               'newOriginalClientLaunches': 0, 'newProductScenarioPasses': 0,
               'newFeatureDefinitions': 0, 'newThirdPartyImplementations': 0, 'newClientImplementation': 0},
    'limits': [
        '38 is a count of proposal records, not 38 distinct recovered original modules or a whole-client denominator.',
        'Per-field source references document bounded contracts/proposals; complete logical imports/exports/state/effects and feature/task ownership remain open.',
        'Main-or-shared published-file classification is not actual process selection; proposed paths do not establish runtime placement.',
        'App-host historical indirect input pin drift remains unresolved; direct saved proposal pins and inherited source ranges are checked without revalidating the old entire provenance graph.',
        'Existing package version/modification/native ABI findings and runtime limitations remain unchanged; no lock or clean rebuild is claimed.',
        'No active application, personal settings/history/credentials or model service is accessed.',
    ],
    'nextAction': {'issueId': 'SD-06',
                   'question': 'Resolve source-overlap ownership and join these proposed responsibilities to the current 48 restoration tasks before choosing implementation file boundaries.',
                   'fixedInput': 'This 38-record view, current task/feature ownership, and existing contract metadata; no new feature discovery.',
                   'closure': 'Each overlap is explicitly split/refined/retained unresolved with evidence; each proposal has evidenced task ownership or a specific unresolved join. Do not merge solely by file or path name.',
                   'authorization': 'Existing-artifact analysis/design only; no client/model/runtime activity.'},
    'fullAnalysisCompleted': False, 'implementationReady': False, 'inputPins': list(inputs.values()),
}


def publish(name, data):
    path = OUT / name
    assert not path.exists(), f'Immutable publication already exists: {path}'
    if not isinstance(data, str):
        data = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    path.write_text(data)
    path.chmod(0o444)
    return pin(path)


catalog_pin = publish('logical-module-inventory-v1.json', catalog)
md = ['# 已有逻辑模块建议统一清单 v1', '',
      '本次将七组既有建议的 38 条记录整理为统一视图。38 是建议记录数；存在源码重叠，不能称为 38 个独立恢复模块。', '',
      '每条记录保留职责、来源环境与拟议运行位置、模式、源码范围、输入接口、输出接口、共享状态、副作用、第三方边界及拟议路径。完整导入/导出闭包和实际运行结果仍未知。', '',
      '438 条发布文件记录保持原样。373 项功能、48 组恢复任务和 1216 条未执行场景规格保持原样。没有生成客户端代码或第三方实现。', '',
      '| 建议记录 | 职责 | 拟议路径 |', '| --- | --- | --- |']
for r in records:
    md.append('| ' + r['id'] + ' | ' + r['responsibility']['value'].replace('|', '/') + ' | `' + r['proposedPath']['value'] + '` |')
md += ['', f'已列出 {len(overlaps)} 组具有重叠来源范围的建议，逐组关系见 JSON 的 `sourceOverlapReviews`。范围相交只证明证据重叠，不能自动合并模块。', '',
       '明确保留的差异：RWC-FETCH 的既有拟议 main 路径与 renderer 来源分类需要复核；项目领域和 chunk 传输跨多个运行环境，应区分共享合同与各进程适配器；host-provided RPC 的最新条件化 main 来源关系已引用，实际实例仍未知。', '',
       '第三方处理沿用包导入、原生运行时适配器和未知 helper 的边界。未把依赖注入对象一律判为第三方；未宣称版本锁定、原生兼容或完整可重建。App-host 旧间接输入 pin 漂移仍保留为限制。', '',
       '下一项工作是处理清单内的来源重叠，并将职责关联到现有恢复任务。当前只关闭“这些既有建议缺少统一字段视图”这一子项；原计划九项完成条件不变，整体分析未完成。', '']
summary_pin = publish('logical-module-inventory-v1.md', '\n'.join(md))
buf = io.StringIO()
writer = csv.writer(buf)
writer.writerow(['id', 'originFamily', 'responsibility', 'sourceFiles', 'intendedRuntime', 'mode', 'proposedPath', 'sourceRangeCount', 'runtimeValidated'])
for r in records:
    writer.writerow([r['id'], r['originFamily'], r['responsibility']['value'], ';'.join(v['sourcePath'] for v in r['environment']['sourceFiles']), r['environment']['intendedRuntime'], 'unknown', r['proposedPath']['value'], len(r['sourceRanges']), False])
csv_pin = publish('logical-module-inventory-v1.csv', buf.getvalue())
evidence = []
for i, r in enumerate(records):
    evidence.append({'id': f'LOGICAL-MODULE-V1-{i+1:03}', 'baselineId': BASE,
                     'claim': f"Existing {r['originFamily']} proposal is retained as {r['id']} with explicit bounded fields and unknown closure; not a recovered original module.",
                     'sourcePath': r['origin']['path'], 'sourceHash': r['origin']['sha256'],
                     'locator': {'kind': 'json-pointer', 'jsonPointer': r['origin']['jsonPointer']},
                     'method': 'existing-artifact proposal normalization; inherited range identity verification only',
                     'confidence': 'inferred', 'verificationStatus': 'proposal-record-reviewed; runtime-and-complete-module-closure-unverified'})
ev_pin = publish('logical-module-inventory-v1-evidence.jsonl', ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in evidence))
state['logicalModuleInventory'] = {'catalog': catalog_pin, 'summary': summary_pin, 'csv': csv_pin,
                                    'evidence': ev_pin, 'counts': catalog['counts'],
                                    'qualification': catalog['scope'], 'fullAnalysisCompleted': False}
state['stageDecisions']['nextAction'] = catalog['nextAction']
state['updatedAtUtc'] = datetime.now(timezone.utc).isoformat()
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
(WORK / 'publication.json').write_text(json.dumps({'catalog': catalog_pin, 'summary': summary_pin,
                                                   'csv': csv_pin, 'evidence': ev_pin,
                                                   'producer': pin(Path(__file__))}, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'published': catalog_pin, 'counts': catalog['counts']}, ensure_ascii=False))
