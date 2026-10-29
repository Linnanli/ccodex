#!/usr/bin/env python3
"""Independently verify saved, bounded Mach-O accessor observations.

This verifier never imports/runs the producer, disassembler, target or a probe.
Only validation.json is written; the input bytes and old freeze remain read-only.
"""
from datetime import datetime, timezone
import hashlib
import json
import mmap
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / '.analysis-local/runtime-native-accessors-work'
BASELINE = 'codex-26.1007.30912-c5b273322a83'
BINARY_HASH = '34598d1cd28252b97c5010bd5d82e2ffc6ca71f2661c85cf89eeddfbb1706398'
BINARY_SIZE = 296533696
OLD_MANIFEST_HASH = '2efce3db6eab91e01263e6ddfaf0a65c807dfc205a51ff8debce03c706a5cadb'
PRODUCER_HASH = 'ab66e6d6b34bf53eeec2d4e03c78df7d2b0a6e407820bb0292ba8aa39b359518'
SYMBOL_NAMES = [
    '__ZN8electron5fuses18IsRunAsNodeEnabledEv',
    '__ZN8electron5fuses25IsCookieEncryptionEnabledEv',
    '__ZN8electron5fuses20IsNodeOptionsEnabledEv',
    '__ZN8electron5fuses23IsNodeCliInspectEnabledEv',
    '__ZN8electron5fuses40IsEmbeddedAsarIntegrityValidationEnabledEv',
    '__ZN8electron5fuses28IsOnlyLoadAppFromAsarEnabledEv',
    '__ZN8electron5fuses45IsLoadBrowserProcessSpecificV8SnapshotEnabledEv',
    '__ZN8electron5fuses41IsGrantFileProtocolExtraPrivilegesEnabledEv',
    '__ZN8electron5fuses25IsWasmTrapHandlersEnabledEv',
    '_napi_get_version', '_napi_create_promise',
]
SYMBOL_VMS = [0x4a279e0 + 32 * i for i in range(9)] + [0x4b2aa60, 0x4b2aab0]
NAPI_INSTRUCTIONS = [
    (0x00, '55'), (0x01, '4889e5'), (0x04, 'b801000000'),
    (0x09, '4885ff'), (0x0c, '741f'), (0x0e, '4885f6'),
    (0x11, '741c'), (0x13, 'c7060a000000'), (0x19, '0f57c0'),
    (0x1c, '0f114778'), (0x20, '48c7878800000000000000'),
    (0x2b, '31c0'), (0x2d, '5d'), (0x2e, 'c3'),
    (0x2f, '48b90000000001000000'), (0x39, '48898f88000000'),
    (0x40, '48c7878000000000000000'), (0x4b, 'ebe0'),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def describe(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return {'path': str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            'bytes': path.stat().st_size, 'sha256': digest.hexdigest()}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def declared(record):
    path = ROOT / record['path']
    require(path.resolve().is_relative_to(ROOT), 'input path escapes workspace')
    actual = describe(path)
    require(actual == record, 'declared file hash/length mismatch: ' + record['path'])
    return actual


def parse_metadata(data):
    # Independent metadata reader. No producer code is imported or evaluated.
    h = struct.unpack_from('<8I', data, 0)
    require(h[0] == 0xfeedfacf and h[1] == 0x1000007, 'unexpected Mach-O architecture')
    count, byte_count = h[4:6]
    end = 32 + byte_count
    require(end <= len(data), 'load commands outside binary')
    pos, segments, symtab, commands = 32, [], None, []
    for ordinal in range(count):
        command, size = struct.unpack_from('<II', data, pos)
        require(size >= 8 and pos + size <= end, 'invalid load command extent')
        commands.append(command)
        if command == 0x19:
            values = struct.unpack_from('<II16sQQQQiiII', data, pos)
            name = values[2].split(b'\0')[0].decode('ascii')
            vm, vm_size, file_off, file_size, maxprot, initprot, section_count, flags = values[3:]
            require(size == 72 + 80 * section_count, 'segment section extent mismatch')
            require(file_off + file_size <= len(data), 'segment file extent mismatch')
            sections = []
            for i in range(section_count):
                at = pos + 72 + 80 * i
                s = struct.unpack_from('<16s16sQQIIIIIIII', data, at)
                sections.append({'name': s[0].split(b'\0')[0].decode('ascii'),
                    'segmentName': s[1].split(b'\0')[0].decode('ascii'),
                    'vmAddress': s[2], 'vmSize': s[3], 'fileOffset': s[4], 'flags': s[8],
                    'sectionHeaderFileOffset': at, 'sectionHeaderBytes': 80})
            segments.append({'name': name, 'vmAddress': vm, 'vmSize': vm_size,
                'fileOffset': file_off, 'fileSize': file_size, 'maxprot': maxprot,
                'initprot': initprot, 'commandFileOffset': pos, 'commandBytes': size,
                'sections': sections})
        if command == 2:
            require(symtab is None and size == 24, 'invalid/duplicate LC_SYMTAB')
            _, _, symoff, nsyms, stroff, strsize = struct.unpack_from('<6I', data, pos)
            require(symoff + 16 * nsyms <= len(data) and stroff + strsize <= len(data),
                    'symbol/string table outside binary')
            symtab = {'commandFileOffset': pos, 'commandBytes': size,
                'symbolTableFileOffset': symoff, 'symbolCount': nsyms,
                'stringTableFileOffset': stroff, 'stringTableBytes': strsize}
        pos += size
    require(pos == end and symtab is not None, 'load-command table incomplete')
    header = dict(zip(['magic', 'cpuType', 'cpuSubtype', 'fileType', 'loadCommandCount',
                      'loadCommandBytes', 'flags'], h[:7]))
    header['functionStartsCommandPresent'] = 0x26 in commands
    selected = {}
    wanted = dict(zip(SYMBOL_VMS, SYMBOL_NAMES))
    # Enumerate the declared symbol table to detect a duplicate selected binding.
    for i in range(symtab['symbolCount']):
        at = symtab['symbolTableFileOffset'] + 16 * i
        strx, typ, section, desc, vm = struct.unpack_from('<IBBHQ', data, at)
        if vm not in wanted or typ & 0x0e != 0x0e:
            continue
        require(strx < symtab['stringTableBytes'], 'symbol string index outside table')
        string_at = symtab['stringTableFileOffset'] + strx
        string_end = data.find(b'\0', string_at,
                               symtab['stringTableFileOffset'] + symtab['stringTableBytes'])
        require(string_end >= string_at, 'unterminated selected symbol name')
        name = data[string_at:string_end].decode('ascii')
        if name != wanted[vm]:
            continue
        require(vm not in selected, 'duplicate selected native symbol')
        selected[vm] = {'name': name, 'unslidVmAddress': vm, 'nlistIndex': i,
            'nlistFileOffset': at, 'nlistBytes': 16, 'stringFileOffset': string_at,
            'stringBytesIncludingNull': string_end + 1 - string_at,
            'nType': typ, 'sectionIndex': section}
    require(set(selected) == set(wanted), 'selected symbol denominator incomplete')
    return header, segments, symtab, selected


def mapping(segments, vm, size):
    selected = [s for s in segments if s['vmAddress'] <= vm and
                vm + size <= s['vmAddress'] + s['fileSize']]
    require(len(selected) == 1, 'ambiguous/unbacked VM-to-file mapping')
    s = selected[0]
    offset = s['fileOffset'] + vm - s['vmAddress']
    section = [x for x in s['sections'] if x['vmAddress'] <= vm and
               vm + size <= x['vmAddress'] + x['vmSize']]
    return {'segmentName': s['name'], 'segmentVmAddress': s['vmAddress'],
        'segmentFileOffset': s['fileOffset'],
        'sectionName': section[0]['name'] if len(section) == 1 else None,
        'unslidVmAddress': vm, 'fileOffset': offset, 'bytes': size}


def instruction_rows(text, start, end, segments, data):
    # Only consume saved LLVM output; verify its complete bounded byte coverage.
    rows = []
    for line in text.splitlines():
        match = re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)(.*)$', line)
        if match:
            address = int(match.group(1), 16)
            body = bytes.fromhex(match.group(2))
            require(start <= address and address + len(body) <= end, 'LLVM output outside byte scope')
            off = mapping(segments, address, len(body))['fileOffset']
            require(data[off:off + len(body)] == body, 'LLVM displayed bytes differ from binary')
            rows.append((address, body, match.group(3).strip()))
    require(rows and rows[0][0] == start, 'LLVM range does not start at requested byte')
    cursor = start
    for address, body, asm in rows:
        require(address == cursor, 'LLVM saved instruction coverage gap/overlap')
        cursor += len(body)
    require(cursor == end, 'LLVM saved instruction coverage truncated')
    return rows


def verify(report, evidence, counts, snapshots):
    require(report['baselineId'] == BASELINE, 'baseline changed')
    require(len(report['sourceInputs']) == 8 and len(report['scripts']) == 1,
            'input/producer pin denominator changed')
    snapshots['sourceInputs'] = [declared(r) for r in report['sourceInputs']]
    snapshots['producerPins'] = [declared(r) for r in report['scripts']]
    require(snapshots['producerPins'][0]['sha256'] == PRODUCER_HASH, 'producer differs from reviewed pin')
    counts['sourceInputHashChecks'], counts['producerPinHashChecks'] = 8, 1
    products = [WORK / x for x in ['runtime-native-accessors.json', 'evidence.jsonl', 'summary.md']]
    products += [WORK / (label + '.' + suffix) for label in
                 ['llvm-version', 'fuse-accessors', 'napi-get-version'] for suffix in
                 ['stdout.txt', 'stderr.txt', 'command.json']]
    snapshots['productFiles'] = [describe(p) for p in products]
    require(len(snapshots['productFiles']) == 12, 'product denominator changed')
    manifest_path = ROOT / '.analysis-local/runtime-fuse-work/frozen-manifest.json'
    require(describe(manifest_path)['sha256'] == OLD_MANIFEST_HASH, 'old fuse manifest changed')
    manifest = json.loads(manifest_path.read_text())
    snapshots['oldFuseFrozenFiles'] = [declared(r) for r in manifest['files']]
    counts['oldFuseFrozenFileHashChecks'] = len(manifest['files'])
    snapshots['oldFuseManifest'] = describe(manifest_path)
    old_fuse = json.loads((ROOT / '.analysis-local/runtime-fuse-work/runtime-fuse-observation.json').read_text())
    old_evidence = {e['id']: e for e in map(json.loads,
        (ROOT / '.analysis-local/runtime-fuse-work/evidence.jsonl').read_text().splitlines())}
    old_wire = old_fuse['observations'][1]['wireCandidates'][0]
    require(old_wire['wireAscii'] == '010011001', 'frozen wire differs')
    source = report['sourceBinary']
    require(source['bytes'] == BINARY_SIZE and source['sourceHash'] == BINARY_HASH and
            source['runtimeCopyPath'] == old_fuse['observations'][1]['runtimeCopyPath'],
            'source binary binding changed')
    binary = ROOT / source['runtimeCopyPath']
    snapshots['binary'] = describe(binary)
    require(snapshots['binary']['bytes'] == BINARY_SIZE and snapshots['binary']['sha256'] == BINARY_HASH,
            'complete Framework pin differs')
    inventory = json.loads((ROOT / ('analysis/' + BASELINE + '/files.json')).read_text())
    inventory_items = [x for x in inventory['applicationFiles'] if x['sourcePath'] == source['sourcePath']]
    require(len(inventory_items) == 1 and inventory_items[0]['sha256'] == BINARY_HASH and
            inventory_items[0]['bytes'] == BINARY_SIZE and source['frozenInventoryHashMatch'] is True,
            'Framework inventory binding differs')
    counts['binaryInventoryHashChecks'], counts['completeBinaryBytes'] = 1, BINARY_SIZE
    require(len(evidence) == 48, 'evidence denominator differs')
    by_id = {e['id']: e for e in evidence}
    require(len(by_id) == 48 and set(by_id) == {'RUNTIME-NATIVE-ACCESSOR-E' + str(i).zfill(3)
            for i in range(1, 49)}, 'evidence IDs duplicate/missing')
    used = set()
    with binary.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        for e in evidence:
            require(e['baselineId'] == BASELINE and e['sourcePath'] == source['sourcePath'] and
                    e['sourceHash'] == BINARY_HASH and e['confidence'] == 'confirmed', 'evidence source differs')
            locator = e['locator']
            require(locator['kind'] == 'byte-range' and
                    0 <= locator['start'] < locator['endExclusive'] <= len(data), 'invalid evidence extent')
            require(sha(data[locator['start']:locator['endExclusive']]) == e['spanSha256'],
                    'evidence span bytes differ: ' + e['id'])
            require('static' in e['verificationStatus'] and 'unverified' in e['verificationStatus'],
                    'evidence status overclaims execution')
        counts['evidenceSpanChecks'] = len(evidence)
        def ref(ident, start, length):
            require(ident in by_id and by_id[ident]['locator'] ==
                    {'kind': 'byte-range', 'start': start, 'endExclusive': start + length},
                    'evidence-to-record locator mismatch: ' + ident)
            used.add(ident)
        header, segments, symtab, symbols = parse_metadata(data)
        require(report['machO']['header'] == header and report['machO']['segments'] == segments and
                report['machO']['symbolTable'] == symtab, 'published Mach-O metadata differs')
        require(header['loadCommandCount'] == 81 and len(segments) == 5 and
                header['functionStartsCommandPresent'] is False, 'Mach-O table denominator differs')
        text = next(x for x in segments if x['name'] == '__TEXT')
        section = next(x for x in text['sections'] if x['name'] == '__text')
        expected_spans = [(0, 32), (32, header['loadCommandBytes']),
                          (text['commandFileOffset'], text['commandBytes']),
                          (section['sectionHeaderFileOffset'], 80),
                          (symtab['commandFileOffset'], 24)]
        require(len(report['machO']['mappingEvidenceIds']) == 5, 'mapping evidence denominator differs')
        for ident, (start, size) in zip(report['machO']['mappingEvidenceIds'], expected_spans):
            ref(ident, start, size)
        counts['loadCommandsParsed'], counts['segmentsParsed'], counts['selectedSymbolChecks'] = 81, 5, 11
        def symbol(record, vm):
            actual = {k: v for k, v in record.items() if k not in ['nlistEvidenceId', 'nameEvidenceId']}
            require(actual == symbols[vm], 'native symbol binding differs')
            ref(record['nlistEvidenceId'], actual['nlistFileOffset'], 16)
            ref(record['nameEvidenceId'], actual['stringFileOffset'], actual['stringBytesIncludingNull'])
        binding = report['wireBinding']
        require(binding == {'priorFuseObservationHash': snapshots['sourceInputs'][2]['sha256'],
            'priorFuseEvidenceId': old_wire['evidenceId'], 'wireFileStart': old_wire['byteStart'],
            'wireByteStart': 246224818, 'wireByteEndExclusive': 246224827,
            'wireAscii': '010011001', 'wireEvidenceId': 'RUNTIME-NATIVE-ACCESSOR-E028',
            'linkedAccessors': 9}, 'wire cross-artifact binding differs')
        wire_start, wire_end = old_wire['byteStart'], old_wire['byteEndExclusive']
        require(data[wire_start + 32:wire_start + 34] == b'\x01\x09' and
                data[246224818:246224827] == b'010011001', 'wire header/states differ')
        require(sha(data[wire_start:wire_end]) == old_evidence[old_wire['evidenceId']]['spanSha256'],
                'old fuse span cross-binding differs')
        ref(binding['wireEvidenceId'], wire_start, wire_end - wire_start)
        require(len(report['fuseAccessors']) == 9, 'accessor denominator differs')
        for i, a in enumerate(report['fuseAccessors']):
            vm = SYMBOL_VMS[i]
            symbol(a['nativeSymbol'], vm)
            code_map = mapping(segments, vm, 17)
            require(a['codeMapping'] == code_map and code_map['sectionName'] == '__text', 'accessor code map differs')
            offset = code_map['fileOffset']
            body = data[offset:offset + 17]
            require(body[:6] == bytes.fromhex('554889e58a05') and
                    body[10:] == bytes.fromhex('3c310f94c05dc3'), 'complete accessor opcodes differ')
            disp = struct.unpack_from('<i', body, 6)[0]
            target = vm + 10 + disp
            read_map = mapping(segments, target, 1)
            require(target == 0xead17b2 + i and read_map['fileOffset'] == 246224818 + i,
                    'RIP target/wire ordinal differs')
            require(a['ordinal'] == a['readWireOrdinal'] == i and a['bodyBytes'] == 17 and
                    a['bodyHex'] == body.hex() and a['ripDisplacementSigned'] == disp and
                    a['ripDisplacementBytesHex'] == body[6:10].hex() and
                    a['ripNextUnslidVm'] == vm + 10 and a['readUnslidVm'] == target and
                    a['readMapping'] == read_map, 'accessor decoded record differs')
            require(a['rawByte'] == data[read_map['fileOffset']] == ord(binding['wireAscii'][i]) and
                    a['wireAsciiByte'] == binding['wireAscii'][i], 'accessor byte differs')
            require(a['officialSchemaName'] == old_wire['states'][i]['officialSchemaName'] and
                    a['priorFuseEvidenceId'] == old_wire['states'][i]['evidenceId'] and
                    a['priorFuseEvidenceId'] in old_evidence, 'prior fuse identity differs')
            require(a['staticReturnPredicate'] == 'AL := (memory[readUnslidVm] == 0x31); ret' and
                    all(a[k] is False for k in ['executionVerified', 'callerClosureVerified',
                                               'startupEnforcementVerified']), 'accessor semantic scope differs')
            ref(a['codeEvidenceId'], offset, 17)
            ref(a['byteEvidenceId'], read_map['fileOffset'], 1)
        counts['completeAccessorBodyChecks'], counts['ripTargetChecks'], counts['accessorBodyBytes'] = 9, 9, 153
        n = report['napiGetVersion']
        vm, end, next_vm = 0x4b2aa60, 0x4b2aaad, 0x4b2aab0
        symbol(n['nativeSymbol'], vm)
        symbol(n['nextNativeSymbol'], next_vm)
        nmap = mapping(segments, vm, 77)
        off = nmap['fileOffset']
        body = data[off:off + 77]
        expected_body = b''.join(bytes.fromhex(code) for _, code in NAPI_INSTRUCTIONS)
        require(len(expected_body) == 77 and body == expected_body and n['bodyHex'] == body.hex() and
                n['codeMapping'] == nmap and n['bodyBytes'] == 77 and n['bodyEndUnslidVmExclusive'] == end,
                'complete NAPI function bytes/range differ')
        starts = {vm + delta for delta, _ in NAPI_INSTRUCTIONS}
        edges, branches = {}, []
        for delta, code in NAPI_INSTRUCTIONS:
            instruction = bytes.fromhex(code)
            at, after = vm + delta, vm + delta + len(instruction)
            if instruction[0] in (0x74, 0xeb):
                target = after + struct.unpack('<b', instruction[1:2])[0]
                require(target in starts, 'NAPI branch escapes instruction boundary')
                kind = 'conditional-equal' if instruction[0] == 0x74 else 'unconditional-short-jump'
                item = {'instructionUnslidVm': at, 'kind': kind, 'targetUnslidVm': target}
                if instruction[0] == 0x74:
                    item['condition'] = 'RDI == 0 after test' if delta == 0x0c else 'RSI == 0 after test'
                branches.append(item)
                edges[at] = [target, after] if instruction[0] == 0x74 else [target]
            elif instruction == b'\xc3':
                edges[at] = []
            else:
                require(after in starts, 'NAPI fallthrough escapes body')
                edges[at] = [after]
        reachable, pending = set(), [vm]
        while pending:
            at = pending.pop()
            if at not in reachable:
                reachable.add(at)
                pending.extend(edges[at])
        require(reachable == starts and n['controlFlow'] == branches and
                n['returnUnslidVm'] == vm + 0x2e, 'NAPI complete CFG differs')
        require(n['writeInstructionUnslidVm'] == vm + 0x13 and n['writeInstructionFileOffset'] == off + 0x13 and
                n['writeInstructionHex'] == body[0x13:0x19].hex() and
                n['storedUint32Immediate'] == struct.unpack_from('<I', body, 0x15)[0] == 10 and
                n['destinationRegister'] == 'rsi', 'NAPI constant/destination differs')
        pad_off = mapping(segments, end, 3)['fileOffset']
        require(data[pad_off:pad_off + 3] == bytes.fromhex('0f1f00') and
                n['followingPaddingBytes'] == 3 and n['executionVerified'] is False,
                'NAPI padding/semantic execution claim differs')
        require('not an LC_FUNCTION_STARTS table' in n['rangeBasis'] and
                all(x in n['claimScope'] for x in ['10', 'Node version', 'NODE_MODULE_VERSION', 'unverified']),
                'NAPI version/range limitation missing')
        ref(n['bodyEvidenceId'], off, 77)
        ref(n['writeEvidenceId'], off + 0x13, 6)
        counts['napiInstructionChecks'], counts['napiInternalBranchChecks'] = len(starts), len(branches)
        counts['napiBodyBytes'], counts['napiPaddingByteChecks'] = 77, 3
        require(used == set(by_id), 'orphan/unbound evidence records')
        counts['evidenceRecordBindingChecks'] = len(used)
        require(len(report['toolRuns']) == 3, 'saved tool run denominator differs')
        tool_specs = [('llvm-version', ['--version'], None),
            ('fuse-accessors', ['--disassemble', '--start-address=0x4a279e0', '--stop-address=0x4a27af1', str(binary)],
             {'startUnslidVm': 0x4a279e0, 'endUnslidVmExclusive': 0x4a27af1, 'selectedFunctionCount': 9}),
            ('napi-get-version', ['--disassemble', '--start-address=0x4b2aa60', '--stop-address=0x4b2aab0', str(binary)],
             {'startUnslidVm': vm, 'endUnslidVmExclusive': next_vm, 'selectedFunctionCount': 1, 'paddingBytes': 3})]
        tool_hashes = set()
        raw_rows = {}
        for record, (label, args, scope) in zip(report['toolRuns'], tool_specs):
            saved = json.loads((WORK / (label + '.command.json')).read_text())
            require(saved == record and record['label'] == label and record['exitCode'] == 0 and
                    record['argv'] == [record['toolExecutable']] + args and record['byteScope'] == scope and
                    record['targetApplicationExecuted'] is False, 'saved tool command/scope differs')
            executable = Path(record['toolExecutable'])
            require(str(executable.resolve()) == record['toolResolvedPath'] and
                    describe(executable)['sha256'] == record['toolSha256'], 'saved tool executable pin differs')
            tool_hashes.add(record['toolSha256'])
            out, err = declared(record['stdout']), declared(record['stderr'])
            require(out['path'] == str((WORK / (label + '.stdout.txt')).relative_to(ROOT)) and
                    err['path'] == str((WORK / (label + '.stderr.txt')).relative_to(ROOT)) and err['bytes'] == 0,
                    'saved tool output path/stderr differs')
            stdout = (ROOT / out['path']).read_text()
            if label == 'llvm-version':
                require(stdout == report['toolVersion'] and 'Apple LLVM version 21.0.0' in stdout,
                        'saved LLVM version differs')
            else:
                rows = instruction_rows(stdout, scope['startUnslidVm'], scope['endUnslidVmExclusive'], segments, data)
                raw_rows[label] = rows
                needed = SYMBOL_VMS[:9] if label == 'fuse-accessors' else [vm]
                for address in needed:
                    require(re.search(r'^0*' + format(address, 'x') + r' <' +
                                      re.escape(symbols[address]['name']) + r'>:', stdout, re.M),
                            'saved disassembly selected symbol label differs')
        require(len(tool_hashes) == 1 and len(raw_rows['fuse-accessors']) == 71 and
                len(raw_rows['napi-get-version']) == 19, 'saved tool byte coverage denominator differs')
        counts['savedToolArtifactHashChecks'], counts['savedToolCommandChecks'] = 9, 3
        counts['savedToolInstructionByteChecks'], counts['toolExecutableHashChecks'] = 90, 1
    scope = report['scope']
    expected_scope = {'selectedBinaryCount': 1, 'selectedFuseAccessorFunctions': 9,
        'selectedNodeApiAccessorFunctions': 1, 'accessorBodyBytes': 153, 'nodeApiBodyBytes': 77,
        'machineCodeBodyBytes': 230, 'sourceEvidenceRecords': 48, 'completeNativeCallerClosure': False,
        'targetApplicationLaunched': False, 'targetBinaryModified': False, 'fusesChanged': False,
        'modelTasksSubmitted': 0, 'networkRequests': 0, 'broadNativeDisassembly': False,
        'actualNodeVersion': 'unknown', 'nodeModuleVersion': 'unknown', 'nativeModulesAbi': 'unknown'}
    require(scope == expected_scope, 'reported scope differs')
    for key in ['actualNodeVersion', 'actualElectronCompatibilityVersion', 'nodeModuleVersion',
                'nativeModulesAbi', 'completeNativeCallerClosure', 'startupExecutionAndEnforcement']:
        require(report['conclusions'][key] == 'unknown', 'unknown scope improperly resolved: ' + key)
    require(len(report['schemaReferences']) == 1 and
            report['schemaReferences'][0]['url'] == 'https://nodejs.org/api/n-api.html#napi_get_version' and
            report['schemaReferences'][0]['externalPageReportedVersion'] == 'v26.11.1' and
            'not target Node release' in report['schemaReferences'][0]['role'] and
            'external libraries' in report['schemaReferences'][0]['abiScope'],
            'external documentation scope differs')
    require(any('seven earlier' in x and 'unexplained' in x for x in report['limitations']) and
            any('do not prove callers' in x for x in report['limitations']), 'retained limitation missing')
    summary = (WORK / 'summary.md').read_text()
    require('010011001' in summary and '77字节' in summary and '230字节' in summary and
            'unknown' in summary and '不是目标 Node 版本' in summary and '7条既有归档声明矛盾' in summary,
            'summary scope inconsistent')
    # Verify all input and product bytes again before writing the sole output.
    for group in ['sourceInputs', 'producerPins', 'productFiles', 'oldFuseFrozenFiles']:
        for item in snapshots[group]:
            require(describe(ROOT / item['path']) == item, 'input/product changed during validation')
    require(describe(binary) == snapshots['binary'] and describe(manifest_path) == snapshots['oldFuseManifest'],
            'binary/old manifest changed during validation')
    counts['unchangedInputProductChecks'] = sum(len(snapshots[k]) for k in
        ['sourceInputs', 'producerPins', 'productFiles', 'oldFuseFrozenFiles']) + 2


def main():
    output = WORK / 'validation.json'
    require(not output.exists(), 'refuse to overwrite validation.json')
    runner = describe(Path(__file__).resolve())
    counts, snapshots, errors = {}, {}, []
    try:
        report = json.loads((WORK / 'runtime-native-accessors.json').read_text())
        evidence = [json.loads(line) for line in (WORK / 'evidence.jsonl').read_text().splitlines()]
        verify(report, evidence, counts, snapshots)
    except Exception as exc:
        errors.append({'type': type(exc).__name__, 'message': str(exc)})
    require(describe(Path(__file__).resolve()) == runner, 'verifier changed during run')
    result = {'baselineId': BASELINE, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
        'status': 'passed; execution-caller-and-runtime-version-unverified' if not errors else 'failed',
        'method': 'Independent read-only source hashes, Mach-O tables, complete fixed machine-code instruction bytes, internal CFG, saved tool output and old frozen material checks; no producer/tool/target execution.',
        'runner': runner, 'runnerArgv': sys.argv, 'runnerUnchangedDuringRun': True,
        'counts': counts, 'snapshots': snapshots, 'errors': errors,
        'retainedUnknowns': {'actualNodeVersion': 'unknown', 'actualElectronCompatibilityVersion': 'unknown',
            'nodeModuleVersion': 'unknown', 'nativeModulesAbi': 'unknown',
            'completeNativeCallerClosure': 'unknown', 'startupExecutionAndEnforcement': 'unknown'},
        'executionScope': {'producerRuns': 0, 'disassemblerRuns': 0, 'targetProgramsLaunched': 0,
            'nodeDiagnosticProbes': 0, 'networkRequests': 0, 'modelTasksSubmitted': 0,
            'changedOutputs': [str(output.relative_to(ROOT))], 'oldFuseMaterialModified': False},
        'limitations': ['Byte and metadata checks establish the selected static bindings only.',
            'Official Node-API interpretation is supplied source context; the verifier performs no network request.',
            'Seven historical archive/unpacked declaration contradictions remain unresolved.']}
    with output.open('x') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'counts': counts, 'errors': errors,
                      'validation': describe(output), 'runner': runner}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
