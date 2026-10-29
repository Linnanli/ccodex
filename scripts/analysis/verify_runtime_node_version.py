#!/usr/bin/env python3
"""Independent, bounded, read-only verification of static Node-version evidence.

verify(root, work) returns an in-memory result without writing anything. The CLI
writes validation.json once. No producer, target, disassembler or probe is run.
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
WORK = ROOT / '.analysis-local/runtime-node-version-work'
BASELINE = 'codex-26.1007.30912-c5b273322a83'
BINARY_HASH = '34598d1cd28252b97c5010bd5d82e2ffc6ca71f2661c85cf89eeddfbb1706398'
BINARY_SIZE = 296533696
MAIN_HASH = '866f3acf38a7728ab3c38869f635076fc84b4a611fe2cfa486170e98ed32d8f5'
PRODUCER_HASH = '9256b413c91a5a3c57b445a348514cc33f80e9dc08dda430f493059a56bc0610'
NATIVE_MANIFEST_HASH = '72776bbdff059553a0aa10b6167e98c89e765eb2b52b385db0eb6333bd963f25'
FUSE_MANIFEST_HASH = '2efce3db6eab91e01263e6ddfaf0a65c807dfc205a51ff8debce03c706a5cadb'
APPLE_HEADER_HASH = '90bd2b316ada7fc5fe47c2872ea679f0c6cc6d249ed5965dbbdc5bea5afdd21a'
START, BODY_END, NEXT = 0x4b42f60, 0x4b42fb1, 0x4b42fc0
NAMES = {START: '_napi_get_node_version', NEXT: '_napi_create_async_work'}
# Instruction boundaries and bytes independently read before the producer ran.
INSTRUCTIONS = [
    (0x00, '55'), (0x01, '4889e5'), (0x04, 'b801000000'),
    (0x09, '4885ff'), (0x0c, '7423'), (0x0e, '4885f6'),
    (0x11, '7420'), (0x13, '488d05a607690c'), (0x1a, '488906'),
    (0x1d, '0f57c0'), (0x20, '0f114778'),
    (0x24, '48c7878800000000000000'), (0x2f, '31c0'),
    (0x31, '5d'), (0x32, 'c3'), (0x33, '48b90000000001000000'),
    (0x3d, '48898f88000000'), (0x44, '48c7878000000000000000'),
    (0x4f, 'ebe0'),
]
PADDING = bytes.fromhex('6666666666662e0f1f840000000000')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def describe(path, root):
    path = Path(path)
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            value.update(block)
    return {'path': str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
            'bytes': path.stat().st_size, 'sha256': value.hexdigest()}


def read_metadata(data):
    # The reader does not import or evaluate either producer or previous verifier.
    h = struct.unpack_from('<8I', data)
    require(h[0] == 0xfeedfacf and h[1] == 0x1000007, 'unexpected Mach-O architecture')
    cursor, end = 32, 32 + h[5]
    require(end <= len(data), 'load commands outside source binary')
    segments, symbols, fixups, tags = [], None, None, []
    for ordinal in range(h[4]):
        tag, size = struct.unpack_from('<II', data, cursor)
        require(size >= 8 and cursor + size <= end, 'invalid load-command extent')
        tags.append(tag)
        if tag == 0x19:
            a = struct.unpack_from('<II16sQQQQiiII', data, cursor)
            name = a[2].split(b'\0')[0].decode('ascii')
            require(size == 72 + 80 * a[9] and a[5] + a[6] <= len(data), 'invalid segment extent')
            sections = []
            for i in range(a[9]):
                at = cursor + 72 + i * 80
                s = struct.unpack_from('<16s16sQQIIIIIIII', data, at)
                require(s[1].split(b'\0')[0].decode('ascii') == name, 'section segment name differs')
                sections.append({'name': s[0].split(b'\0')[0].decode('ascii'),
                    'vmAddress': s[2], 'vmSize': s[3], 'fileOffset': s[4],
                    'flags': s[8], 'headerFileOffset': at})
            segments.append({'name': name, 'vmAddress': a[3], 'vmSize': a[4],
                'fileOffset': a[5], 'fileSize': a[6], 'commandFileOffset': cursor,
                'commandBytes': size, 'sections': sections})
        elif tag == 2:
            require(symbols is None and size == 24, 'invalid/duplicate LC_SYMTAB')
            _, _, off, count, strings, length = struct.unpack_from('<6I', data, cursor)
            require(off + count * 16 <= len(data) and strings + length <= len(data),
                    'symbol table outside binary')
            symbols = {'commandFileOffset': cursor, 'commandBytes': size,
                'symbolTableFileOffset': off, 'symbolCount': count,
                'stringTableFileOffset': strings, 'stringTableBytes': length}
        elif tag == 0x80000034:
            require(fixups is None and size == 16, 'invalid/duplicate chained-fixups command')
            _, _, off, length = struct.unpack_from('<4I', data, cursor)
            require(off + length <= len(data), 'chained-fixups payload outside binary')
            fixups = {'commandFileOffset': cursor, 'commandBytes': size,
                      'dataFileOffset': off, 'dataBytes': length}
        cursor += size
    require(cursor == end and symbols and fixups, 'incomplete Mach-O load-command table')
    header = dict(zip(['magic', 'cpuType', 'cpuSubtype', 'fileType',
                      'loadCommandCount', 'loadCommandBytes'], h[:6]))
    header['functionStartsCommandPresent'] = 0x26 in tags
    found = {}
    # Name selection is restricted to two exact names in the declared symbol table.
    for i in range(symbols['symbolCount']):
        at = symbols['symbolTableFileOffset'] + 16 * i
        strx, typ, section, desc, vm = struct.unpack_from('<IBBHQ', data, at)
        require(strx < symbols['stringTableBytes'], 'symbol string index outside table')
        string_at = symbols['stringTableFileOffset'] + strx
        string_end = data.find(b'\0', string_at,
            symbols['stringTableFileOffset'] + symbols['stringTableBytes'])
        require(string_end >= string_at, 'unterminated symbol name')
        name = data[string_at:string_end].decode('ascii')
        if name not in NAMES.values():
            continue
        require(vm in NAMES and NAMES[vm] == name and typ & 0x0e == 0x0e and vm not in found,
                'exact selected native symbol binding differs')
        found[vm] = {'name': name, 'unslidVmAddress': vm, 'nlistIndex': i,
            'nlistFileOffset': at, 'nlistBytes': 16, 'stringFileOffset': string_at,
            'stringBytesIncludingNull': string_end + 1 - string_at,
            'nType': typ, 'sectionIndex': section}
    require(set(found) == set(NAMES), 'selected symbol denominator incomplete')
    return header, segments, symbols, fixups, found


def mapping(segments, vm, size):
    selected = [s for s in segments if s['vmAddress'] <= vm and
                vm + size <= s['vmAddress'] + s['fileSize']]
    require(len(selected) == 1, 'ambiguous/unbacked VM mapping')
    s = selected[0]
    sections = [x for x in s['sections'] if x['vmAddress'] <= vm and
                vm + size <= x['vmAddress'] + x['vmSize']]
    require(len(sections) == 1 and sections[0]['flags'] & 0xff not in (1, 12, 18),
            'selected bytes not in one file-backed section')
    return {'unslidVmAddress': vm, 'fileOffset': s['fileOffset'] + vm - s['vmAddress'],
        'bytes': size, 'segmentName': s['name'], 'segmentVmAddress': s['vmAddress'],
        'segmentFileOffset': s['fileOffset'], 'sectionName': sections[0]['name'],
        'sectionHeaderFileOffset': sections[0]['headerFileOffset']}


def verify(root, work):
    """Verify saved material without executing tools or writing any file."""
    root, work = Path(root).resolve(), Path(work).resolve()
    require(work.is_relative_to(root), 'work directory outside workspace')
    counts, snapshots, before = {}, {}, {}
    def track(path, expected=None):
        path = Path(path)
        actual = describe(path, root)
        if expected is not None:
            require(actual == expected, 'declared file bytes/hash differ: ' + str(path))
        key = str(path)
        require(key not in before or before[key] == actual, 'file changed between reads: ' + key)
        before[key] = actual
        return actual
    def declared(record):
        path = root / record['path']
        require(path.resolve().is_relative_to(root), 'declared source path escapes workspace')
        return track(path, record)
    runner = track(Path(__file__).resolve())
    main_pin = track(work / 'runtime-node-version.json')
    require(main_pin['sha256'] == MAIN_HASH, 'main JSON differs from reviewed successful pin')
    a = json.loads((work / 'runtime-node-version.json').read_text())
    require(a['baselineId'] == BASELINE, 'baseline changed')
    require(len(a['sourceInputs']) == 4 and len(a['sourceArtifacts']) == 5 and len(a['scripts']) == 1,
            'source/pin denominator changed')
    for key in ['sourceInputs', 'sourceArtifacts', 'scripts']:
        snapshots[key] = [declared(x) for x in a[key]]
    require(snapshots['scripts'][0]['sha256'] == PRODUCER_HASH, 'reviewed producer pin differs')
    counts.update(sourceInputHashChecks=4, sourceArtifactHashChecks=5, producerPinHashChecks=1)
    names = ['runtime-node-version.json', 'evidence.jsonl', 'summary.md', 'apple-fixup-chains.h']
    names += [label + '.' + suffix for label in ['llvm-version', 'napi-get-node-version']
              for suffix in ['stdout.txt', 'stderr.txt', 'command.json']]
    snapshots['products'] = [track(work / name) for name in names]
    counts['productHashSnapshots'] = len(names)
    for attempt in ['01', '02']:
        directory = root / ('.analysis-local/runtime-node-version-attempt-' + attempt)
        failed = json.loads((directory / 'failure-record.json').read_text())
        require(failed['exitCode'] == 1 and failed['exception'] == 'AssertionError' and
                failed['scriptSha256'] == track(directory / 'producer-attempt.py')['sha256'] and
                'before' in failed['scope'].lower() and 'target never executed' in failed['scope'],
                'failed producer attempt source pin/scope differs')
    counts['failedProducerArchiveBindings'] = 2
    for key, directory, pin, expected_count in [
        ('oldNativeFreeze', '.analysis-local/runtime-native-accessors-work', NATIVE_MANIFEST_HASH, 15),
        ('oldFuseFreeze', '.analysis-local/runtime-fuse-work', FUSE_MANIFEST_HASH, 5)]:
        path = root / directory / 'frozen-manifest.json'
        manifest_pin = track(path)
        require(manifest_pin['sha256'] == pin, 'old frozen manifest changed')
        manifest = json.loads(path.read_text())
        require(len(manifest['files']) == expected_count, 'old freeze file denominator changed')
        snapshots[key] = {'manifest': manifest_pin, 'files': [declared(x) for x in manifest['files']]}
        counts[key + 'FileHashChecks'] = expected_count
    source = a['sourceBinary']
    require(source['sha256'] == BINARY_HASH and source['bytes'] == BINARY_SIZE,
            'Framework declared identity differs')
    binary = root / source['runtimeCopyPath']
    snapshots['binary'] = track(binary)
    require(snapshots['binary']['sha256'] == BINARY_HASH and snapshots['binary']['bytes'] == BINARY_SIZE,
            'complete binary bytes/hash differ')
    inventory = json.loads((root / source['inventoryPath']).read_text())
    rows = [x for x in inventory['applicationFiles'] if x['sourcePath'] == source['sourcePath']]
    require(len(rows) == 1 and rows[0]['sha256'] == BINARY_HASH and rows[0]['bytes'] == BINARY_SIZE,
            'inventory binary identity differs')
    previous = json.loads((root / '.analysis-local/runtime-native-accessors-work/runtime-native-accessors.json').read_text())
    require(previous['sourceBinary']['runtimeCopyPath'] == source['runtimeCopyPath'],
            'runtime clone source binding changed')
    counts['completeBinaryBytes'], counts['binaryInventoryHashChecks'] = BINARY_SIZE, 1
    evidence = [json.loads(line) for line in (work / 'evidence.jsonl').read_text().splitlines()]
    by_id = {e['id']: e for e in evidence}
    require(len(evidence) == len(by_id) == 24 and set(by_id) ==
            {'RUNTIME-NODE-VERSION-E' + str(i).zfill(3) for i in range(1, 25)},
            'evidence denominator/unique IDs differ')
    used = set()
    def ref(ident, start, size):
        require(ident in by_id and by_id[ident]['locator'] ==
                {'kind': 'byte-range', 'start': start, 'endExclusive': start + size},
                'evidence record binding differs: ' + ident)
        used.add(ident)
    with binary.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        for e in evidence:
            loc = e['locator']
            require(e['baselineId'] == BASELINE and e['sourcePath'] == source['sourcePath'] and
                    e['sourceHash'] == BINARY_HASH and e['confidence'] == 'confirmed' and
                    loc['kind'] == 'byte-range' and 0 <= loc['start'] < loc['endExclusive'] <= len(data),
                    'evidence source/extent differs')
            require(sha(data[loc['start']:loc['endExclusive']]) == e['spanSha256'] and
                    'static source bytes' in e['verificationStatus'] and
                    'no target execution' in e['verificationStatus'], 'evidence hash/status differs')
        counts['evidenceSpanChecks'] = 24
        header, segments, symtab, fixcmd, symbols = read_metadata(data)
        require(a['machO']['header'] == header and a['machO']['segments'] == segments and
                a['machO']['symbolTable'] == symtab and header['loadCommandCount'] == 81 and
                len(segments) == 5 and header['functionStartsCommandPresent'] is False,
                'full Mach-O metadata differs')
        counts.update(loadCommandsParsed=81, segmentsParsed=5, exactNativeSymbolChecks=2)
        getter = a['getter']
        for record, vm in [(getter['nativeSymbol'], START), (getter['nextNativeSymbol'], NEXT)]:
            require({k: v for k, v in record.items() if k not in ['nlistEvidenceId', 'nameEvidenceId']} == symbols[vm],
                    'selected nlist/name binding differs')
            ref(record['nlistEvidenceId'], symbols[vm]['nlistFileOffset'], 16)
            ref(record['nameEvidenceId'], symbols[vm]['stringFileOffset'], symbols[vm]['stringBytesIncludingNull'])
        code_map = mapping(segments, START, 81)
        off = code_map['fileOffset']
        body = data[off:off + 81]
        expected = b''.join(bytes.fromhex(code) for _, code in INSTRUCTIONS)
        require(len(expected) == 81 and body == expected and getter['bodyHex'] == body.hex() and
                getter['codeMapping'] == code_map and getter['bodyBytes'] == 81 and
                getter['bodyEndUnslidVmExclusive'] == BODY_END and getter['instructionCount'] == 19,
                'complete independently decoded getter body/range differs')
        starts = {START + delta for delta, _ in INSTRUCTIONS}
        edges, branches, cursor = {}, [], START
        for delta, code in INSTRUCTIONS:
            at, instruction = START + delta, bytes.fromhex(code)
            require(at == cursor, 'independent instruction boundaries not contiguous')
            after = at + len(instruction)
            cursor = after
            if instruction[0] in (0x74, 0xeb):
                target = after + struct.unpack('<b', instruction[1:2])[0]
                require(target in starts, 'branch outside complete function/instruction boundary')
                kind = 'conditional-equal' if instruction[0] == 0x74 else 'unconditional-short-jump'
                entry = {'instructionUnslidVm': at, 'kind': kind, 'targetUnslidVm': target}
                if instruction[0] == 0x74:
                    entry['condition'] = 'RDI == 0' if delta == 0x0c else 'RSI == 0'
                branches.append(entry)
                edges[at] = [target, after] if instruction[0] == 0x74 else [target]
            elif instruction == b'\xc3':
                edges[at] = []
            else:
                require(after in starts, 'fallthrough outside getter body')
                edges[at] = [after]
        seen, pending = set(), [START]
        while pending:
            at = pending.pop()
            if at not in seen:
                seen.add(at)
                pending.extend(edges[at])
        require(cursor == BODY_END and seen == starts and getter['controlFlow'] == branches and
                getter['returnUnslidVm'] == START + 0x32, 'complete getter CFG differs')
        pad_map = mapping(segments, BODY_END, 15)
        padding = data[pad_map['fileOffset']:pad_map['fileOffset'] + 15]
        require(padding == PADDING and getter['paddingHex'] == padding.hex() and
                getter['followingPaddingBytes'] == 15 and
                getter['executionVerified'] is False and getter['callerClosureVerified'] is False and
                'no function-starts table' in getter['rangeBasis'], 'getter padding/range scope differs')
        ref(getter['bodyEvidenceId'], off, 81)
        ref(getter['paddingEvidenceId'], pad_map['fileOffset'], 15)
        disp = struct.unpack_from('<i', body, 0x16)[0]
        structure_vm = START + 0x1a + disp
        require(structure_vm == 0x111d3720 and getter['leaInstructionUnslidVm'] == START + 0x13 and
                getter['leaInstructionFileOffset'] == off + 0x13 and
                getter['leaInstructionHex'] == body[0x13:0x1a].hex() and
                getter['ripDisplacementSigned'] == disp and getter['ripNextUnslidVm'] == START + 0x1a and
                getter['directStructureUnslidVm'] == structure_vm and
                getter['outputStoreInstructionUnslidVm'] == START + 0x1a and
                getter['outputStoreInstructionHex'] == body[0x1a:0x1d].hex() == '488906',
                'direct LEA/output store binding differs')
        ref(getter['leaEvidenceId'], off + 0x13, 7)
        ref(getter['outputStoreEvidenceId'], off + 0x1a, 3)
        counts.update(getterBodyBytes=81, getterInstructionChecks=19, internalBranchChecks=3,
                      paddingBytesChecked=15, directLeaAndOutputStoreChecks=2)
        structure_map = mapping(segments, structure_vm, 24)
        structure_off = structure_map['fileOffset']
        raw_structure = data[structure_off:structure_off + 24]
        major, minor, patch, alignment, encoded = struct.unpack('<IIIIQ', raw_structure)
        require((major, minor, patch, alignment) == (24, 19, 0, 0), 'direct structure fields differ')
        v = a['versionStructure']
        require(v['mapping'] == structure_map and v['structureBytes'] == 24 and
                v['rawHex'] == raw_structure.hex() and v['major'] == major and v['minor'] == minor and
                v['patch'] == patch and v['encodedVersion'] == f'{major}.{minor}.{patch}',
                'version structure record differs')
        layout = [{'field': name, 'offset': 4 * i, 'bytes': 4, 'type': 'uint32_t', 'value': value}
                  for i, (name, value) in enumerate(zip(['major', 'minor', 'patch'], [major, minor, patch]))]
        layout += [{'field': 'alignmentPadding', 'offset': 12, 'bytes': 4, 'value': 0},
                   {'field': 'release', 'offset': 16, 'bytes': 8, 'type': 'const char*',
                    'encoding': 'Mach-O DYLD_CHAINED_PTR_64 rebase'}]
        require(v['layout'] == layout and 'not an executed API result' in v['structureLayoutBasis'],
                'structure interpretation scope differs')
        ref(v['structureEvidenceId'], structure_off, 24)
        # All fixup decoding starts from actual load commands, never an inferred mask alone.
        fix = a['releasePointerFixup']
        require(fix['command'] == fixcmd, 'chained-fixups command differs')
        base, limit = fixcmd['dataFileOffset'], fixcmd['dataFileOffset'] + fixcmd['dataBytes']
        values = struct.unpack_from('<7I', data, base)
        fh = dict(zip(['fixupsVersion', 'startsOffset', 'importsOffset', 'symbolsOffset',
                       'importsCount', 'importsFormat', 'symbolsFormat'], values))
        require(fix['header'] == fh and values[0] == 0, 'chained-fixups header differs')
        image = base + values[1]
        require(base <= image and image + 4 <= limit, 'fixup starts image outside payload')
        segment_count = struct.unpack_from('<I', data, image)[0]
        require(segment_count == len(segments) == 5 and image + 4 + 4 * segment_count <= limit,
                'fixup segment count/table extent differs')
        info_offsets = list(struct.unpack_from('<' + str(segment_count) + 'I', data, image + 4))
        segment_index = next(i for i, s in enumerate(segments) if s['name'] == '__DATA_CONST')
        info = image + info_offsets[segment_index]
        require(base <= info and info + 22 <= limit, 'selected segment info outside payload')
        info_size, page_size, fmt, segment_vm, max_pointer, page_count = struct.unpack_from('<IHHQIH', data, info)
        require(info_size >= 22 + 2 * page_count and info + info_size <= limit and
                page_size == 4096 and fmt == 2 and segment_vm == segments[segment_index]['vmAddress'],
                'selected chain header/page format differs')
        pointer_vm = structure_vm + 16
        page_index = (pointer_vm - segment_vm) // page_size
        require(0 <= page_index < page_count, 'release field page outside table')
        page_entry = info + 22 + page_index * 2
        page_start = struct.unpack_from('<H', data, page_entry)[0]
        require(page_start < 0x8000, 'selected page not a single direct chain start')
        page_base = segment_vm + page_index * page_size
        cursor, chain = page_base + page_start, []
        while True:
            require(page_base <= cursor <= pointer_vm and cursor + 8 <= page_base + page_size and
                    len(chain) < 1024, 'selected chain outside bounded page/target')
            at = mapping(segments, cursor, 8)['fileOffset']
            raw = struct.unpack_from('<Q', data, at)[0]
            step = (raw >> 51) & 0xfff
            chain.append({'unslidVmAddress': cursor, 'fileOffset': at, 'rawUint64': raw,
                'rawHex': data[at:at + 8].hex(), 'nextStrideUnits': step, 'bind': raw >> 63})
            if cursor == pointer_vm:
                break
            require(step > 0, 'selected chain terminated before release field')
            cursor += 4 * step
        require(len(chain) == 229 and chain == fix['chainWalk'] and fix['chainWalkCount'] == 229 and
                chain[-1]['rawUint64'] == encoded, '229-entry chain/membership differs')
        low, high, reserved, bind, step = encoded & ((1 << 36) - 1), (encoded >> 36) & 0xff, \
            (encoded >> 44) & 0x7f, encoded >> 63, (encoded >> 51) & 0xfff
        release_vm = low | high << 56
        require(high == reserved == bind == 0 and release_vm == 0xf69f978 and step == 2,
                'format-2 release pointer decoding differs')
        expected_fix_fields = {'startsInImageFileOffset': image, 'segmentCount': segment_count,
            'segmentInfoOffsets': info_offsets, 'selectedSegmentIndex': segment_index,
            'selectedSegmentInfoFileOffset': info, 'selectedSegmentInfoBytes': info_size,
            'pageSize': page_size, 'pointerFormat': fmt, 'pointerFormatName': 'DYLD_CHAINED_PTR_64',
            'segmentVmOffset': segment_vm, 'maxValidPointer': max_pointer, 'pageCount': page_count,
            'bytesAfterDeclaredPageStartArray': info_size - (22 + 2 * page_count),
            'selectedPageIndex': page_index, 'selectedPageEntryFileOffset': page_entry,
            'selectedPageStart': page_start, 'selectedPageUnslidVm': page_base,
            'releasePointerUnslidVm': pointer_vm, 'releasePointerFileOffset': structure_off + 16,
            'encodedPointerUint64': encoded, 'encodedPointerHex': raw_structure[16:24].hex(),
            'targetLow36': low, 'high8': high, 'reserved': reserved, 'bind': bind,
            'nextStrideUnits': step, 'strideBytes': 4, 'decodedUnslidVmAddress': release_vm}
        require(all(fix[k] == value for k, value in expected_fix_fields.items()) and
                fix['bytesAfterDeclaredPageStartArray'] == 6 and
                'not interpreted' in fix['bytesAfterDeclaredPageStartArrayMeaning'] and
                'not all dyld fixups' in fix['scope'], 'fixup metadata/decode scope differs')
        chain_start = chain[0]['fileOffset']
        chain_end = chain[-1]['fileOffset'] + 8
        fix_spans = [(base, 28), (image, 4 + 4 * segment_count), (info, 22),
                     (page_entry, 2), (chain_start, chain_end - chain_start)]
        require(len(fix['mappingEvidenceIds']) == 5, 'fixup evidence denominator differs')
        for ident, (at, size) in zip(fix['mappingEvidenceIds'], fix_spans):
            ref(ident, at, size)
        ref(fix['pointerEvidenceId'], structure_off + 16, 8)
        release_map = mapping(segments, release_vm, 5)
        release_off = release_map['fileOffset']
        release = data[release_off:release_off + 5]
        require(release == b'node\0' and v['releaseMapping'] == release_map and
                v['releaseHex'] == release.hex() and v['releaseBytesIncludingNull'] == 5 and
                v['release'] == release[:-1].decode('ascii'), 'release C string differs')
        ref(v['releaseEvidenceId'], release_off, 5)
        text = next(s for s in segments if s['name'] == '__TEXT')
        const = segments[segment_index]
        macho_spans = [(0, 32), (32, header['loadCommandBytes']), (symtab['commandFileOffset'], 24),
            (fixcmd['commandFileOffset'], 16), (text['commandFileOffset'], text['commandBytes']),
            (const['commandFileOffset'], const['commandBytes']), (code_map['sectionHeaderFileOffset'], 80),
            (structure_map['sectionHeaderFileOffset'], 80)]
        require(len(a['machO']['mappingEvidenceIds']) == 8, 'Mach-O evidence denominator differs')
        for ident, (at, size) in zip(a['machO']['mappingEvidenceIds'], macho_spans):
            ref(ident, at, size)
        require(used == set(by_id), 'orphan/unbound evidence')
        counts.update(evidenceRecordBindingChecks=24, versionStructureBytes=24,
            selectedChainPointerChecks=229, selectedChainPointerBytes=229 * 8,
            selectedChainCoveredRegionBytes=chain_end - chain_start,
            releaseCStringBytes=5, chainedPointerDecodeChecks=1)
        require(len(a['toolRuns']) == 2, 'saved tool run denominator differs')
        tool_pins, instruction_rows = {}, []
        for run in a['toolRuns']:
            label = run['label']
            require(label in ['llvm-version', 'napi-get-node-version'], 'unexpected saved tool label')
            command = json.loads((work / (label + '.command.json')).read_text())
            require(command == run and run['exitCode'] == 0 and run['targetExecuted'] is False,
                    'saved tool command/exit/scope differs')
            tool = Path(run['toolExecutable'])
            tool_pin = track(tool)
            require(tool_pin['sha256'] == run['toolSha256'] and
                    str(tool.resolve()) == run['toolResolvedPath'], 'tool executable pin differs')
            tool_pins[str(tool)] = tool_pin
            for kind in ['stdout', 'stderr']:
                declared(run[kind])
                require(run[kind]['path'] == str((work / (label + '.' + kind + '.txt')).relative_to(root)),
                        'saved output path differs')
            require(run['stderr']['bytes'] == 0, 'nonempty saved tool stderr')
            stdout = (root / run['stdout']['path']).read_text()
            if label == 'llvm-version':
                require(run['argv'] == [str(tool), '--version'] and run['scope'] == {'targetInput': False} and
                        stdout.strip() == a['toolVersion'] and 'Apple LLVM version 21.0.0' in stdout,
                        'saved tool version command/output differs')
            else:
                require(run['argv'] == [str(tool), '--disassemble', '--start-address=0x4b42f60',
                    '--stop-address=0x4b42fc0', str(binary)] and run['scope'] ==
                    {'startUnslidVm': START, 'endUnslidVmExclusive': NEXT, 'bodyBytes': 81, 'paddingBytes': 15},
                    'finite saved disassembly argv/range differs')
                require(re.search(r'^0*4b42f60 <_napi_get_node_version>:', stdout, re.M),
                        'saved getter symbol label differs')
                for line in stdout.splitlines():
                    match = re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)(.*)$', line)
                    if match:
                        address, raw = int(match.group(1), 16), bytes.fromhex(match.group(2))
                        require(START <= address and address + len(raw) <= NEXT,
                                'saved disassembly outside bounded range')
                        at = mapping(segments, address, len(raw))['fileOffset']
                        require(data[at:at + len(raw)] == raw, 'saved LLVM instruction bytes differ')
                        instruction_rows.append((address, raw))
        expected_rows = [(START + delta, bytes.fromhex(code)) for delta, code in INSTRUCTIONS] + [(BODY_END, PADDING)]
        require(instruction_rows == expected_rows and len(tool_pins) == 1,
                'saved LLVM complete instruction/padding boundary coverage differs')
        snapshots['toolExecutables'] = list(tool_pins.values())
        counts.update(savedToolArtifactHashChecks=6, savedToolCommandChecks=2,
                      savedDisassemblyInstructionByteChecks=20, toolExecutableHashChecks=1)
    schemas = a['schemaReferences']
    require(len(schemas) == 3 and schemas[0]['url'] == 'https://nodejs.org/api/n-api.html#napi_get_node_version' and
            schemas[0]['reviewedBy'] == schemas[1]['reviewedBy'] == 'root' and
            schemas[0]['externalPageReportedVersion'] == 'v26.11.1' and
            schemas[1]['url'] == 'https://raw.githubusercontent.com/nodejs/node/v24.19.0/src/node_api_types.h' and
            schemas[0]['externalSourceArchived'] is False and schemas[1]['externalSourceArchived'] is False and
            all(s['layout'] == 'uint32_t major; uint32_t minor; uint32_t patch; const char* release;'
                for s in schemas[:2]), 'parent-reviewed Node schema context differs')
    apple = schemas[2]
    schema_pin = declared(apple['snapshot'])
    require(schema_pin['sha256'] == APPLE_HEADER_HASH and schema_pin['bytes'] == 12659 and
            apple['originalSha256'] == APPLE_HEADER_HASH and apple['originalBytes'] == 12659,
            'Apple schema snapshot pin differs')
    original = Path(apple['originalPath'])
    original_pin = track(original)
    require(original_pin['bytes'] == 12659 and original_pin['sha256'] == APPLE_HEADER_HASH and
            str(original.resolve()) == apple['resolvedOriginalPath'], 'original Apple primary header differs')
    snapshots['appleOriginalHeader'] = original_pin
    schema = (root / schema_pin['path']).read_bytes()
    require(len(apple['byteRanges']) == 3, 'Apple schema span denominator differs')
    tokens = [(b'struct dyld_chained_fixups_header', b'// these values are set'),
        (b'// values for dyld_chained_starts_in_segment.pointer_format', b'// DYLD_CHAINED_PTR_ARM64E'),
        (b'struct dyld_chained_ptr_64_rebase', b'// DYLD_CHAINED_PTR_ARM64E_USERLAND24')]
    for span, (start_token, end_token) in zip(apple['byteRanges'], tokens):
        start = schema.index(start_token)
        end = schema.index(end_token, start)
        require(span == {'start': start, 'endExclusive': end, 'spanSha256': sha(schema[start:end])},
                'Apple schema span differs')
    rebase = re.search(rb'struct dyld_chained_ptr_64_rebase\s*\{([^}]+)\}', schema)
    require(rebase is not None and re.findall(rb'(target|high8|reserved|next|bind)\s*:\s*(\d+)',
            rebase.group(1)) == [(b'target', b'36'), (b'high8', b'8'), (b'reserved', b'7'),
                                (b'next', b'12'), (b'bind', b'1')] and
            b'4-byte stride' in rebase.group(1) and
            re.search(rb'DYLD_CHAINED_PTR_64\s*=\s*2,\s*// target is vmaddr', schema) and
            apple['pointerFormat'] == 2 and apple['name'] == 'DYLD_CHAINED_PTR_64',
            'Apple format-2 bitfield/stride/VM meaning differs')
    counts.update(appleSchemaByteSpanChecks=3, applePrimaryHeaderIdentityChecks=1)
    expected_summary = {'newEvidenceCount': 24, 'selectedSymbols': 2, 'getterBodyBytes': 81,
        'getterInstructionCount': 19, 'internalControlFlowEdges': 3, 'versionStructureBytes': 24,
        'releaseCStringBytes': 5, 'selectedChainPointerCount': 229, 'encodedNodeVersion': '24.19.0', 'release': 'node'}
    require(a['summary'] == expected_summary and
            a['conclusions']['selectedFrameworkNativeStaticVersion'] == '24.19.0' and
            a['conclusions']['selectedFrameworkNativeStaticRelease'] == 'node' and
            a['conclusions']['directGetterToStructureBinding'] == 'confirmed' and
            a['conclusions']['releaseFixupChainMembershipAndTarget'] == 'confirmed', 'summary/static conclusions differ')
    unknown_keys = ['observedExecutedNodeVersion', 'actualElectronCompatibilityVersion',
                    'nodeModuleVersion', 'nativeModulesAbi', 'completeNativeCallerClosure', 'startupExecutionAndEnforcement']
    require(all(a['conclusions'][k] == 'unknown' for k in unknown_keys), 'unverified scope improperly resolved')
    require(all(a['executionScope'][k] == 0 for k in ['targetPrograms', 'probes', 'appStarts',
            'fuseModifications', 'credentialReads', 'networkRequests', 'newModelTasks']), 'execution scope differs')
    require(any('No traditional NODE_MODULE_VERSION' in x for x in a['limitations']) and
            any('contradictions remain unexplained' in x for x in a['limitations']) and
            any('all other fixups' in x for x in a['limitations']), 'material limitation missing')
    summary = (work / 'summary.md').read_text()
    require('24.19.0' in summary and '229' in summary and '81 字节' in summary and
            'NODE_MODULE_VERSION' in summary and '未执行查询' in summary and '仍未知' in summary,
            'human summary scope differs')
    # A pure read-only recheck of every original input/product identity, including
    # both old manifests, tool and schema files, binary, and this verifier itself.
    for path, pin in before.items():
        require(describe(Path(path), root) == pin, 'material changed during verification: ' + path)
    counts['unchangedUniqueFileHashChecks'] = len(before)
    snapshots['allBeforeAfterIdentities'] = list(before.values())
    return {'baselineId': BASELINE, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
        'status': 'passed; selected-static-version-confirmed; execution-and-traditional-ABI-unverified',
        'method': 'Independent complete source hashes, Mach-O tables, separately enumerated getter instructions/CFG, actual fixup metadata/page chain, local primary schema and saved LLVM-byte checks; no producer or tool execution.',
        'runner': runner, 'runnerUnchangedDuringRun': True, 'counts': counts, 'snapshots': snapshots, 'errors': [],
        'staticObservation': {'encodedNodeVersion': '24.19.0', 'release': 'node', 'getterBodyBytes': 81},
        'retainedUnknowns': {k: a['conclusions'][k] for k in unknown_keys},
        'executionScope': {'producerRuns': 0, 'disassemblerRuns': 0, 'targetProgramsLaunched': 0,
            'probes': 0, 'networkRequests': 0, 'modelTasksSubmitted': 0, 'pureVerifyWrites': 0,
            'oldFrozenMaterialModified': False},
        'limitations': ['Static getter data is not an executed runtime query or stock runtime equivalence proof.',
            'External Node schema meaning was reviewed by root; no network request occurred here.',
            'Traditional NODE_MODULE_VERSION/native ABI and earlier archive contradictions remain unresolved.']}


def main():
    output = WORK / 'validation.json'
    require(not output.exists(), 'refuse to overwrite validation.json')
    try:
        result = verify(ROOT, WORK)
    except Exception as exc:
        result = {'baselineId': BASELINE, 'status': 'failed',
            'runner': describe(Path(__file__).resolve(), ROOT), 'counts': {},
            'errors': [{'type': type(exc).__name__, 'message': str(exc)}]}
    result['runnerArgv'] = sys.argv
    result['outputPolicy'] = 'CLI writes this validation once; verify(root,work) writes nothing.'
    with output.open('x') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'counts': result['counts'], 'errors': result['errors'],
                      'validation': describe(output, ROOT), 'runner': result['runner']}, ensure_ascii=False))
    return 0 if not result['errors'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
