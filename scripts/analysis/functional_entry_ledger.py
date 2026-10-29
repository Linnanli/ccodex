#!/usr/bin/env python3
"""Join frozen analysis contracts by provenance, never by labels or URLs.

Reads JSON/JSONL artifacts only. It neither parses nor executes target code.
The ledger is an entry/contract census, not an application feature census.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pointer(root, path):
    node = root
    for part in path.split('/')[1:]:
        key = part.replace('~1', '/').replace('~0', '~')
        node = node[int(key)] if isinstance(node, list) else node[key]
    return node


def walk(node, path=''):
    yield path, node
    if isinstance(node, dict):
        for key, value in node.items():
            escaped = key.replace('~', '~0').replace('/', '~1')
            yield from walk(value, path + '/' + escaped)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk(value, path + '/' + str(index))


class Ledger:
    def __init__(self, root):
        self.root = root
        self.inputs, self.docs, self.artifacts = {}, {}, {}
        self.evidence, self.used_evidence = {}, set()
        self.entries, self.support, self.links, self.deferred = [], [], [], []
        self.denominators = []
        self.baseline = self.read('baseline', '.analysis-local/current-baseline.json')['baselineId']
        manifest = self.read('manifest', f'analysis/{self.baseline}/files.json')
        assert manifest['baselineId'] == self.baseline
        self.source_manifest = {f['sourcePath']: f for f in manifest['archiveFiles']}

    def read(self, key, path, jsonl=False):
        raw = (self.root / path).read_bytes()
        self.inputs[path] = digest(raw)
        if jsonl:
            lines = raw.splitlines()
            assert all(line.strip() for line in lines), 'JSONL catalog requires nonempty physical lines for exact journal locators'
            doc = [json.loads(line) for line in lines]
        else:
            doc = json.loads(raw)
        self.docs[key] = doc
        self.artifacts[key] = {'artifactId': key, 'path': path, 'sha256': digest(raw),
                               'bytes': len(raw), 'format': 'jsonl' if jsonl else 'json'}
        if jsonl:
            for index, record in enumerate(doc):
                assert record['baselineId'] == self.baseline
                assert record['id'] not in self.evidence
                self.evidence[record['id']] = (key, index, record)
        elif isinstance(doc, dict) and 'baselineId' in doc and hasattr(self, 'baseline'):
            assert doc['baselineId'] == self.baseline
        return doc

    def reference(self, artifact, path):
        # Resolve here so every stored source pointer has already been checked.
        pointer(self.docs[artifact], path)
        return {'artifactId': artifact, 'path': self.artifacts[artifact]['path'],
                'sha256': self.artifacts[artifact]['sha256'], 'jsonPointer': path}

    def refs(self, raw):
        refs = sorted({value for _, value in walk(raw)
                       if isinstance(value, str) and value in self.evidence})
        self.used_evidence.update(refs)
        return refs

    def coordinates(self, evidence_id):
        artifact, index, record = self.evidence[evidence_id]
        self.used_evidence.add(evidence_id)
        source = self.source_manifest[record['sourcePath']]
        assert source['sha256'] == record['sourceHash']
        span = record['locator']
        assert span['kind'] == 'byte-range'
        assert 0 <= span['start'] <= span['endExclusive'] <= source['bytes']
        return {'sourcePath': record['sourcePath'], 'sourceHash': record['sourceHash'],
                'byteRange': span, 'spanHash': record.get('spanHash'),
                'spanHashStatus': 'present-in-frozen-evidence' if record.get('spanHash') else 'absent-in-lexical-discovery',
                'archiveByteOffset': source.get('archiveByteOffset'),
                'evidenceId': evidence_id}

    def stable_id(self, category, artifact, path):
        payload = [self.baseline, category, self.artifacts[artifact]['sha256'], path]
        return category + ':' + digest(json.dumps(payload, separators=(',', ':')).encode())[:24]

    def targets(self, raw, artifact, origin_pointer):
        """Preserve resolved target definitions and explicit uncertain call boundaries.

        Source-local targets are not operation identities. Infrastructure callees
        and component bindings are retained without being used for feature merges.
        """
        targets, unresolved = [], []
        for relative, value in walk(raw):
            if not isinstance(value, dict):
                continue
            status = value.get('status', '')
            if not isinstance(status, str):
                continue
            is_target = ('expression' in value or 'calls' in value or 'terminal' in value) and status
            if not is_target:
                continue
            definition_ids = [value[k] for k in ['callableDefinitionEvidenceId', 'definitionEvidenceId']
                              if value.get(k) in self.evidence]
            terminal = value.get('terminal') or {}
            definition_ids += [d['evidenceId'] for d in terminal.get('valueDefinitions', [])
                               if d.get('evidenceId') in self.evidence]
            item = {'status': status, 'expression': value.get('expression'),
                    'sourceReference': self.reference(artifact, origin_pointer + relative),
                    'evidenceIds': self.refs({k: v for k, v in value.items()
                                              if k not in ['calls', 'calleeTrace', 'children']}),
                    'definitionCoordinates': [self.coordinates(e) for e in dict.fromkeys(definition_ids)]}
            if value.get('bindingId'):
                item['bindingId'] = value['bindingId']
            if value.get('rootBinding'):
                item['receiverBinding'] = {k: value['rootBinding'].get(k) for k in
                                          ['status', 'name', 'kind', 'moduleSpecifier', 'parameterPropertyPath']}
            if value.get('definitionRange'):
                # Host legacy AST binding uses full source hash + exact range,
                # without a separate definition-evidence record.
                host = self.docs['host']
                span = value['definitionRange']
                assert span['endExclusive'] <= self.source_manifest[host['sourcePath']]['bytes']
                item['definitionCoordinates'].append({'sourcePath': host['sourcePath'],
                    'sourceHash': host['sourceHash'], 'byteRange': span,
                    'spanHash': None, 'spanHashStatus': 'definition-range-only-in-frozen-contract'})
            if item['definitionCoordinates']:
                item['bindingMeaning'] = 'source target only; operation/payload/effect equivalence not established'
                targets.append(item)
            uncertain = any(s in status for s in ['unknown', 'unresolved', 'dynamic', 'unbound'])
            if uncertain:
                unresolved.append({'kind': 'unresolved-binding-or-value', 'status': status,
                    'expression': value.get('expression'),
                    'reason': value.get('unresolvedReason') or value.get('registryBindingStatus') or value.get('reason'),
                    'receiverBinding': item.get('receiverBinding'),
                    'sourceReference': item['sourceReference'], 'evidenceIds': item['evidenceIds']})
        return targets, unresolved

    def entry(self, group, kind, artifact, path, evidence_id, label=None, entry_id=None,
              discovery='static-contract', target_raw=None):
        raw = pointer(self.docs[artifact], path)
        targets, unknown = self.targets(raw if target_raw is None else target_raw, artifact, path)
        value = {'entryId': entry_id or self.stable_id(kind, artifact, path),
                 'denominatorGroup': group, 'entryKind': kind, 'sourceArtifact': self.reference(artifact, path),
                 'primaryEvidenceId': evidence_id, 'evidenceIds': self.refs(raw),
                 'sourceCoordinates': self.coordinates(evidence_id), 'displayLabel': label,
                 'displayLabelMeaning': 'display only; never used as an identity or merge key',
                 'discoveryClass': discovery, 'boundTargets': targets,
                 'unresolvedBoundaries': unknown,
                 'conditionEvidenceIds': sorted({v for p, v in walk(raw)
                     if isinstance(v, str) and v in self.evidence and
                     ('conditionEvidenceId' in p or 'completeControlEvidenceId' in p)}),
                 'mode': 'unknown', 'runtimeStatus': 'not-verified-by-this-ledger',
                 'featureId': None, 'featureAssociationStatus': 'unassigned'}
        value['unresolvedBoundaries'] += [
            {'kind': 'domain-operation-contract', 'reason': 'payload/results/state effects and user workflow not mapped to a reviewed feature'},
            {'kind': 'mode-and-runtime', 'reason': 'Codex/Work/ChatGPT reachability and behavior are not resolved by label or source registration'}]
        if discovery == 'lexical-candidate':
            value['boundTargets'] = []
            value['unresolvedBoundaries'].insert(0, {'kind': 'candidate-registration-or-call-binding',
                'reason': 'Lexical discovery has no complete registration/callee/payload contract; keep as candidate'})
        self.entries.append(value)
        return value

    def support_node(self, kind, artifact, path, evidence_id, node_id=None, extra=None):
        node = {'nodeId': node_id or self.stable_id(kind, artifact, path), 'kind': kind,
                'sourceArtifact': self.reference(artifact, path), 'primaryEvidenceId': evidence_id,
                'sourceCoordinates': self.coordinates(evidence_id),
                'evidenceIds': self.refs(pointer(self.docs[artifact], path)),
                'notAdditionalEntry': True, 'featureId': None}
        node.update(extra or {})
        self.support.append(node)
        return node

    def link(self, source, target, relation, witnesses, evidence_ids, explanation,
             equivalence=False):
        payload = [source, target, relation, witnesses]
        link = {'linkId': 'LINK:' + digest(json.dumps(payload, sort_keys=True).encode())[:24],
                'from': source, 'to': target, 'relation': relation,
                'reviewStatus': 'confirmed-static-contract-link',
                'verificationBasis': 'existing frozen contract reference/binding reconciled; target code not reanalyzed',
                'runtimeReachability': 'unknown',
                'operationEquivalence': False, 'featureMergeAuthorized': False,
                'handlerIdentity': equivalence, 'witnesses': witnesses,
                'evidenceIds': sorted(set(evidence_ids)), 'explanation': explanation}
        self.used_evidence.update(link['evidenceIds'])
        self.links.append(link)
        return link

    def denominator(self, group, role, count, definition, coverage, caveats=None):
        self.denominators.append({'groupId': group, 'role': role, 'recordCount': count,
            'definition': definition, 'coverage': coverage, 'caveats': caveats or []})

    def load(self):
        paths = {'route': '.analysis-local/feature-work/route-contracts.json',
                 'host': '.analysis-local/feature-work/host-message-contracts.json',
                 'menu': '.analysis-local/entry-work/menu-command-contracts.json',
                 'settings': '.analysis-local/feature-work/settings.json',
                 'rpc': '.analysis-local/feature-work/app-server-methods.json',
                 'ipc': '.analysis-local/feature-work/ipc-channels.json',
                 'ipc_contract': '.analysis-local/feature-work/ipc-transport-contracts.json'}
        for key, path in paths.items():
            self.read(key, path)
        for key, path in {'route-evidence': '.analysis-local/feature-work/route-contract-evidence.jsonl',
                          'host-evidence': '.analysis-local/feature-work/host-message-contract-evidence.jsonl',
                          'menu-evidence': '.analysis-local/entry-work/menu-command-evidence.jsonl',
                          'lexical-evidence': '.analysis-local/feature-work/evidence.jsonl'}.items():
            self.read(key, path, jsonl=True)
        reviews = self.root / '.analysis-local/entry-ledger-work/reviewed-links.json'
        if reviews.exists():
            self.read('reviewed-links', str(reviews.relative_to(self.root)))

    def build(self):
        route, menu, host = self.docs['route'], self.docs['menu'], self.docs['host']
        route_entries, route_consumers = {}, {}
        for index, raw in enumerate(route['registrations']):
            e = self.entry('route-constructions', 'route-construction', 'route', f'/registrations/{index}',
                raw['evidenceId'], (raw.get('path') or {}).get('value'), entry_id=raw['id'])
            e['routeDetails'] = {'pathStatus': (raw.get('path') or {}).get('status'),
                'pathless': raw.get('path') is None, 'isIndex': raw.get('index'),
                'staticMapInstanceCount': len(raw.get('staticMapInstances', [])),
                'registrationStatus': raw['registrationStatus']}
            route_entries[raw['id']] = e
            for n, instance in enumerate(raw.get('staticMapInstances', [])):
                ids = self.refs(instance)
                node = self.support_node('route-static-map-instance', 'route',
                    f'/registrations/{index}/staticMapInstances/{n}', raw['evidenceId'],
                    extra={'templateEntryId': raw['id'], 'displayPath': (instance.get('path') or {}).get('value'),
                           'coordinateMeaning': 'source construction template, not independently generated source code',
                           'sourceConstructionEntryCount': 0})
                self.link(node['nodeId'], e['entryId'], 'static-instance-of-source-template',
                    [node['sourceArtifact']], ids + [raw['evidenceId']],
                    'Saved AST finite-map expansion; an instance is not another source construction.')
        self.denominator('route-constructions', 'primary-entry', len(route_entries),
            'Actual Route element-construction expressions with resolved Route import/export identity in the two requested chunks.',
            'app-initial:170; app-primary:0;170 have saved conversion-contract membership; actual runtime reachability unknown.',
            ['146 path-bearing;24 pathless;8 index (overlap with pathless).',
             '143 fixed-path constructions +1 statically resolved literal-return helper =144 resolved-path constructions;2 map templates expand52 instances.',
             'Registration construction, navigation target, runtime route instance and feature are different denominators.'])
        for index, raw in enumerate(route['conversionConsumers']):
            e = self.entry('route-conversion-consumers', 'route-conversion-consumer', 'route',
                f'/conversionConsumers/{index}', raw['evidenceId'], raw['kind'], entry_id=raw['id'])
            route_consumers[raw['id']] = e
        self.denominator('route-conversion-consumers', 'auxiliary-entry', len(route_consumers),
            'Saved bound createRoutesFromElements conversion calls.', 'Three saved calls; static consumers, not UI features.')
        for index, raw in enumerate(route['navigationTargets']):
            self.entry('navigate-component-targets', 'navigate-component-target', 'route',
                f'/navigationTargets/{index}', raw['evidenceId'], raw['target'].get('value'))
        self.denominator('navigate-component-targets', 'auxiliary-entry', len(route['navigationTargets']),
            'Actual Navigate component constructions with resolved Navigate import/export identity.',
            '47 saved constructions; navigation URLs are not matched to Route paths for operation/feature links.')
        for index, raw in enumerate(route['registrations']):
            e = route_entries[raw['id']]
            for parent_id in raw['parentRouteIds']:
                parent = route_entries[parent_id]
                self.link(e['entryId'], parent_id, 'route-parent-registration',
                    [self.reference('route', f'/registrations/{index}/parentRouteIds')],
                    [e['primaryEvidenceId'], parent['primaryEvidenceId']],
                    'Saved AST route-element nesting; no path/name matching and no operation equivalence.')
            for consumer_id in raw['conversionConsumerIds']:
                consumer = route_consumers[consumer_id]
                assert raw['id'] in pointer(self.docs['route'], consumer['sourceArtifact']['jsonPointer'])['registrationIds']
                self.link(e['entryId'], consumer_id, 'route-registration-conversion-consumer',
                    [self.reference('route', f'/registrations/{index}/conversionConsumerIds'),
                     self.reference('route', consumer['sourceArtifact']['jsonPointer'] + '/registrationIds')],
                    [e['primaryEvidenceId'], consumer['primaryEvidenceId']],
                    'Both frozen references identify source registration/conversion-contract membership. This is API/construction applicability, not proof of runtime route reachability or business operation. No URL matching.')

        for contract in menu['contractRecordIndex']:
            raw = pointer(menu, contract['jsonPointer'])
            assert raw['contractId'] == contract['contractId']
            label = raw.get('id') or raw.get('api') or raw.get('event') or raw.get('name')
            if not label:
                label = (raw.get('values', {}).get('label') or {}).get('value')
            self.entry('menu-contract-records', contract['kind'], 'menu', contract['jsonPointer'],
                       contract['primaryEvidenceId'], label, entry_id=contract['contractId'])
        # These are explicit frozen source-dataflow references, checked in both
        # directions. The 255 paths reduce to229 endpoint pairs; neither command
        # names nor URL equality is involved in this reconciliation.
        for index, item in enumerate(menu['nativeMenuItems']):
            uses_by_registration = defaultdict(list)
            for use_index, use in enumerate(item['registrationUses']):
                uses_by_registration[use['registrationIndex']].append((use_index, use))
            for registration_index, uses in uses_by_registration.items():
                registration = menu['nativeMenuRegistrations'][registration_index]
                assert item['registrationReachability'] == 'bound-source-dataflow'
                assert index in registration['reachableItemSchemaIndices']
                witnesses = [self.reference('menu', f'/nativeMenuItems/{index}/registrationUses/{i}')
                             for i, _ in uses]
                witnesses += [self.reference('menu', f'/nativeMenuRegistrations/{registration_index}/reachableItemSchemaIndices')]
                evidence_ids = self.refs([use for _, use in uses])
                evidence_ids += [item['completeItemEvidenceId'], registration['callEvidenceId']]
                self.link(item['contractId'], registration['contractId'], 'schema-registration-dataflow',
                    witnesses, evidence_ids,
                    'Reciprocal saved registrationIndex/reachableItemSchemaIndices with bound-source-dataflow; every recorded path and branch is retained by pointer. Not handler or feature equivalence.')
        self.denominator('menu-contract-records', 'primary-entry', len(menu['contractRecordIndex']),
            'All411 frozen contractRecordIndex rows, retaining their distinct entryKind and stable contractId.',
            'Complete-main API registrations/selected factory scopes; metadata from bound src registry; renderer7 selected function fragments.',
            ['Mixed contract denominator:182 metadata instances are not182 handler registrations.',
             '130 native schema constructions and26 generator option sites are source sites, not runtime menu item counts.',
             '31 native API calls include construction, installation and mutation.',
             'Renderer6 command-registration and10 subscription candidates retain original outer-binding unknown; whole-renderer coverage unknown.'])

        for index, raw in enumerate(host['groups']):
            self.support_node('host-effective-handler-group', 'host', f'/groups/{index}', raw['handlerEvidenceId'],
                node_id=f'HOST-HANDLER-GROUP-{index:03d}', extra={'caseCount': len(raw['caseIndices']),
                    'caseIndices': raw['caseIndices'], 'noOp': raw['noOp'],
                    'sharedEmptyLabelFallthrough': raw['hasSharedEmptyLabelFallthrough']})
        for index, raw in enumerate(host['cases']):
            e = self.entry('host-top-level-message-cases', 'host-top-level-message-case', 'host', f'/cases/{index}',
                raw['clauseEvidenceId'], raw['label'].get('value'))
            e['dispatchDetails'] = {k: raw[k] for k in ['emptyOwnHandler', 'noOpOwnHandler',
                'effectiveHandlerNoOp', 'topLevelTailExit', 'groupIndex', 'effectiveHandlerCaseIndex']}
            e['effectiveHandlerCoordinates'] = self.coordinates(raw['effectiveHandlerEvidenceId'])
            group = host['groups'][raw['groupIndex']]
            assert index in group['caseIndices']
            assert raw['effectiveHandlerEvidenceId'] == group['handlerEvidenceId']
            self.link(e['entryId'], f"HOST-HANDLER-GROUP-{raw['groupIndex']:03d}",
                'dispatch-case-effective-handler',
                [self.reference('host', f'/cases/{index}/effectiveHandlerEvidenceId'),
                 self.reference('host', f"/groups/{raw['groupIndex']}")],
                [raw['clauseEvidenceId'], raw['effectiveHandlerEvidenceId'], group['fullGroupEvidenceId']],
                'Saved switch-case control-flow group including explicit fallthrough; same body does not establish same payload/effect/feature.',
                equivalence=len(group['caseIndices']) > 1)
        self.denominator('host-top-level-message-cases', 'primary-entry', len(host['cases']),
            'Top-level SwitchCase clauses of main MMe async handleMessage(e,t), switch(t.type).',
            '143 clauses/143 literal labels in the saved complete switch;112 effective handler groups.',
            ['Old171 lexical labels include28 nested browser-sidebar-command switch labels, excluded here.',
             '6 groups share empty-label fallthrough;33 labels have effective no-op handlers.',
             'Handler groups are support nodes; not112 additional entries or confirmed features.'])

        for index, raw in enumerate(self.docs['settings']):
            self.entry('settings-lexical-candidates', 'settings-section-lexical-candidate', 'settings',
                f'/{index}', raw['evidenceId'], raw['section'], discovery='lexical-candidate')
        self.denominator('settings-lexical-candidates', 'primary-entry', len(self.docs['settings']),
            'Saved lexical section candidates in settings.json, each associated with one lexical evidence match.',
            '53 discovered candidates; registry/factory binding and whole-settings denominator are unresolved.',
            ['Not joined to50 settings Route map instances by section name or path.'])
        direct = 0
        for index, raw in enumerate(self.docs['rpc']):
            if raw['callForm'] == 'sendAppServerRequest' and raw['protocolClass'] == 'app-server':
                e = self.entry('direct-app-server-call-candidates', 'app-server-direct-call-lexical-candidate',
                    'rpc', f'/{index}', raw['evidenceId'], raw['method'], discovery='lexical-candidate')
                e['protocolCandidate'] = {'callForm': raw['callForm'], 'method': raw['method'],
                                          'classification': 'saved-lexical-call-form', 'schema': raw['schema']}
                direct += 1
            else:
                self.deferred.append({'candidateId': self.stable_id('unknown-request-wrapper', 'rpc', f'/{index}'),
                    'groupId': 'unknown-request-wrapper-candidates', 'sourceArtifact': self.reference('rpc', f'/{index}'),
                    'sourceCoordinates': self.coordinates(raw['evidenceId']),
                    'evidenceIds': self.refs(raw), 'displayLabel': raw['method'],
                    'callForm': raw['callForm'], 'protocolClass': raw['protocolClass'],
                    'reason': 'Generic sendRequest wrapper has no confirmed app-server protocol binding; not counted as a direct app-server entry.',
                    'featureId': None})
        self.denominator('direct-app-server-call-candidates', 'primary-entry', direct,
            'Only saved callForm=sendAppServerRequest and protocolClass=app-server lexical rows.',
            '91 callsite candidates/52 distinct method literals in the selected-source discovery.',
            ['Method spelling alone does not resolve actual receiver binding, handler, payload, results or mode.'])
        self.denominator('unknown-request-wrapper-candidates', 'deferred-discovery', len(self.deferred),
            'Saved generic sendRequest lexical rows with unknown wrapper/protocol.',
            '337 rows retained separately with provenance; not added to91 direct calls.')
        for index, raw in enumerate(self.docs['ipc']):
            self.entry('ipc-source-channel-candidates', 'ipc-source-channel-lexical-candidate',
                'ipc', f'/{index}', raw['evidenceId'], raw['channel'], discovery='lexical-candidate')
        self.denominator('ipc-source-channel-candidates', 'auxiliary-entry', len(self.docs['ipc']),
            'Saved explicit IPC source-file/channel pairs (one representative lexical evidence match per pair).',
            '50 source/channel pairs;25 distinct channel literals; not all invocation/registration callsites.',
            ['No joins by channel spelling; direction/consumer bindings require reviewed protocol links.'])
        for index, raw in enumerate(self.docs['ipc_contract']):
            self.support_node('ipc-transport-analysis-note', 'ipc_contract', f'/{index}', raw['evidenceId'],
                extra={'displayLabel': raw['id'], 'analysisStatus': raw['verificationStatus'],
                       'meaning': 'curated static transport note; no automatically inferred source/channel or operation link'})
        self.denominator('host-effective-handler-groups', 'support-node', len(host['groups']),
            'Already saved effective switch-case handler/fallthrough groups.',
            '112 support nodes overlap143 case entries and are not extra source entries.')
        self.denominator('route-static-map-instances', 'support-node',
            sum(len(r['staticMapInstances']) for r in route['registrations']),
            'Saved finite-map expansions of two Route construction templates.',
            '52 instances overlap2 of170 source constructions; not extra registrations.')
        self.denominator('ipc-transport-analysis-notes', 'support-node', len(self.docs['ipc_contract']),
            'Saved curated static IPC transport summaries, not a registration census.',
            '12 support notes; no name/channel-based entry association.')
        self.reviewed_links()

    def reviewed_links(self):
        # Child review format is intentionally explicit, and imported only once
        # after provenance and endpoint validation. No cross-artifact name joins.
        review = self.docs.get('reviewed-links')
        if review is None:
            return
        # Adapt this list only to a reviewed format; fail on missing endpoints.
        for index, link in enumerate(review.get('confirmedLinks', [])):
            endpoints = [link['from'], link['to']]
            for endpoint in endpoints:
                assert endpoint['artifactPath'] == self.artifacts['menu']['path']
                assert endpoint['artifactSha256'] == self.artifacts['menu']['sha256']
                resolved = pointer(self.docs['menu'], endpoint['jsonPointer'])
                assert resolved['contractId'] == endpoint['contractId']
                assert all(e in self.evidence for e in endpoint['evidenceIds'])
                for reference_pointer in endpoint['referencePointers']:
                    pointer(self.docs['menu'], reference_pointer)
            source, target = [e['contractId'] for e in endpoints]
            relation = link['kind']
            if relation == 'schema-registration-dataflow':
                matches = [l for l in self.links if l['from'] == source and l['to'] == target
                           and l['relation'] == relation]
                assert len(matches) == 1
                matches[0]['independentReviewReference'] = self.reference('reviewed-links', f'/confirmedLinks/{index}')
                self.used_evidence.update(link['evidenceIds'])
                continue
            assert relation == 'shares-callback-definition'
            definition_id = link['basis']['definitionEvidenceId']
            for endpoint in endpoints:
                resolved = pointer(self.docs['menu'], endpoint['jsonPointer'])
                assert resolved['callback']['definitionEvidenceId'] == definition_id
            witnesses = [self.reference('reviewed-links', f'/confirmedLinks/{index}')]
            witnesses += [self.reference('menu', q) for endpoint in endpoints for q in endpoint['referencePointers']]
            added = self.link(source, target, relation, witnesses, link['evidenceIds'],
                link['basis']['rule'], equivalence=True)
            added['conditions'] = link['conditions']
            added['unknowns'] = link['unknowns']
            added['handlerDefinitionCoordinates'] = self.coordinates(definition_id)

    def finish(self):
        ids = {e['entryId'] for e in self.entries}
        support_ids = {e['nodeId'] for e in self.support}
        assert len(ids) == len(self.entries)
        assert len(support_ids) == len(self.support)
        assert not ids.intersection(support_ids)
        link_ids = set()
        for link in self.links:
            assert link['from'] in ids | support_ids and link['to'] in ids | support_ids
            assert link['linkId'] not in link_ids
            link_ids.add(link['linkId'])
            assert all(e in self.evidence for e in link['evidenceIds'])
        incident = defaultdict(list)
        identity_incident = defaultdict(list)
        for link in self.links:
            for endpoint in [link['from'], link['to']]:
                if endpoint in ids:
                    incident[endpoint].append(link['linkId'])
                    if link['handlerIdentity']:
                        identity_incident[endpoint].append(link['linkId'])
        for e in self.entries:
            e['reviewedContractLinkIds'] = incident[e['entryId']]
            e['reviewedHandlerIdentityLinkIds'] = identity_incident[e['entryId']]
            e['contractAssociationStatus'] = 'has-reviewed-contract-links' if e['reviewedContractLinkIds'] else 'no-reviewed-contract-links'
        # Validate every source artifact pointer and evidence reference introduced
        # anywhere in the assembled ledger before publishing our local outputs.
        referenced_evidence = []
        for evidence_id in sorted(self.used_evidence):
            artifact, index, evidence = self.evidence[evidence_id]
            self.coordinates(evidence_id)
            referenced_evidence.append({'evidenceId': evidence_id, 'evidenceJournal': {
                'artifactId': artifact, 'path': self.artifacts[artifact]['path'],
                'sha256': self.artifacts[artifact]['sha256'], 'line': index + 1,
                'locatorConvention': 'one-based JSONL physical line'},
                'sourceCoordinates': self.coordinates(evidence_id),
                'method': evidence['method'], 'confidence': evidence['confidence'],
                'verificationStatus': evidence['verificationStatus']})
        group_counts = Counter(e['denominatorGroup'] for e in self.entries)
        for d in self.denominators:
            if d['role'] in ['primary-entry', 'auxiliary-entry']:
                assert group_counts[d['groupId']] == d['recordCount']
        primary = {d['groupId'] for d in self.denominators if d['role'] == 'primary-entry'}
        primary_entries = [e for e in self.entries if e['denominatorGroup'] in primary]
        category_links = Counter(l['relation'] for l in self.links)
        summary = {'baselineId': self.baseline, 'entryRecords': len(self.entries),
            'primaryEntryRecords': len(primary_entries),
            'auxiliaryEntryRecords': len(self.entries) - len(primary_entries),
            'supportNodes': len(self.support), 'deferredCandidateRecords': len(self.deferred),
            'byDenominator': dict(group_counts),
            'associationByDenominator': {group: {
                'recordCount': count,
                'withReviewedContractLinks': sum(bool(e['reviewedContractLinkIds']) for e in self.entries if e['denominatorGroup'] == group),
                'withoutReviewedContractLinks': sum(not e['reviewedContractLinkIds'] for e in self.entries if e['denominatorGroup'] == group),
                'withReviewedHandlerIdentityLinks': sum(bool(e['reviewedHandlerIdentityLinkIds']) for e in self.entries if e['denominatorGroup'] == group),
                'withReviewedOperationEquivalenceLinks': 0,
                'mappedToConfirmedFeature': 0}
                for group, count in group_counts.items()},
            'menuKinds': dict(Counter(e['entryKind'] for e in self.entries if e['denominatorGroup'] == 'menu-contract-records')),
            'reviewedLinks': len(self.links), 'linksByRelation': dict(category_links),
            'entriesWithReviewedContractLinks': sum(bool(e['reviewedContractLinkIds']) for e in self.entries),
            'entriesWithoutReviewedContractLinks': sum(not e['reviewedContractLinkIds'] for e in self.entries),
            'primaryEntriesWithReviewedContractLinks': sum(bool(e['reviewedContractLinkIds']) for e in primary_entries),
            'primaryEntriesWithoutReviewedContractLinks': sum(not e['reviewedContractLinkIds'] for e in primary_entries),
            'entriesWithReviewedHandlerIdentityLinks': sum(bool(e['reviewedHandlerIdentityLinkIds']) for e in self.entries),
            'entriesWithReviewedOperationEquivalenceLinks': 0,
            'crossArtifactConfirmedHandlerIdentityLinks': 0,
            'crossArtifactIdentityReviewScope': 'Saved119 host call-definition ranges and114 route terminal valueDefinition records versus menu411 entry index; scoped comparison only, not an exhaustive absence proof.',
            'entriesMappedToConfirmedFeature': 0, 'entriesUnmappedToFeature': len(self.entries),
            'confirmedFeatures': 0, 'featureCensusDenominator': 'unknown',
            'ledgerEvidenceReferences': len(referenced_evidence),
            'sourceArtifactCount': len(self.artifacts), 'modeResolvedEntryCount': 0,
            'runtimeVerifiedByLedger': 0}
        for path, sha in self.inputs.items():
            assert digest((self.root / path).read_bytes()) == sha, f'Frozen input changed: {path}'
        result = {'schemaVersion': 1, 'baselineId': self.baseline,
            'purpose': 'Provenance-preserving entry/contract ledger; not a feature count or ChatGPT exclusion list.',
            'generationMethod': 'frozen JSON/JSONL reconciliation only; no target-code parsing/execution or runtime access',
            'idPolicy': 'Menu entryId retains frozen contractId; Route source/consumer IDs retain frozen IDs; remaining IDs derive from baseline/category/input-artifact hash/JSON pointer. IDs are baseline-local, not cross-release feature identities.',
            'associationPolicy': {'allowed': ['explicit reviewed contract references', 'same complete handler definition with reviewed binding/control-flow proof'],
                'forbidden': ['names/command IDs without registry binding', 'URLs/paths', 'channel/method spelling', 'substring overlaps', 'shared infrastructure callee as feature identity'],
                'noFeatureMergesPerformed': True},
            'sourceArtifacts': list(self.artifacts.values()), 'denominators': self.denominators,
            'entries': self.entries, 'supportNodes': self.support, 'reviewedContractLinks': self.links,
            'deferredCandidates': self.deferred, 'evidenceReferences': referenced_evidence,
            'summary': summary,
            'independentReviewScope': self.reference('reviewed-links', '/coverage') if 'reviewed-links' in self.docs else None,
            'scopedCrossArtifactComparisons': self.reference('reviewed-links', '/scopedComparisons') if 'reviewed-links' in self.docs else None,
            'pendingIndependentReview': self.reference('reviewed-links', '/needsReview') if 'reviewed-links' in self.docs else None,
            'requiredReviews': [
                {'id': 'resolve-candidate-bindings', 'scope': ['53 settings candidates', '91 direct RPC candidates', '50 IPC source/channel pairs', '337 unknown request wrappers'],
                 'review': 'Resolve actual registry/callee/receiver definitions and payload/result/error/cancel/state contracts before linking them.'},
                {'id': 'resolve-renderer-registration-scope', 'scope': ['6 Pw candidates', '10 xs candidates', '7 selected hook scopes'],
                 'review': 'Resolve original Program/import bindings and live normal/fallback registrations; same commandId does not prove same handler.'},
                {'id': 'operation-equivalence-review', 'scope': ['shared host handler groups', 'shared native callbacks', 'explicit registration dataflow'],
                 'review': 'Review arguments, branch conditions, account/platform/mode, side effects and results for each entry variant. Shared code may implement multiple operations.'},
                {'id': 'feature-census', 'scope': ['all primary/auxiliary entries'],
                 'review': 'Define user-visible workflow/operation specs, assign stable feature IDs, map entries N:M with evidence, and document merge/split decisions plus unresolved entries. Do not total route/menu/handler counts as features.'},
                {'id': 'mode-reachability', 'scope': ['all entries'],
                 'review': 'Establish actual Codex/Work/ChatGPT guards, prerequisites and runtime behavior before excluding any feature. Names do not justify exclusion.'},
                {'id': 'bundled-package-ownership', 'scope': ['mixed/bundled target definitions'],
                 'review': 'Resolve first-party versus bundled dependency ownership. A bound namespace/source symbol does not prove first-party ownership or justify generating dependency source.'}],
            'validation': {'inputHashesRechecked': len(self.inputs), 'entryIdsUnique': True,
                'linkIdsUnique': True, 'linkEndpointsResolved': True, 'jsonPointersResolved': True,
                'evidenceIdsResolved': True, 'evidenceSourceHashesMatchBaselineManifest': True,
                'evidenceRangesWithinManifestBytes': True,
                'targetSourceSpanBytesRehashedByThisLedger': False,
                'scope': 'Frozen artifact integrity, provenance references and reconciled denominators; no new target AST/runtime verification.'}}
        return result


def summary_md(doc):
    s = doc['summary']
    lines = ['# 功能入口台账（不是功能数）', '', f"冻结版本：`{doc['baselineId']}`。仅汇总既有 JSON/JSONL；未重跑目标 AST、UI 或模型任务。", '',
        f"主类 {s['primaryEntryRecords']} 条、辅助类 {s['auxiliaryEntryRecords']} 条，共 {s['entryRecords']} 条入口/合同记录；另有 {s['supportNodes']} 个支持节点和 {s['deferredCandidateRecords']} 条未知 wrapper 候选。这个总数只用于台账完整性核对。", '',
        '| 分母 | 类型 | 数量 | 定义与限制 |', '| --- | --- | ---: | --- |']
    for d in doc['denominators']:
        lines.append(f"| {d['groupId']} | {d['role']} | {d['recordCount']} | {d['definition']} {d['coverage']} |")
    lines += ['', '菜单411条混合合同细分：', '', '| entryKind | 数量 |', '| --- | ---: |']
    for kind, count in s['menuKinds'].items():
        lines.append(f'| {kind} | {count} |')
    lines += ['', '各入口分母的合同关联覆盖：', '',
        '| 分母 | 记录 | 已有关联 | 未有关联 | 同handler来源关联 |',
        '| --- | ---: | ---: | ---: | ---: |']
    for group, coverage in s['associationByDenominator'].items():
        lines.append(f"| {group} | {coverage['recordCount']} | {coverage['withReviewedContractLinks']} | {coverage['withoutReviewedContractLinks']} | {coverage['withReviewedHandlerIdentityLinks']} |")
    lines += ['', '关联状态必须分别理解：', '',
        f"- 有已审查合同关联：{s['entriesWithReviewedContractLinks']}/{s['entryRecords']}；未关联：{s['entriesWithoutReviewedContractLinks']}/{s['entryRecords']}。主类已关联 {s['primaryEntriesWithReviewedContractLinks']}/{s['primaryEntryRecords']}、未关联 {s['primaryEntriesWithoutReviewedContractLinks']}/{s['primaryEntryRecords']}。", 
        f"- 有同完整 handler 的来源关联：{s['entriesWithReviewedHandlerIdentityLinks']}/{s['entryRecords']}。该数仍不证明操作、payload 或功能等价。",
        '- 经审查确认同一 domain operation 的跨入口关联：0。映射到已确认 feature_id：0；功能总分母仍 unknown。',
        '- 当前跨产物 handler identity 为0：只对保存的119 host definition range、114 route terminal definition 与411 menu index进行坐标比较，不能据此断言完整图不存在关联。路径、commandId、channel 与 method 的同名未用于关联。',
        '', '| 合同关系 | 数量 |', '| --- | ---: |']
    for relation, count in s['linksByRelation'].items():
        lines.append(f'| {relation} | {count} |')
    lines += ['', '493条 route→conversion 关联仅表示冻结合同中保存的 source 构造/API适用关系，不能称作逐条实际路由运行可达或同一业务功能。所有链接的 runtimeReachability 都为 unknown。229条菜单注册关联是保存的双向 source-dataflow 引用核对；独立审查只抽验其中1条，未重新分析目标代码。', '',
        '来源定位：每个 entry 保留冻结 sourceArtifact 的路径、SHA256、JSON pointer、evidenceIds、原始 source hash/UTF-8 byte range；evidenceReferences 保留 journal SHA256 与一基 JSONL 行号。菜单 entryId 直接继承原411稳定 contractId。其余 ID 限于当前 baseline，并不是未来升级时的 feature_id。', '',
        'AST evidence 原有 spanHash 保留；词法候选原本没有 spanHash，显式记为 absent-in-lexical-discovery。台账只验证原始 hash 与 baseline manifest 一致、范围不越界，未再次读取目标源码重算 byte-span hash。', '',
        'Route 170 source 构造、143 fixed path、144含字面 helper 的 resolved path、2 map template 与52 static instance 各有自己的分母；52实例只作支持节点。旧171 lexical host case 中28 nested labels不加入143顶层 case。Settings53与Route50 settings实例没有按名称合并。RPC只计91 sendAppServerRequest候选，337 sendRequest单列未解析。', '',
        '下一轮通往 feature census 的审查：', '']
    for review in doc['requiredReviews']:
        lines.append(f"- `{review['id']}`：{review['review']}")
    lines += ['', f"校验：{s['sourceArtifactCount']} 个输入 artifact hash、{s['entryRecords']} 个唯一 entryId、所有 JSON pointer/link endpoint/evidence reference 均可解析；引用 {s['ledgerEvidenceReferences']} 个既有 evidence。此次静态台账没有新增运行验证，所有模式归属仍 unknown。", '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, default=Path('.analysis-local/entry-ledger-work'))
    args = parser.parse_args()
    ledger = Ledger(args.root.resolve())
    ledger.load()
    ledger.build()
    doc = ledger.finish()
    output = args.output if args.output.is_absolute() else ledger.root / args.output
    output.mkdir(parents=True, exist_ok=True)
    (output / 'functional-entry-ledger.json').write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n')
    (output / 'summary.md').write_text(summary_md(doc))
    (output / 'summary.json').write_text(json.dumps(doc['summary'], ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(doc['summary'], ensure_ascii=False))


if __name__ == '__main__':
    main()
